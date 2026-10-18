"""V0.2 continuous shell, original CadQuery geometry; units mm.

Independent of commercial CAD. G-Wolves HSK/HTR inform only the visual direction.
See references/GWOLVES_REFERENCE.md. V0.1 remains intact.
"""
from pathlib import Path
import json, math, time, argparse, copy
import cadquery as cq
import trimesh
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box
from build_mouse import rounded_box,soft_box,beam,base_beam,envelope_defs
ROOT=Path(__file__).resolve().parents[1]
V=cq.Vector

def bounds(s):
    b=Bnd_Box(); BRepBndLib.AddOptimal_s(s.wrapped,b,False,False)
    return b.Get()

def arch(y,w,h):
    # Superellipse x^4/w^4 + z^4/h^4 = 1. Broad crown, continuous sides.
    pts=[]
    for i in range(41):
        a=math.pi*i/40; c=math.cos(a)
        pts.append(V(w*math.copysign(abs(c)**.5,c),-y,h*math.sin(a)**.5))
    return cq.Wire.assembleEdges([cq.Edge.makeSpline(pts),cq.Edge.makeLine(pts[-1],pts[0])])

def make_outer(p):
    stations=[]
    for d,w,h in p['shell_stations']:
        # Waist control changes independently from the overall width.
        waist=math.exp(-((d-46)/11)**2)
        w=w*p['max_width']/62+(p['grip_width']-54)*waist/2
        stations.append((d*p['length']/90,w,h*(p['height']-1)/30))
    outer=cq.Solid.makeLoft([arch(*st) for st in stations],ruled=False)
    bb=bounds(outer); xfactor=p['max_width']/(bb[3]-bb[0])
    outer=cq.Solid.makeLoft([arch(d,w*xfactor,h) for d,w,h in stations],ruled=False)
    clip=cq.Workplane('XY').box(200,300,100).val().translate((0,-60,50+p['shell_floor_z']))
    outer=outer.intersect(clip)
    # Keep the offset surface free of short fillet faces. Button/wheel/lip
    # radii are explicit below; the front shell rim needs light deburring.
    return outer

def create(p):
    outer=make_outer(p)
    body=cq.Workplane(obj=outer).faces('<Z').shell(-p['wall']).val()
    assert body.isValid() and len(body.Solids())==1
    print('hollow',body.ShapeType(),body.Volume(),flush=True)
    cq.exporters.export(body,str(ROOT/'.tools/v02_uncut_shell.step'))
    body=cq.importers.importStep(str(ROOT/'.tools/v02_uncut_shell.step')).val()
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
    parts={'continuous_shell':body}
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
            reach={8:28.0,43:26.2,61:27.0}[d]
            parts[f'wall_floor_link_{side}_{i}']=base_beam((side*21,-d*sy),(side*reach,-d*sy),2.8,2.6).translate((0,0,.6))
    sp=p['sensor'];x,y=sp['x'],-sp['y'];w=p['base_rib_width']
    ow,ol=sp['opening_width'],sp['opening_length'];z=sp['frame_z']
    parts['sensor_reference_frame']=rounded_box(ow+2*w,ol+2*w,p['wall'],3,(x,y,z+p['wall']/2)).cut(rounded_box(ow,ol,10,2,(x,y,z)))
    fx=ow/2+w/2;fy=ol/2+w/2
    for i,(a,b) in enumerate([(feet[0],(x-fx,y+fy)),(feet[1],(x+fx,y+fy)),(feet[2],(x-fx,y-fy)),(feet[3],(x+fx,y-fy))]):
        parts[f'floor_diagonal_{i}']=beam((*a,2.0),(*b,3.2),p['rib_diameter'])
    # One-sided low lip, kept within X=+31 and clear of the pad plane.
    parts['right_antidrag_lip']=soft_box(6,31,2.8,1.2,(p['max_width']/2-3,-50*sy,3.1))
    for i,b in enumerate(p['side_buttons']):
        # Inner reach is deliberately buried in the shell, no free floating key.
        parts[f'fixed_side_button_{i+1}']=soft_box(6.0,b['length'],4.8,1.2,(-p['grip_width']/2+.5,-b['y'],b['z']))
    wr=wheel['diameter']/2
    ws=cq.Solid.makeCylinder(wr,wheel['width'],V(wheel['x']-wheel['width']/2,wy,wz),V(1,0,0))
    parts['fixed_wheel']=cq.Workplane(obj=ws).edges().fillet(1).val()
    parts['fixed_wheel_axle']=beam((wheel['x']-7,wy,wz),(wheel['x']+7,wy,wz),2.8)
    for side in (-1,1):
        parts[f'wheel_support_{side}']=beam((wheel['x']+side*7,wy,wz),(side*12,wy-6,2.0),2.8)
        parts[f'wheel_base_tie_{side}']=base_beam((side*12,wy-6),feet[0 if side<0 else 1],2.6,2.6).translate((0,0,.6))
        # Upper tie spreads fixed wheel load into the continuous crown.
        parts[f'wheel_roof_tie_{side}']=beam((side*7,wy,wz),(side*10,wy,26.5*(p['height']/31)),2.8)
    print('Fusing',len(parts),'V0.2 components',flush=True)
    shapes=list(parts.values());solid=shapes[0].copy()
    for name,s in list(parts.items())[1:]:
        solid=solid.fuse(s.copy())
        if not solid.isValid():raise RuntimeError('Invalid union after '+name)
    return solid,parts,feet,outer

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--params',default=str(ROOT/'cad/parameters_v02.json'));args=parser.parse_args()
    p=json.loads(Path(args.params).read_text(encoding='utf8'));start=time.time()
    out=ROOT/'exports/v02';out.mkdir(parents=True,exist_ok=True)
    report=ROOT/'reports/v02';report.mkdir(parents=True,exist_ok=True)
    (ROOT/'.tools').mkdir(exist_ok=True)
    solid,parts,feet,outer=create(p)
    print('CAD',solid.isValid(),len(solid.Solids()),solid.Volume(),flush=True)
    assert solid.isValid() and len(solid.Solids())==1
    step=out/'quietmirror_fingertip_V0.2.step';cq.exporters.export(solid,str(step))
    solid=cq.importers.importStep(str(step)).val()
    raw=ROOT/'.tools/raw_v02.stl';solid.exportStl(str(raw),tolerance=.02,angularTolerance=.15,relative=False,parallel=False)
    m=trimesh.load_mesh(raw);raw_faces=len(m.faces)
    m.merge_vertices(digits_vertex=5);m.update_faces(m.nondegenerate_faces(height=1e-5));m.update_faces(m.unique_faces());m.remove_unreferenced_vertices()
    print('STL',len(m.faces),'watertight',m.is_watertight,flush=True)
    m.export(out/'quietmirror_fingertip_V0.2.stl')
    assert m.is_watertight and len(m.split(only_watertight=False))==1
    # Smooth original body is saved locally for independent wall-normal samples.
    cq.exporters.export(outer,str(ROOT/'.tools/v02_outer.step'))
    bb=bounds(solid)
    metrics=dict(version='0.2',units='mm',dimensions_xyz_mm=[bb[i+3]-bb[i] for i in range(3)],bounds=[list(bb[:3]),list(bb[3:])],volume_mm3=solid.Volume(),cad_valid=solid.isValid(),cad_solids=len(solid.Solids()),mesh_cleanup=dict(raw_faces=raw_faces,final_faces=len(m.faces),weld_tolerance_mm=1e-5,holes_patched=0,components_discarded=0),feet=[dict(id=i+1,x=x,y=y,diameter=p['foot_diameter'],bottom_z=0) for i,(x,y) in enumerate(feet)],parameters=p,build_seconds=time.time()-start)
    (report/'cad_metrics.json').write_text(json.dumps(metrics,indent=2,ensure_ascii=False),encoding='utf8')
    envs=envelope_defs(p);collisions=[]
    assy=cq.Assembly(solid.copy(),name='V0_2_fixed_print_model',color=cq.Color(.55,.65,.7,.2))
    for e in envs:
        box=cq.Workplane('XY').box(*e['size']).val().translate(e['center'])
        col=e['color'];rgb=[int(col[i:i+2],16)/255 for i in (1,3,5)]
        assy.add(box,name=e['name'],color=cq.Color(*rgb,.4))
        hits=[]
        for name,s in parts.items():
            vol=s.copy().intersect(box.copy()).Volume()
            if vol>.05:hits.append(dict(part=name,overlap_mm3=round(vol,3)))
        collisions.append(dict(envelope=e['name'],hits=hits))
    assy.save(str(out/'electronic_envelopes_V0.2_ESTIMATES.step'))
    (report/'envelope_interferences.json').write_text(json.dumps(dict(envelopes=envs,collisions=collisions),indent=2,ensure_ascii=False),encoding='utf8')
    print(json.dumps({k:v for k,v in metrics.items() if k not in ['feet','parameters']},indent=2),flush=True)

if __name__=='__main__':main()
