"""V0.9 movable mechanical trial kit; source units millimetres.

Original geometry, CERN-OHL-P-2.0. The V0.8 lower framework is retained;
new front keys share the body surface and upper ventilation is triangular.
"""
from pathlib import Path
import json,time,copy,math,argparse,shutil
import cadquery as cq
import trimesh
from shapely.geometry import box,Polygon
from shapely import affinity
from build_mouse import rounded_box,beam
from build_v03 import bounds
from build_v05 import make_surfaces,clip_above
from export_v09 import save_model,export_step
from vent_layout_v09 import cells,cutter,manifest
from mechanisms_v09 import union,pose,cartridge,side_face,side_opening,main_face,wheel_parts,cyl
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'exports/v09';RP=ROOT/'reports/v09';V=cq.Vector

def qmodule(p,m):
    q=copy.deepcopy(p['mechanism'])
    if m.get('side'):q['stem_xy']=[3.2,7.6];q['shoulder_extra_x']=0;q['boss_centres_xy']=p['side_mount_centres_xy']
    return q

def build_shell(p):
    print('Loft, inset lower framework, open-front full-width main keys',flush=True)
    outer,inner=make_surfaces(p);print('Parent loft complete',flush=True);raw=outer.cut(inner);print('Hollow shell complete',flush=True)
    skin=raw.copy();outline,domain,items=cells(p,outer)
    report=manifest(p,outline,domain,items);report['version']='0.9'
    for h in items:
        skin=skin.cut(cutter(h),tol=1e-5);print('Triangle',h['id'],flush=True)
    # Triangles are cut directly; no old Voronoi underside rails refill them.
    (RP/'vent_layout.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    for n in ('left_key','right_key'):
        k=p[n];skin=skin.cut(rounded_box(k['width']+.8,k['length']+.8,45,p['main_key_surface']['corner_radius']+.4,(k['x'],-k['y'],27)))
        nose=cq.Workplane('XY').box(k['width']+.8,30,50).val().translate((k['x'],15-k['y']+k['length']/2-1,p['main_key_surface']['front_frame_cut_z']+25))
        skin=skin.cut(nose)
    w=p['wheel'];skin=skin.cut(rounded_box(w['opening_width'],w['opening_length'],45,2,(0,-w['y'],27)))
    # The moving wheel carrier must actually enter a one-piece shell. Its
    # connected assembly aperture replaces the former closed central spine.
    cw,cl=w['carrier_install_opening_xy'];skin=skin.cut(rounded_box(cw,cl,45,2,(0,-w['carrier_install_opening_d'],27)))
    usb=p['usb_port'];port=rounded_box(usb['width'],usb['height'],16,usb['radius'],(0,0,0)).rotate((0,0,0),(1,0,0),90).translate((0,-2,usb['z']))
    skin=skin.cut(port)
    assert skin.isValid() and skin.BoundingBox().ylen>p['length']-.5,'Upper skin was lost in a Boolean operation'
    old=cq.importers.importStep(str(ROOT/p['frozen_bottom']['source_step'])).val()
    lower=old.cut(clip_above(5.6))
    p8=json.loads((ROOT/'cad/parameters_v08.json').read_text(encoding='utf8'))
    old_outer,old_inner=make_surfaces(p8)
    core=lower.cut(old_outer.cut(old_inner))
    export_step(core,str(ROOT/'.tools/v09_core_only.step'))
    shell=skin.fuse(core,tol=1e-5).clean()
    assert shell.isValid() and shell.BoundingBox().ylen>p['length']-.5
    (RP/'base_trim.json').write_text(json.dumps(dict(source=p['frozen_bottom']['source_step'],new_framework_trim_mm=0,preservation='Retain the exact V0.8 internal lower core, five feet, sensor and switch structures. Rebuild the lower side skin using the new thinner parent loft; no overlapping old side wall graft.'),indent=2),encoding='utf8')
    export_step(shell,str(ROOT/'.tools/v09_pre_frames.step'))
    export_step(outer,str(ROOT/'.tools/v09_outer.step'))
    export_step(raw,str(ROOT/'.tools/v09_raw_skin.step'))
    return add_frames(p,shell,outer),outer,raw,report

def add_frames(p,shell,outer):
    raw=cq.importers.importStep(str(ROOT/'.tools/v09_raw_skin.step')).val()
    nose_zone=cq.Workplane('XY').box(100,34,60).val().translate((0,-15,25))
    shell=shell.fuse(raw.cut(clip_above(p['main_key_surface']['front_frame_cut_z'])).intersect(nose_zone))
    # The former isolated bridge above USB is opened into the wheel aperture.
    # This is an intentional open-top front service throat, not a loose island.
    shell=shell.cut(cq.Workplane('XY').box(13.0,20,40).val().translate((0,2.5,27.6)))
    usb=p['usb_port'];port=rounded_box(usb['width'],usb['height'],16,usb['radius'],(0,0,0)).rotate((0,0,0),(1,0,0),90).translate((0,-2,usb['z']))
    shell=shell.cut(port)
    for name,m in p['modules'].items():
        unit=cartridge(qmodule(p,m));fr=pose(unit['frame'],m)
        if name=='middle':fr=fr.cut(cq.Workplane('XY').box(12.4,100,80).val().translate((0,20.6,30)))
        if m.get('side'):
            window=side_opening(p,m)
            shell=shell.cut(window)
            # Frame connects to the wall through a local ring, not a solid plug.
            ring=rounded_box(11,17,8,1,(0,0,2)).cut(rounded_box(4.1,8.7,16,.8,(0,0,1)))
            ring=ring.cut(rounded_box(4.1,11.6,14,.6,(0,0,7.01)))
            ring=pose(ring,m)
            fr=fr.fuse(ring).intersect(outer.translate((.65,0,0)))
        elif name!='middle':
            x,y,z=m['origin'];sign=1 if x>0 else -1
            fr=fr.fuse(beam((x+sign*6.5,y,z-p['main_support_drop_mm']),(sign*29,y,z-p['main_support_drop_mm']),2.8)).intersect(outer)
        else:
            for sign in (-1,1):fr=fr.fuse(beam((sign*6.5,-33,15.0),(sign*27,-28,15.0),2.8))
            fr=fr.intersect(outer)
        # The V0.9 parent-surface key undersides clear these lower guides; verify the
        # actual motion after export rather than cutting redundant spline sweeps.
        assert fr.isValid(),name
        shell=shell.fuse(fr)
        print('Module fixed frame',name,len(shell.Solids()),flush=True)
    # Later guide pads must not refill an adjacent cap's aperture. The stepped
    # relief clears the large inner shoulder while preserving the guide at Z=0.
    for m in p['modules'].values():
        if not m.get('side'):continue
        shell=shell.cut(side_opening(p,m))
    shell=shell.clean()
    if len(shell.Solids())!=1:
        print('Shell components',[(s.Volume(),bounds(s)) for s in shell.Solids()],flush=True)
    assert shell.isValid() and len(shell.Solids())==1,('shell',len(shell.Solids()))
    return shell

def side_internal_reliefs(p,shell):
    # Keep the guide's -3 mm stop face and boss mounting faces. Relieve only
    # material that would occupy the removable side retainer/tray space.
    # Preserve the actual R2.3 bosses, not the larger R2.65 tray clearance:
    # preserving the clearance disc leaves an unattached corner of the middle beam.
    for name,m in p['modules'].items():
        if not m.get('side'):continue
        q=qmodule(p,m);w,l=q['stem_xy']
        ret=rounded_box(w+2.8,l+4.,2.4,.8,(0,0,-4.2))
        floor=rounded_box(13.8,12.0,1.8,1,(-1.7,0,-10.5))
        rim=rounded_box(10.2,10.2,3.5,.8,(0,0,-7.85))
        for x,y in q['boss_centres_xy']:
            rim=rim.cut(cq.Solid.makeCylinder(2.3,7,V(x,y,-11.3)))
        shell=shell.cut(pose(ret.fuse(floor).fuse(rim),m))
        print('Internal side relief',name,shell.isValid(),len(shell.Solids()),flush=True)
    shell=shell.clean()
    if not shell.isValid() or len(shell.Solids())!=1:
        print('Side-relief components',[(s.Volume(tol=1e-3),bounds(s)) for s in shell.Solids()],flush=True)
    assert shell.isValid() and len(shell.Solids())==1
    return shell

def main_install_reliefs(p,shell,outer):
    # Short key faces no longer cover the full shoulder. Give the shoulder a
    # vertical installation slot behind the cap while retaining the local guide stop.
    for name in ('left','right'):
        m=p['modules'][name];q=qmodule(p,m);w,l=q['stem_xy']
        window=rounded_box(w+q.get('shoulder_extra_x',3.2)+.6,l+3.8,40,.8,(0,0,20.05))
        shell=shell.cut(pose(window,m))
        # Allow the pressed cap's underside to clear the outboard support beam.
        # The face-only cutter cannot alter the plunger's guide or stop.
        face=main_face(p,p['left_key' if name=='left' else 'right_key'],outer)
        shell=shell.cut(face.translate((0,0,-p['main_key_surface']['motion_relief_depth'])),tol=1e-5)
    shell=shell.clean()
    assert shell.isValid() and len(shell.Solids())==1
    return shell

def preserve_lower_interfaces(p,shell,raw):
    # All window cuts are above the preserved core or clear of its interfaces.
    # Do not re-graft the old curved side wall onto the new parent loft.
    # Re-add the complete original filleted foot primitives. Subtracting the
    # old skin to extract the framework had also removed a tiny part of the
    # two rear platforms at their former skin intersection.
    for x,y in [(-21,-8),(21,-8),(-21.5,-61.5),(21.5,-61.5),(0,-81.5)]:
        foot=cq.Workplane('XY').center(x,y).circle(p['foot_diameter']/2).extrude(p['foot_thickness']).edges('>Z').fillet(.35).val()
        shell=shell.fuse(foot,tol=1e-5)
    shell=shell.clean()
    assert shell.isValid() and len(shell.Solids())==1
    return shell


def build_parts(p,shell,outer,raw):
    parts={'BODY':shell};meta={'BODY':dict(kind='fixed',color=[.44,.60,.65],print_quantity=1)};hardware={};moved={}
    for name,m in p['modules'].items():
        unit=cartridge(qmodule(p,m))
        pl=unit['plunger']
        if m.get('side'):
            pl=pl.cut(clip_above(3.7))
            cap=pose(pl,m).fuse(side_face(p,m,outer))
        elif name!='middle':
            k=p['left_key' if name=='left' else 'right_key']
            touch=main_face(p,k,outer)
            cap=pose(pl,m).intersect(outer).fuse(touch)
        else:continue
        assert cap.isValid() and len(cap.Solids())==1,name
        parts[name+'_KEY']=cap
        meta[name+'_KEY']=dict(kind='moving',module=name,color=[.55,.66,.69] if m.get('side') else [.72,.81,.81],print_quantity=1)
    parts.update({k.upper():v for k,v in wheel_parts(p).items()})
    for k in ('WHEEL','AXLE','AXLE_WASHER','WHEEL_CARRIER','DETENT_LEAF'):
        meta[k]=dict(kind='wheel' if k=='WHEEL' else 'moving',module='middle',color=[.25,.31,.35] if k in ('WHEEL','AXLE','AXLE_WASHER') else [.77,.54,.27],print_quantity=1)
    for name,m in p['modules'].items():
        unit=cartridge(qmodule(p,m))
        for part in ('retainer','tray'):
            key=name+'_'+part.upper();parts[key]=pose(unit[part],m)
            meta[key]=dict(kind='moving' if part=='retainer' else 'fixed',module=name,color=[.65,.69,.73],print_quantity=1)
        hardware[name+'_SWITCH_EXAMPLE']=pose(unit['switch'],m)
    return parts,meta,hardware

def print_pose(s,name,p):
    if name=='BODY':return s
    if name.startswith('thumb_'):
        m=p['modules']['thumb_front' if 'front' in name else 'thumb_rear']
        s=s.translate(tuple(-x for x in m['origin'])).rotate((0,0,0),(0,1,0),90)
    elif name in ('WHEEL','AXLE','AXLE_WASHER'):s=s.rotate((0,0,0),(0,1,0),-90 if name=='AXLE' else 90)
    elif name=='DETENT_LEAF':s=s.rotate((0,0,0),(1,0,0),-90)
    if name.endswith('_RETAINER'):s=s.rotate((0,0,0),(1,0,0),180)
    bb=bounds(s);return s.translate((-(bb[0]+bb[3])/2,-(bb[1]+bb[4])/2,-bb[2]))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--reuse-shell',action='store_true');ap.add_argument('--reuse-core',action='store_true');args=ap.parse_args()
    for d in (OUT,OUT/'placed',OUT/'print',RP):d.mkdir(parents=True,exist_ok=True)
    p=json.loads((ROOT/'cad/parameters_v09.json').read_text(encoding='utf8'));start=time.time()
    if args.reuse_shell:
        shell=cq.Shape.importBrep(str(ROOT/'.tools/v09_final_BODY.brep')) if (ROOT/'.tools/v09_final_BODY.brep').exists() else cq.importers.importStep(str(OUT/'placed/BODY.step')).val();outer=cq.importers.importStep(str(ROOT/'.tools/v09_outer.step')).val();raw=cq.importers.importStep(str(ROOT/'.tools/v09_raw_skin.step')).val();layout=json.loads((RP/'vent_layout.json').read_text())
    elif args.reuse_core:
        outer=cq.importers.importStep(str(ROOT/'.tools/v09_outer.step')).val();raw=cq.importers.importStep(str(ROOT/'.tools/v09_raw_skin.step')).val();layout=json.loads((RP/'vent_layout.json').read_text())
        shell=add_frames(p,cq.importers.importStep(str(ROOT/'.tools/v09_pre_frames.step')).val(),outer);export_step(shell,str(OUT/'placed/BODY.step'))
    else:
        shell,outer,raw,layout=build_shell(p);export_step(shell,str(OUT/'placed/BODY.step'))
    for kn in ('left_key','right_key'):
        k=p[kn]
        nose=cq.Workplane('XY').box(k['width']+.8,30,50).val().translate((k['x'],15-k['y']+k['length']/2-1,p['main_key_surface']['front_frame_cut_z']+25))
        shell=shell.cut(nose)
    shell=side_internal_reliefs(p,shell)
    shell=main_install_reliefs(p,shell,outer)
    shell=preserve_lower_interfaces(p,shell,raw)
    parts,meta,hardware=build_parts(p,shell,outer,raw)
    assembly=cq.Assembly(name='QUIETMIRROR_V09_MECHANICAL_TEST');records=[];scene=trimesh.Scene()
    for name,shape in parts.items():
        print('Export',name,flush=True)
        record=save_model(shape,name,OUT/'placed');flat=print_pose(shape,name,p)
        if name=='BODY':
            for suffix in ('.step','.stl'):shutil.copyfile(OUT/'placed'/(name+suffix),OUT/'print'/(name+suffix))
            pm=record.copy()
        else:pm=save_model(flat,name,OUT/'print')
        record.update(meta[name]);record['print_bounds']=pm['bounds'];record['file']=f'exports/v09/placed/{name}.stl';record['print_file']=f'exports/v09/print/{name}.stl';records.append(record)
        assembly.add(shape,name=name,color=cq.Color(*meta[name]['color']))
        mesh=trimesh.load_mesh(OUT/'placed'/f'{name}.stl');mesh.visual.face_colors=[int(x*255) for x in meta[name]['color']]+[255];scene.add_geometry(mesh,node_name=name)
    for name,shape in hardware.items():
        export_step(shape,str(OUT/'placed'/f'{name}.step'));shape.exportStl(str(OUT/'placed'/f'{name}.stl'),tolerance=.03,angularTolerance=.15,relative=False)
        assembly.add(shape,name=name,color=cq.Color(.76,.31,.21))
        mesh=trimesh.load_mesh(OUT/'placed'/f'{name}.stl');mesh.visual.face_colors=[194,79,54,255];scene.add_geometry(mesh,node_name=name)
    assembly.save(str(OUT/'quietmirror_V0.9_MECHANICAL_ASSEMBLY.step'),write_pcurves=False)
    scene.units='mm';(OUT/'quietmirror_V0.9_MECHANICAL_VIEW_ONLY.3mf').write_bytes(trimesh.exchange.threemf.export_3MF(scene))
    report=dict(version='0.9',units='mm',parts=records,printable_parts=len(records),switch_examples=5,vent_count=layout['total_holes'],build_seconds=time.time()-start,parameters=p)
    (RP/'cad_metrics.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
    print('COMPLETE',len(records),'printable pieces',report['build_seconds'],flush=True)

if __name__=='__main__':main()
