"""V0.7 movable mechanical trial kit; source units millimetres.

Independent original geometry, CERN-OHL-P-2.0. The V0.6 lower body through
Z=5.4 is retained verbatim by a solid intersection, not reconstructed.
"""
from pathlib import Path
import json,time,copy,math,argparse
import cadquery as cq
import trimesh
from shapely.geometry import box,Polygon
from shapely import affinity
from build_mouse import rounded_box,beam
from build_v03 import bounds
from build_v05 import make_surfaces,save_model,clip_above
from vent_layout_v06 import cells,cutter,manifest
from mechanisms_v07 import union,pose,cartridge,side_face,wheel_parts,cyl
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'exports/v07';RP=ROOT/'reports/v07';V=cq.Vector

def qmodule(p,m):
    q=copy.deepcopy(p['mechanism'])
    if m.get('side'):q['stem_xy']=[3.2,7.6];q['shoulder_extra_x']=0
    return q

def front_holes(p,outline):
    free=outline.buffer(-2.4).intersection(box(-50,2.8,50,45.7))
    # Insets are actual aperture clearances; separate datum from the touch face.
    for n in ('left_key','right_key'):
        k=p[n];f=box(k['x']-k['width']/2+.4,k['y']-k['length']/2+.4,k['x']+k['width']/2-.4,k['y']+k['length']/2-.4).buffer(.8,quad_segs=12)
        free=free.difference(f.buffer(2.2))
    free=free.difference(box(-6.4,7.3,6.4,26.7).buffer(2.2))
    cw,cl=p['wheel']['carrier_install_opening_xy'];cd=p['wheel']['carrier_install_opening_d']
    free=free.difference(box(-cw/2,cd-cl/2,cw/2,cd+cl/2).buffer(2.2))
    # Upper bearings and middle plunger need an unperforated centre spine.
    free=free.difference(box(-4.2,25,4.2,39))
    # Keep finger-contact side walls and the side-key guide roots continuous.
    free=free.difference(box(20,29,50,60)).difference(box(-50,29,-20,60))
    holes=[]
    for lo,hi in [(2.8,7.0),(9.2,20),(22.2,36),(38.2,45.7)]:
        region=free.intersection(box(1.1,lo,50,hi))
        for g in ([region] if region.geom_type=='Polygon' else region.geoms):
            if g.is_empty or g.area<8:continue
            g=g.buffer(-.7,quad_segs=10).buffer(.7,quad_segs=10).simplify(.008)
            if g.is_empty or g.geom_type!='Polygon' or g.area<7:continue
            holes += [g,affinity.scale(g,-1,1,origin=(0,0))]
    return holes

def build_shell(p):
    print('Loft and retained lower V0.6 body',flush=True)
    outer,inner=make_surfaces(p);raw=outer.cut(inner)
    skin=raw.copy();outline,domain,items=cells(p,outer)
    report=manifest(p,outline,domain,items);report['version']='0.7'
    for h in items:skin=skin.cut(cutter(h),tol=1e-5)
    rails=json.loads((ROOT/'reports/v06/underside_web_rails.json').read_text())
    for pts in rails['paths']:skin=skin.fuse(union([beam(a,b,2) for a,b in zip(pts,pts[1:])]).intersect(outer))
    front=front_holes(p,outline)
    for i,g in enumerate(front):
        wire=cq.Workplane('XY').polyline([(x,-d) for x,d in list(g.exterior.coords)[:-1]]).close().val()
        tool=cq.Solid.extrudeLinear(wire,[],V(0,0,40)).translate((0,0,12))
        skin=skin.cut(tool,tol=1e-5)
    report['front_holes']=[dict(id=f'F{i+1:02}',xd_mm=list(g.exterior.coords),area_mm2=g.area) for i,g in enumerate(front)]
    report['total_holes']=len(items)+len(front)
    (RP/'vent_layout.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    for n in ('left_key','right_key'):
        k=p[n];skin=skin.cut(rounded_box(k['width']+.8,k['length']+.8,45,3.4,(k['x'],-k['y'],27)))
    w=p['wheel'];skin=skin.cut(rounded_box(w['opening_width'],w['opening_length'],45,2,(0,-w['y'],27)))
    # The moving wheel carrier must actually enter a one-piece shell. Its
    # connected assembly aperture replaces the former closed central spine.
    cw,cl=w['carrier_install_opening_xy'];skin=skin.cut(rounded_box(cw,cl,45,2,(0,-w['carrier_install_opening_d'],27)))
    usb=p['usb_port'];port=rounded_box(usb['width'],usb['height'],16,usb['radius'],(0,0,0)).rotate((0,0,0),(1,0,0),90).translate((0,-2,usb['z']))
    skin=skin.cut(port)
    old=cq.importers.importStep(str(ROOT/'exports/v06/quietmirror_fingertip_V0.6_SHELL.step')).val()
    lower=old.cut(clip_above(5.6))
    skin=skin.intersect(clip_above(5.4))
    shell=union([lower,skin]);frames=[]
    cq.exporters.export(shell,str(ROOT/'.tools/v07_pre_frames.step'))
    cq.exporters.export(outer,str(ROOT/'.tools/v07_outer.step'))
    cq.exporters.export(raw,str(ROOT/'.tools/v07_raw_skin.step'))
    return add_frames(p,shell,outer),outer,raw,report

def add_frames(p,shell,outer):
    for name,m in p['modules'].items():
        unit=cartridge(qmodule(p,m));fr=pose(unit['frame'],m)
        if name=='middle':fr=fr.cut(cq.Workplane('XY').box(12.4,100,80).val().translate((0,20.6,30)))
        if m.get('side'):
            window=pose(rounded_box(6.1,13.4,25,.65,(0,0,11.5)),m)
            window=window.fuse(pose(rounded_box(7.2,11.6,4.4,.8,(0,0,.7)),m))
            shell=shell.cut(window)
            # Frame connects to the wall through a local ring, not a solid plug.
            ring=rounded_box(11,17,8,1,(0,0,2)).cut(rounded_box(4.1,8.7,16,.8,(0,0,1)))
            ring=ring.cut(rounded_box(7.2,12.8,14,1,(0,0,7.01)))
            ring=pose(ring,m)
            fr=fr.fuse(ring).intersect(outer)
        elif name!='middle':
            x,y,z=m['origin'];sign=1 if x>0 else -1
            fr=fr.fuse(beam((x+sign*6.5,y,z-2),(sign*29,y,z-2),2.8)).intersect(outer)
        else:
            for sign in (-1,1):fr=fr.fuse(beam((sign*6.5,-33,16.5),(sign*27,-28,16.5),2.8))
            fr=fr.intersect(outer)
        raw=cq.importers.importStep(str(ROOT/'.tools/v07_raw_skin.step')).val()
        for kn in ('left_key','right_key'):
            k=p[kn]
            sweep=raw.intersect(rounded_box(k['width']+1,k['length']+1,50,3,(k['x'],-k['y'],25)))
            sweep=sweep.fuse(sweep.translate((0,0,-.65)))
            fr=fr.cut(sweep)
        assert fr.isValid(),name
        shell=shell.fuse(fr)
        print('Module fixed frame',name,len(shell.Solids()),flush=True)
    # Later guide pads must not refill an adjacent cap's aperture. The stepped
    # relief clears the large inner shoulder while preserving the guide at Z=0.
    for m in p['modules'].values():
        if not m.get('side'):continue
        window=rounded_box(6.1,13.4,20,.65,(0,0,12.5)).fuse(rounded_box(7.2,11.6,3,.8,(0,0,1.5)))
        shell=shell.cut(pose(window,m))
    shell=shell.clean()
    assert shell.isValid() and len(shell.Solids())==1,('shell',len(shell.Solids()))
    return shell

def build_parts(p,shell,outer,raw):
    parts={'BODY':shell};meta={'BODY':dict(kind='fixed',color=[.44,.60,.65],print_quantity=1)};hardware={};moved={}
    for name,m in p['modules'].items():
        unit=cartridge(qmodule(p,m))
        pl=unit['plunger']
        if m.get('side'):
            pl=pl.cut(clip_above(4.6)).fuse(side_face())
            cap=pose(pl,m)
        elif name!='middle':
            k=p['left_key' if name=='left' else 'right_key']
            touch=raw.intersect(rounded_box(k['width'],k['length'],55,3,(k['x'],-k['y'],27)))
            touch=cq.Workplane(obj=touch).edges().fillet(.4).val()
            cap=pose(pl,m).intersect(outer).fuse(touch)
        else:continue
        assert cap.isValid() and len(cap.Solids())==1,name
        parts[name+'_KEY']=cap
        meta[name+'_KEY']=dict(kind='moving',module=name,color=[.89,.56,.27] if m.get('side') else [.72,.81,.81],print_quantity=1)
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
    p=json.loads((ROOT/'cad/parameters_v07.json').read_text(encoding='utf8'));start=time.time()
    if args.reuse_shell:
        shell=cq.importers.importStep(str(OUT/'placed/BODY.step')).val();outer=cq.importers.importStep(str(ROOT/'.tools/v07_outer.step')).val();raw=cq.importers.importStep(str(ROOT/'.tools/v07_raw_skin.step')).val();layout=json.loads((RP/'vent_layout.json').read_text())
    elif args.reuse_core:
        outer=cq.importers.importStep(str(ROOT/'.tools/v07_outer.step')).val();raw=cq.importers.importStep(str(ROOT/'.tools/v07_raw_skin.step')).val();layout=json.loads((RP/'vent_layout.json').read_text())
        shell=add_frames(p,cq.importers.importStep(str(ROOT/'.tools/v07_pre_frames.step')).val(),outer);cq.exporters.export(shell,str(OUT/'placed/BODY.step'))
    else:
        shell,outer,raw,layout=build_shell(p);cq.exporters.export(shell,str(OUT/'placed/BODY.step'))
    parts,meta,hardware=build_parts(p,shell,outer,raw)
    assembly=cq.Assembly(name='QUIETMIRROR_V07_MECHANICAL_TEST');records=[];scene=trimesh.Scene()
    for name,shape in parts.items():
        print('Export',name,flush=True)
        record=save_model(shape,name,OUT/'placed');flat=print_pose(shape,name,p)
        pm=save_model(flat,name,OUT/'print');record.update(meta[name]);record['print_bounds']=pm['bounds'];record['file']=f'exports/v07/placed/{name}.stl';record['print_file']=f'exports/v07/print/{name}.stl';records.append(record)
        assembly.add(shape,name=name,color=cq.Color(*meta[name]['color']))
        mesh=trimesh.load_mesh(OUT/'placed'/f'{name}.stl');mesh.visual.face_colors=[int(x*255) for x in meta[name]['color']]+[255];scene.add_geometry(mesh,node_name=name)
    for name,shape in hardware.items():
        cq.exporters.export(shape,str(OUT/'placed'/f'{name}.step'));shape.exportStl(str(OUT/'placed'/f'{name}.stl'),tolerance=.03,angularTolerance=.15,relative=False)
        assembly.add(shape,name=name,color=cq.Color(.76,.31,.21))
        mesh=trimesh.load_mesh(OUT/'placed'/f'{name}.stl');mesh.visual.face_colors=[194,79,54,255];scene.add_geometry(mesh,node_name=name)
    assembly.save(str(OUT/'quietmirror_V0.7_MECHANICAL_ASSEMBLY.step'))
    scene.units='mm';(OUT/'quietmirror_V0.7_MECHANICAL_VIEW_ONLY.3mf').write_bytes(trimesh.exchange.threemf.export_3MF(scene))
    report=dict(version='0.7',units='mm',parts=records,printable_parts=len(records),switch_examples=5,vent_count=layout['total_holes'],build_seconds=time.time()-start,parameters=p)
    (RP/'cad_metrics.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
    print('COMPLETE',len(records),'printable pieces',report['build_seconds'],flush=True)

if __name__=='__main__':main()
