"""V0.6: symmetric recessed base, contour vents, central charge/switch ports.

Original CadQuery source, CERN-OHL-P-2.0; units millimetres. Electronics are
separate estimated assemblies, never fused into the one-piece FIT print.
"""
from pathlib import Path
import json,time,copy
import cadquery as cq
import numpy as np
import trimesh
from build_mouse import rounded_box,beam,base_beam
from build_v03 import bounds,yz_round,side_window,side_cap
from build_v05 import make_surfaces,save_model,clip_above
from vent_layout_v06 import cells,cutter,manifest
ROOT=Path(__file__).resolve().parents[1];V=cq.Vector

def union(parts):
    s=parts[0].copy()
    for a in parts[1:]:s=s.fuse(a.copy())
    assert s.isValid(), 'invalid union'
    return s

def create(p):
    print('Building symmetric loft',flush=True)
    outer,inner=make_surfaces(p);skin=outer.cut(inner)
    cq.exporters.export(skin,str(ROOT/'.tools/v06_uncut.step'))
    skin=cq.importers.importStep(str(ROOT/'.tools/v06_uncut.step')).val()
    for name in ('left_key','right_key'):
        k=p[name];w=p['key_outline_width']
        ring=rounded_box(k['width'],k['length'],55,4.5,(k['x'],-k['y'],27.5)).cut(rounded_box(k['width']-2*w,k['length']-2*w,60,4.5-w,(k['x'],-k['y'],27.5)))
        for dy in (-12,5,17):ring=ring.cut(cq.Workplane('XY').box(70,5,70).val().translate((0,-k['y']+dy,25)))
        skin=skin.cut(ring.intersect(clip_above(6)))
    w=p['wheel'];wy=-w['y'];wz=p['height']+w['height_offset']-w['diameter']/2
    skin=skin.cut(rounded_box(w['opening_width'],w['opening_length'],60,2,(0,wy,25)))
    unvented=skin.Volume(tol=1e-7)
    outline,domain,items=cells(p,outer)
    print('Generated',len(items),'contour holes',flush=True)
    (ROOT/'reports/v06/vent_layout.json').write_text(json.dumps(manifest(p,outline,domain,items),indent=2),encoding='utf8')
    cutters=[cutter(a) for a in items]
    for a,t in zip(items,cutters):
        print('cut',a['id'],'skin',skin.isValid(),'tool',t.isValid(),flush=True)
        skin=skin.cut(t.copy(),tol=1e-5);assert skin.isValid(),a['id']
    # Two steep shoulder webs keep the same 2.2 mm top aperture spacing, but
    # receive 2 mm round underside rails. Vertical cutters otherwise leave a
    # short diagonal wall chord here. No change to the outside contact skin.
    outer.exportStl(str(ROOT/'.tools/v06_outer_for_ribs.stl'),tolerance=.02,angularTolerance=.12,relative=False)
    om=trimesh.load_mesh(ROOT/'.tools/v06_outer_for_ribs.stl');byid={a['id']:a for a in items};ribpaths=[]
    a,b=byid['H07'],byid['H11'];edge=a['cell'].boundary.intersection(b['cell'].buffer(1e-7))
    if edge.geom_type=='MultiLineString':edge=max(edge.geoms,key=lambda e:e.length)
    path=[]
    for f in np.linspace(.08,.92,9):
        pt=edge.interpolate(float(f),normalized=True);loc,_,tri=om.ray.intersects_location([[pt.x,-pt.y,50]],[[0,0,-1]],multiple_hits=True)
        j=np.argmax(loc[:,2]);normal=om.face_normals[tri[j]];path.append((loc[j]-normal*1.7).tolist())
    for sign in (-1,1):
        mirrored=[(sign*x,y,z) for x,y,z in path]
        rail=union([beam(a,b,2.0) for a,b in zip(mirrored,mirrored[1:])]).intersect(outer)
        skin=skin.fuse(rail);ribpaths.append(mirrored)
    (ROOT/'reports/v06/underside_web_rails.json').write_text(json.dumps(dict(diameter_mm=2.0,outer_normal_offset_mm=1.7,paths=ribpaths),indent=2),encoding='utf8')
    vented=skin.Volume(tol=1e-7)
    cq.exporters.export(skin,str(ROOT/'.tools/v06_vented_skin.step'))
    # Centre-line front USB-C opening, including a cable plug clearance in the
    # electronics models. This aperture is provisional, not donor dimensions.
    usb=p['usb_port']
    port=rounded_box(usb['width'],usb['height'],16,usb['radius'],(0,0,0)).rotate((0,0,0),(1,0,0),90).translate((0,-2,usb['z']))
    skin=skin.cut(port)
    feet=[(-21,-8),(21,-8),(-21.5,-61.5),(21.5,-61.5),(0,-81.5)]
    base=[]
    for x,y in feet:
        base.append(cq.Workplane('XY').center(x,y).circle(p['foot_diameter']/2).extrude(p['foot_thickness']).edges('>Z').fillet(.35).val())
    route=[0,1,3,4,2,0]
    for a,b in zip(route,route[1:]):base.append(base_beam(feet[a],feet[b],p['base_rib_width'],p['base_rib_height']).translate((0,0,.6)))
    for side in (-1,1):
        for d,reach in [(8,29.5),(43,26),(61.5,26)]:
            base.append(base_beam((side*21,-d),(side*reach,-d),2.8,2.6).translate((0,0,.6)))
    sp=p['sensor'];ow,ol=sp['opening_width'],sp['opening_length'];bw=p['base_rib_width'];sy=-sp['y']
    base.append(rounded_box(ow+2*bw,ol+2*bw,p['wall'],3,(0,sy,sp['frame_z']+p['wall']/2)).cut(rounded_box(ow,ol,12,2,(0,sy,sp['frame_z']))))
    fx=ow/2+bw/2;fy=ol/2+bw/2
    for a,b in [(feet[0],(-fx,sy+fy)),(feet[1],(fx,sy+fy)),(feet[2],(-fx,sy-fy)),(feet[3],(fx,sy-fy))]:base.append(beam((*a,2),(*b,3.2),p['rib_diameter']))
    sw=p['power_switch']
    switch_bridge=rounded_box(12,8,2,1.5,(0,-sw['d'],2.8)).cut(rounded_box(sw['opening_x'],sw['opening_d'],15,.6,(0,-sw['d'],3)))
    base.append(switch_bridge)
    for side in (-1,1):base.append(base_beam((side*5,-sw['d']),(side*12,-sw['d']),2.6,2.6).translate((0,0,.6)))
    bottom=union(base)
    floor=cq.Workplane(obj=outer).section(p['shell_floor_z']+.001).val()
    outline_face=max(floor.Faces(),key=lambda f:f.Area())
    prism=cq.Solid.extrudeLinear(outline_face.outerWire(),[],V(0,0,15)).translate((0,0,-p['shell_floor_z']-.001))
    bottom=bottom.intersect(prism)
    print('Base connected',len(bottom.Solids()),flush=True)
    # Intersect the whole base with the same outer silhouette; all foot disks
    # remain intact. No right lip, rear protruding skate, or asymmetric brace.
    symmetric=union([skin,bottom]);assert len(symmetric.Solids())==1,('symmetric',len(symmetric.Solids()))
    cq.exporters.export(symmetric,str(ROOT/'.tools/v06_symmetric_body.step'))
    bottom.exportStl(str(ROOT/'.tools/v06_base.stl'),tolerance=.02,angularTolerance=.15,relative=False)
    shell=symmetric.copy();caps=[];tacks=[];guide_checks=[]
    for i,b in enumerate(p['side_buttons']):
        q=p['side_interface'];g=p['grip_width']/2
        pad=yz_round(6,q['reinforcement_length'],q['reinforcement_height'],1.6,(-g+3,-b['y'],b['z'])).intersect(outer.copy())
        overlap=sum(pad.intersect(t).Volume(tol=1e-7) for t in cutters)
        guide_checks.append(dict(id=i+1,vent_overlap_mm3=overlap,vent_min_distance_mm=min(pad.distance(t) for t in cutters)))
        assert overlap<1e-5,guide_checks[-1]
        shell=shell.fuse(pad).cut(side_window(p,b));caps.append(side_cap(p,b))
        for sign in (-1,1):tacks.append(cq.Workplane('XY').box(1.2,1.6,4).val().translate((-g+6,-b['y']+sign*6.8,b['z'])))
    assert shell.isValid() and len(shell.Solids())==1
    fixedwheel=cq.Workplane(obj=cq.Solid.makeCylinder(w['diameter']/2,w['width'],V(-w['width']/2,wy,wz),V(1,0,0))).edges().fillet(1).val()
    fit_parts=[shell,fixedwheel,beam((-7,wy,wz),(7,wy,wz),2.8)]
    for side in (-1,1):
        fit_parts.extend([beam((side*12,-23,2),(side*7,wy,wz),2.8),base_beam((side*12,-23),feet[0 if side<0 else 1],2.6,2.6).translate((0,0,.6)),beam((side*7,wy,wz),(side*10,wy,p['wheel_roof_tie_z']),2.8)])
    fit=union(fit_parts+caps+tacks)
    assert len(fit.Solids())==1,('fit',len(fit.Solids()))
    info=dict(vent_count=len(items),vent_guide_checks=guide_checks,unvented_skin_volume_mm3=unvented,vented_skin_volume_mm3=vented,vent_removed_mm3=unvented-vented,base_rebuilt=True,side_key_exceptions='Two left caps, windows, guide pads and FIT tacks only. Electronics internals are not subject to external-shell mirror symmetry.')
    return fit,shell,caps,outer,symmetric,feet,info

def main():
    p=json.loads((ROOT/'cad/parameters_v06.json').read_text());start=time.time()
    out=ROOT/'exports/v06';report=ROOT/'reports/v06'
    for d in (out,report,ROOT/'.tools'):d.mkdir(parents=True,exist_ok=True)
    fit,shell,caps,outer,sym,feet,info=create(p)
    models=[save_model(fit,'quietmirror_fingertip_V0.6_FIT',out),save_model(shell,'quietmirror_fingertip_V0.6_SHELL',out)]
    for i,c in enumerate(caps):
        flat=c.rotate((0,0,0),(0,1,0),90);bb=bounds(flat);flat=flat.translate((-(bb[0]+bb[3])/2,-(bb[1]+bb[4])/2,-bb[2]))
        models.append(save_model(flat,f'side_button_{i+1}_V0.6_PRINT',out))
        cq.exporters.export(c,str(ROOT/f'.tools/v06_cap_{i+1}_placed.step'))
        c.exportStl(str(ROOT/f'.tools/v06_cap_{i+1}_placed.stl'),tolerance=.02,angularTolerance=.15,relative=False)
    cq.exporters.export(outer,str(ROOT/'.tools/v06_outer.step'))
    outer.exportStl(str(ROOT/'.tools/v06_outer.stl'),tolerance=.025,angularTolerance=.12,relative=False)
    clearance=[dict(id=i+1,shell_intersection_mm3=shell.intersect(c).Volume(tol=1e-7),minimum_shell_distance_mm=shell.distance(c)) for i,c in enumerate(caps)]
    assert all(c['shell_intersection_mm3']<1e-5 and c['minimum_shell_distance_mm']>.05 for c in clearance),clearance
    metrics=dict(version='0.6',units='mm',**models[0],models=models,design=info,side_cap_clearance=clearance,feet=[dict(id=i+1,x=x,y=y,diameter_mm=p['foot_diameter']) for i,(x,y) in enumerate(feet)],parameters=p,build_seconds=time.time()-start)
    (report/'cad_metrics.json').write_text(json.dumps(metrics,indent=2,ensure_ascii=False),encoding='utf8')
    print(json.dumps(dict(build_seconds=metrics['build_seconds'],models=models,design=info),indent=2),flush=True)
if __name__=='__main__':main()
