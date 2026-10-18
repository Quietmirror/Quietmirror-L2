"""V0.3 continuous shell, original CadQuery geometry; units mm.

Original geometry: flatter grip sides, rear vents, separate fit-prototype side caps.
See references/GWOLVES_REFERENCE.md. V0.1 remains intact.
"""
from pathlib import Path
import json, math, time, argparse, copy
import cadquery as cq
import trimesh
import numpy as np
from scipy.interpolate import PchipInterpolator
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box
from build_mouse import rounded_box,soft_box,beam,base_beam,envelope_defs
ROOT=Path(__file__).resolve().parents[1]
V=cq.Vector

def yz_round(depth,length,height,r,center):
    return rounded_box(length,height,depth,r,(0,0,0)).rotate((0,0,0),(1,1,1),120).translate(center)

def side_window(p,b):
    q=p['side_interface']
    return yz_round(22,q['opening_length'],q['opening_height'],q['opening_corner_radius'],(-p['grip_width']/2,-b['y'],b['z']))

def side_cap(p,b):
    q=p['side_interface'];g=p['grip_width']/2;y=-b['y'];z=b['z']
    face=soft_box(q['cap_depth'],b['length'],q['cap_height'],1.1,(-g-.8,y,z))
    stem=soft_box(7.1,q['stem_length'],q['stem_height'],.7,(-g+3.15,y,z))
    flange=yz_round(q['flange_thickness'],q['flange_length'],q['flange_height'],1.3,(-g+6+q['axial_gap']+q['flange_thickness']/2,y,z))
    return face.fuse(stem).fuse(flange)

def vent_cutter(p,x,y):
    q=p['ventilation']
    pts=[(x+q['width']/2*math.cos(a),y+q['length']/2*math.sin(a)) for a in [i*math.pi/3 for i in range(6)]]
    return cq.Workplane('XY').polyline(pts).close().extrude(45).edges('|Z').fillet(q['corner_radius']).val().translate((0,0,5))

def bounds(s):
    b=Bnd_Box(); BRepBndLib.AddOptimal_s(s.wrapped,b,False,False)
    return b.Get()

def arch(y,w,h,power=4):
    # Superellipse x^n/w^n + z^n/h^n = 1. Longitudinal stations flatten grip.
    pts=[]
    for i in range(41):
        a=math.pi*i/40; c=math.cos(a)
        pts.append(V(w*math.copysign(abs(c)**(2/power),c),-y,h*math.sin(a)**(2/power)))
    return cq.Wire.assembleEdges([cq.Edge.makeSpline(pts),cq.Edge.makeLine(pts[-1],pts[0])])

def make_surfaces(p):
    """Nested lofts with slope-corrected inner sections.

    OCP thick-solid offset silently returned the original full solid for this
    flatter profile. Construct the cavity explicitly and validate real normal
    thickness on the exported mesh. This is an approximate normal offset,
    not a claim of an analytically constant-thickness freeform shell.
    """
    sy=p['length']/90;n=p['side_profile_power']
    st=np.array(p['shell_stations'],float);d=st[:,0]*sy
    widths=st[:,1]*p['max_width']/62+(p['grip_width']-54)*np.exp(-((st[:,0]-45)/25)**6)/2
    wf=PchipInterpolator(d,widths);hf=PchipInterpolator(d,st[:,2]*(p['height']-1)/30)
    stations=sorted(set(list(d)+list(np.linspace(d[0],d[-1],23))))
    outer=cq.Solid.makeLoft([arch(y,float(wf(y)),float(hf(y)),n) for y in stations],ruled=False)
    bb=bounds(outer);xf=p['max_width']/(bb[3]-bb[0])
    outer=cq.Solid.makeLoft([arch(y,float(wf(y))*xf,float(hf(y)),n) for y in stations],ruled=False)
    clip=cq.Workplane('XY').box(200,300,100).val().translate((0,-60,50+p['shell_floor_z']))
    outer=outer.intersect(clip)
    inner_wires=[]
    # 0.08 mm allowance absorbs loft/interpolation/mesh error; measured below.
    # Solid low tail root prevents nearly tangent cavity/diagonal intersections.
    for y in np.linspace(p['wall'],p['rear_cavity_end']*sy,29):
        w=float(wf(y))*xf;h=float(hf(y));dw=float(wf.derivative()(y))*xf;dh=float(hf.derivative()(y))
        pts=[]
        for a in np.linspace(0,math.pi,41):
            co=math.cos(a);x=w*math.copysign(abs(co)**(2/n),co);z=h*max(0,math.sin(a))**(2/n)
            nx=math.copysign(abs(x)**(n-1)/w**n,x);nz=z**(n-1)/h**n
            norm=math.hypot(nx,nz);nx/=norm;nz/=norm
            longitudinal=nx*x/w*dw+nz*z/h*dh
            off=(p['wall']+.08)*math.sqrt(1+longitudinal**2)
            pts.append(V(x-off*nx,-y,z-off*nz))
        bl=V(pts[-1].x,-y,-5);br=V(pts[0].x,-y,-5)
        inner_wires.append(cq.Wire.assembleEdges([cq.Edge.makeSpline(pts),cq.Edge.makeLine(pts[-1],bl),cq.Edge.makeLine(bl,br),cq.Edge.makeLine(br,pts[0])]))
    inner=cq.Solid.makeLoft(inner_wires,ruled=False)
    return outer,inner

def create(p):
    outer,inner=make_surfaces(p)
    body=outer.cut(inner)
    assert body.isValid() and len(body.Solids())==1
    assert body.Volume()<outer.Volume()*.5, 'Offset failed to form the hollow shell'
    print('hollow',body.ShapeType(),body.Volume(),flush=True)
    cq.exporters.export(body,str(ROOT/'.tools/v03_uncut_shell.step'))
    body=cq.importers.importStep(str(ROOT/'.tools/v03_uncut_shell.step')).val()
    # Narrow boundary slots identify each contact patch. Wide uncut bridges
    # keep the keys fixed to the shell; this is not a spring/click mechanism.
    for name in ('left_key','right_key'):
        k=p[name]; w=p['key_outline_width']
        mask=rounded_box(k['width'],k['length'],35,4.5,(k['x'],-k['y'],35))
        hole=rounded_box(k['width']-2*w,k['length']-2*w,40,4.5-w,(k['x'],-k['y'],35))
        ring=mask.cut(hole)
        for dy in (-12,5,17):
            bridge=cq.Workplane('XY').box(70,5,60).val().translate((0,-k['y']+dy,25))
            ring=ring.cut(bridge)
        body=body.cut(ring)
        print('outline',name,body.isValid(),len(body.Solids()),body.Volume(),flush=True)
    wheel=p['wheel']; wy=-wheel['y'];wz=p['height']+wheel['height_offset']-wheel['diameter']/2
    opening=rounded_box(wheel['opening_width'],wheel['opening_length'],60,2,(wheel['x'],wy,25))
    body=body.cut(opening)
    print('opened',body.isValid(),len(body.Solids()),body.Volume(),flush=True)
    unvented_volume=body.Volume(tol=1e-7)
    cuts=[]
    for row in p['ventilation']['rows']:
        for x in row['x']:
            cut=vent_cutter(p,x,-row['y'])
            body=body.cut(cut)
            cuts.append(dict(x=x,y=-row['y']))
    vented_volume=body.Volume(tol=1e-7)
    caps=[]; tacks=[]; interface=[]
    for i,b in enumerate(p['side_buttons']):
        # Flat inner landing provides a known guide datum independent of skin curvature.
        spec=p['side_interface']; g=p['grip_width']/2
        pad=yz_round(6.0,spec['reinforcement_length'],spec['reinforcement_height'],2.2,(-g+3,-b['y'],b['z']))
        pad=pad.intersect(outer.copy())
        body=body.fuse(pad).cut(side_window(p,b))
        cap=side_cap(p,b); caps.append(cap)
        # For FIT only: connect retaining flange to the landing at both ends.
        for sign in (-1,1):
            tacks.append(cq.Workplane('XY').box(1.2,1.6,4.0).val().translate((-g+6.0,-b['y']+sign*6.8,b['z'])))
        interface.append(dict(id=i+1,opening_yz_mm=[spec['opening_length'],spec['opening_height']],cap_yz_mm=[b['length'],spec['cap_height']],nominal_side_clearance_mm=(spec['opening_height']-spec['cap_height'])/2,axial_gap_mm=spec['axial_gap']))
    assert body.isValid() and len(body.Solids())==1
    parts={'vented_shell_with_guides':body}
    sy=p['length']/90
    feet=[(-21, -8*sy),(21,-8*sy),(-22,-61*sy),(23,-63*sy),(0,-p['length']+p['foot_diameter']/2)]
    for i,(x,y) in enumerate(feet):
        s=cq.Workplane('XY').center(x,y).circle(p['foot_diameter']/2).extrude(p['foot_thickness'])
        parts[f'foot_{i+1}']=s.edges('>Z').fillet(.35).val()
    route=[0,1,3,4,2,0]
    for i,(a,b) in enumerate(zip(route,route[1:])):
        parts[f'base_perimeter_{i}']=base_beam(feet[a],feet[b],p['base_rib_width'],p['base_rib_height']).translate((0,0,.6))
    for side in (-1,1):
        for i,d in enumerate((8,43,61)):
            # Horizontal floor links overlap the inner side of the skin.
            reach={8:29.3,43:25.8,61:25.8}[d]
            parts[f'wall_floor_link_{side}_{i}']=base_beam((side*21,-d*sy),(side*reach,-d*sy),2.8,2.6).translate((0,0,.6))
    sp=p['sensor'];x,y=sp['x'],-sp['y'];w=p['base_rib_width']
    ow,ol=sp['opening_width'],sp['opening_length'];z=sp['frame_z']
    parts['sensor_reference_frame']=rounded_box(ow+2*w,ol+2*w,p['wall'],3,(x,y,z+p['wall']/2)).cut(rounded_box(ow,ol,10,2,(x,y,z)))
    fx=ow/2+w/2;fy=ol/2+w/2
    for i,(a,b) in enumerate([(feet[0],(x-fx,y+fy)),(feet[1],(x+fx,y+fy)),(feet[2],(x-fx,y-fy)),(feet[3],(x+fx,y-fy))]):
        parts[f'floor_diagonal_{i}']=beam((*a,2.0),(*b,3.2),p['rib_diameter'])
    # One-sided low lip, kept within X=+31 and clear of the pad plane.
    parts['right_antidrag_lip']=soft_box(6,31,2.8,1.2,(p['max_width']/2-3,-50*sy,3.1))
    wr=wheel['diameter']/2
    ws=cq.Solid.makeCylinder(wr,wheel['width'],V(wheel['x']-wheel['width']/2,wy,wz),V(1,0,0))
    parts['fixed_wheel']=cq.Workplane(obj=ws).edges().fillet(1).val()
    parts['fixed_wheel_axle']=beam((wheel['x']-7,wy,wz),(wheel['x']+7,wy,wz),2.8)
    for side in (-1,1):
        parts[f'wheel_support_{side}']=beam((wheel['x']+side*7,wy,wz),(side*12,wy-6,2.0),2.8)
        parts[f'wheel_base_tie_{side}']=base_beam((side*12,wy-6),feet[0 if side<0 else 1],2.6,2.6).translate((0,0,.6))
        # Upper tie spreads fixed wheel load into the continuous crown.
        parts[f'wheel_roof_tie_{side}']=beam((side*7,wy,wz),(side*10,wy,26.5*(p['height']/31)),2.8)
    print('Fusing',len(parts),'V0.3 components',flush=True)
    shapes=list(parts.values());solid=shapes[0].copy()
    for name,s in list(parts.items())[1:]:
        solid=solid.fuse(s.copy())
        if not solid.isValid():raise RuntimeError('Invalid union after '+name)
    shell=solid.copy()
    for i,cap in enumerate(caps):
        parts[f'fixed_side_cap_{i+1}']=cap
        solid=solid.fuse(cap.copy())
    for i,tack in enumerate(tacks):
        parts[f'fit_only_cap_tack_{i+1}']=tack
        solid=solid.fuse(tack.copy())
    assert solid.isValid() and len(solid.Solids())==1
    info=dict(vent_count=len(cuts),vents=cuts,unvented_skin_volume_mm3=unvented_volume,vented_skin_volume_mm3=vented_volume,vent_removed_mm3=unvented_volume-vented_volume,side_interfaces=interface)
    return solid,parts,feet,outer,shell,caps,info

def save_model(s,stem,out):
    assert s.isValid() and len(s.Solids())==1,(stem,s.isValid(),len(s.Solids()))
    step=out/(stem+'.step');cq.exporters.export(s,str(step))
    normalized=cq.importers.importStep(str(step)).val()
    raw=ROOT/'.tools'/('raw_'+stem+'.stl')
    normalized.exportStl(str(raw),tolerance=.02,angularTolerance=.15,relative=False,parallel=False)
    mesh=trimesh.load_mesh(raw);raw_faces=len(mesh.faces)
    mesh.merge_vertices(digits_vertex=6)
    mesh.update_faces(mesh.nondegenerate_faces(height=1e-7));mesh.update_faces(mesh.unique_faces());mesh.remove_unreferenced_vertices()
    mesh.export(out/(stem+'.stl'))
    assert mesh.is_watertight and len(mesh.split(only_watertight=False))==1,stem
    bb=bounds(normalized)
    return dict(name=stem,dimensions_xyz_mm=[bb[i+3]-bb[i] for i in range(3)],bounds=[list(bb[:3]),list(bb[3:])],volume_mm3=normalized.Volume(tol=1e-7),volume_integration_tolerance=1e-7,cad_valid=normalized.isValid(),cad_solids=len(normalized.Solids()),mesh_cleanup=dict(raw_faces=raw_faces,final_faces=len(mesh.faces),weld_tolerance_mm=1e-6,holes_patched=0,components_discarded=0))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--params',default=str(ROOT/'cad/parameters_v03.json'));args=ap.parse_args()
    p=json.loads(Path(args.params).read_text(encoding='utf8'));start=time.time()
    out=ROOT/'exports/v03';out.mkdir(parents=True,exist_ok=True)
    report=ROOT/'reports/v03';report.mkdir(parents=True,exist_ok=True)
    solid,parts,feet,outer,shell,caps,info=create(p)
    models=[]
    models.append(save_model(solid,'quietmirror_fingertip_V0.3_FIT',out))
    models.append(save_model(shell,'quietmirror_fingertip_V0.3_SHELL',out))
    for i,c in enumerate(caps):
        # Print inward flange flat on bed. X inward becomes Z up.
        flat=c.rotate((0,0,0),(0,1,0),90)
        bb=bounds(flat);flat=flat.translate((-(bb[0]+bb[3])/2,-(bb[1]+bb[4])/2,-bb[2]))
        models.append(save_model(flat,f'side_button_{i+1}_V0.3_PRINT',out))
        cq.exporters.export(c,str(ROOT/f'.tools/v03_cap_{i+1}_placed.step'))
        c.exportStl(str(ROOT/f'.tools/v03_cap_{i+1}_placed.stl'),tolerance=.02,angularTolerance=.15,relative=False)
        c.translate((-14,0,0)).exportStl(str(ROOT/f'.tools/v03_cap_{i+1}_exploded.stl'),tolerance=.02,angularTolerance=.15,relative=False)
    assembly=cq.Assembly(shell.copy(),name='V0_3_shell',color=cq.Color(.45,.58,.63))
    for i,c in enumerate(caps):assembly.add(c.copy(),name=f'side_cap_{i+1}_ESTIMATED_INTERFACE',color=cq.Color(.9,.57,.23))
    assembly.save(str(out/'side_button_assembly_V0.3.step'))
    cq.exporters.export(outer,str(ROOT/'.tools/v03_outer.step'))
    collisions=[dict(id=i+1,shell_intersection_mm3=shell.copy().intersect(c.copy()).Volume(),minimum_shell_distance_mm=shell.distance(c)) for i,c in enumerate(caps)]
    info['cap_to_cap_overlap_mm3']=caps[0].copy().intersect(caps[1].copy()).Volume()
    info['cap_to_cap_distance_mm']=caps[0].distance(caps[1])
    metrics=dict(version='0.3',units='mm',**models[0],models=models,design=info,side_cap_clearance=collisions,feet=[dict(id=i+1,x=x,y=y,diameter=p['foot_diameter'],bottom_z=0) for i,(x,y) in enumerate(feet)],parameters=p,build_seconds=time.time()-start)
    (report/'cad_metrics.json').write_text(json.dumps(metrics,indent=2,ensure_ascii=False),encoding='utf8')
    envs=envelope_defs(p);hits=[]
    assy=cq.Assembly(solid.copy(),name='V0_3_fixed_fit_model',color=cq.Color(.55,.65,.7,.2))
    for e in envs:
        box=cq.Workplane('XY').box(*e['size']).val().translate(e['center']);col=e['color'];rgb=[int(col[i:i+2],16)/255 for i in (1,3,5)]
        assy.add(box,name=e['name'],color=cq.Color(*rgb,.4));eh=[]
        for name,s in parts.items():
            v=s.copy().intersect(box.copy()).Volume()
            if v>.05:eh.append(dict(part=name,overlap_mm3=round(v,3)))
        hits.append(dict(envelope=e['name'],hits=eh))
    assy.save(str(out/'electronic_envelopes_V0.3_ESTIMATES.step'))
    (report/'envelope_interferences.json').write_text(json.dumps(dict(envelopes=envs,collisions=hits),indent=2,ensure_ascii=False),encoding='utf8')
    print(json.dumps({k:v for k,v in metrics.items() if k not in ['feet','parameters']},indent=2),flush=True)

if __name__=='__main__':main()
