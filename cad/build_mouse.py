"""Quietmirror fingertip mouse V0.1, original parametric CadQuery geometry.

Export coordinates: X right (+ is ring/pinky side), Y forward (front at 0,
rear at -length), Z up. JSON y parameters are positive distances from the
front, mirrored into right-handed export coordinates at the end.
Foot adhesive planes are Z=0. All dimensions in millimetres.
References are documented in references/REFERENCE_REVIEW.md. No upstream
SCAD code, meshes, hand measurements or PCB mounting patterns are reused.
"""
from pathlib import Path
import json, math, argparse, time, copy
import cadquery as cq
import trimesh
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box

ROOT = Path(__file__).resolve().parents[1]
V = cq.Vector

def rounded_box(w, l, h, r, center):
    s = cq.Workplane("XY").box(w,l,h).edges("|Z").fillet(r).val()
    return s.translate(center)

def soft_box(w,l,h,r,center):
    return cq.Workplane("XY").box(w,l,h).edges().fillet(r).val().translate(center)

def beam(a,b,d):
    a,b = V(*a),V(*b)
    dv=b-a
    c=cq.Solid.makeCylinder(d/2,dv.Length,a,dv.normalized())
    return c.fuse(cq.Solid.makeSphere(d/2,a,angleDegrees1=-90),cq.Solid.makeSphere(d/2,b,angleDegrees1=-90)).clean()

def base_beam(a,b,w,h):
    x=(a[0]+b[0])/2; y=(a[1]+b[1])/2
    length=math.dist(a,b)+w
    angle=math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))
    return cq.Workplane("XY").center(x,y).slot2D(length,w,angle).extrude(h).val()

def contact_plate(spec,p):
    """Spherical smooth field, 1.8 normal wall, reinforced R1 edge band."""
    x,y,z=spec['x'],spec['y'],spec['top_z']
    r=spec['curvature_radius']; t=p['contact_rim_thickness']
    c=V(x,y,z-r)
    outer=cq.Solid.makeSphere(r,c,angleDegrees1=-90)
    inner=cq.Solid.makeSphere(r-t,c,angleDegrees1=-90)
    clip=rounded_box(spec['width'],spec['length'],12,4.5,(x,y,z-4))
    shell=outer.cut(inner).intersect(clip).clean()
    shell=cq.Workplane(obj=shell).edges().fillet(p['contact_edge_radius']).val()
    # Pocket the underside field, preserving a reinforced rounded perimeter.
    pocket=cq.Solid.makeSphere(r-p['wall'],c,angleDegrees1=-90)
    mask=rounded_box(spec['width']-7,spec['length']-7,14,3,(x,y,z-5))
    return shell.cut(pocket.intersect(mask)).clean()

def side_plate(spec,p,side):
    # Construct a top-facing dish then rotate it to the left/right side.
    # Concave outside surface: the center is recessed relative to its edges.
    r=spec['curvature_radius']; t=p['contact_rim_thickness']
    # Local X = mouse Y; local Y = mouse Z; local Z maps to inward X.
    c=V(0,0,-r)
    outside=cq.Solid.makeSphere(r+t,c,angleDegrees1=-90)
    inside=cq.Solid.makeSphere(r,c,angleDegrees1=-90)
    clip=rounded_box(spec['length'],spec['height'],10,4,(0,0,0))
    shell=outside.cut(inside).intersect(clip).clean()
    shell=cq.Workplane(obj=shell).edges().fillet(p['contact_edge_radius']).val()
    # Remove 0.6 from the inner face in the middle (leave outer touch face).
    mid=cq.Solid.makeSphere(r+p['wall'],c,angleDegrees1=-90)
    cut=outside.cut(mid).intersect(rounded_box(spec['length']-7,spec['height']-7,10,2.8,(0,0,0)))
    shell=shell.cut(cut).clean()
    # Cyclic permutation X->Y, Y->Z, Z->X: 120 degrees around (1,1,1).
    shell=shell.rotate((0,0,0),(1,1,1),120)
    if side==1:
        shell=shell.mirror("YZ")
    return shell.translate((side*p['grip_width']/2,spec['y'],spec['z']))

def create(p):
    p=copy.deepcopy(p)
    for name in ('left_key','right_key','wheel'):
        p[name]['top_z']=p['height']+p[name]['height_offset']
    parts={}; d=p['rib_diameter']; w=p['base_rib_width']; bh=p['base_rib_height']
    sy=p['length']/90.0
    # Only noncontact skeleton stations scale with nominal length. Key/contact
    # placements remain explicit independent parameters in parameters.json.
    feet=[(-21,8*sy),(21,8*sy),(-23,61*sy),(25,63*sy),(0,p['length']-p['foot_diameter']/2)]
    def rail_x(side,y):
        a,b=feet[0 if side==-1 else 1],feet[2 if side==-1 else 3]
        if y>b[1]: a,b=b,feet[4]
        return a[0]+(b[0]-a[0])*(y-a[1])/(b[1]-a[1])
    def side_anchor(side,y,z):
        spec=p['thumb_contact' if side==-1 else 'right_contact']
        r=spec['curvature_radius']
        sag=r-math.sqrt(r*r-(y-spec['y'])**2-(z-spec['z'])**2)
        # Embed the cap fully inside a small inboard saddle. This preserves
        # the uninterrupted outer face and avoids fragile grazing junctions.
        anchor=(side*(p['grip_width']/2+sag-2.3),y,z)
        parts[f'inner_pad_{side}_{y}_{z}']=soft_box(p['inner_anchor_pad_depth'],p['inner_anchor_pad_span'],p['inner_anchor_pad_span'],.65,anchor)
        return anchor
    for i,(x,y) in enumerate(feet):
        s=cq.Workplane("XY").center(x,y).circle(p['foot_diameter']/2).extrude(p['foot_thickness'])
        parts[f'foot_{i+1}']=s.edges('>Z').fillet(.35).val()
    route=[0,1,3,4,2,0]
    for i,(a,b) in enumerate(zip(route,route[1:])):
        parts[f'base_perimeter_{i}']=base_beam(feet[a],feet[b],w,bh)
    # Front bumper fixes overall X span; all five platforms share the Z=0 plane.
    tip=p['max_width']/2-w/2
    parts['front_bumper']=base_beam((-tip,w/2),(tip,w/2),w,bh)
    for sign,foot in [(-1,feet[0]),(1,feet[1])]:
        parts[f'front_diagonal_{sign}']=base_beam((sign*tip,w/2),foot,w,bh)
    sx,cy=p['sensor']['x'],p['sensor']['y']
    z=p['sensor']['frame_z']; ow=p['sensor']['opening_width']; ol=p['sensor']['opening_length']
    outer=rounded_box(ow+2*w,ol+2*w,p['wall'],3,(sx,cy,z+p['wall']/2))
    inner=rounded_box(ow,ol,10,2,(sx,cy,z+p['wall']/2))
    parts['sensor_reference_frame']=outer.cut(inner)
    fx=ow/2+w/2; fy=ol/2+w/2
    for i,(a,b) in enumerate([(feet[0],(sx-fx,cy-fy)),(feet[1],(sx+fx,cy-fy)),(feet[2],(sx-fx,cy+fy)),(feet[3],(sx+fx,cy+fy))]):
        parts[f'floor_diagonal_{i}']=beam((*a,1.4),(*b,3.2),d)
    parts['left_fixed_key']=contact_plate(p['left_key'],p)
    parts['right_fixed_key']=contact_plate(p['right_key'],p)
    parts['thumb_contact']=side_plate(p['thumb_contact'],p,-1)
    parts['ring_pinky_contact']=side_plate(p['right_contact'],p,1)
    # Triple support under each fixed key; not an operational click mechanism.
    for side,which in [(-1,'left_key'),(1,'right_key')]:
        k=p[which]; x=k['x']+side*(k['width']/2-3)
        for i,y in enumerate([k['y']-13,k['y'],k['y']+14]):
            top=k['top_z']-((x-k['x'])**2+(y-k['y'])**2)/(2*k['curvature_radius'])-2.0
            bottom=(rail_x(side,y),y,2.0)
            parts[f'key_strut_{side}_{i}']=beam(bottom,(x,y,top),d)
        parts[f'key_side_brace_{side}']=beam((x,k['y']+14,top-1),side_anchor(side,46,18),d)
    # Side contact panels connect at several separated load paths to the feet.
    for side in [-1,1]:
        for i,(ybase,ytop,ztop) in enumerate([(23,29,10),(48,47,10),(64,62,8)]):
            parts[f'grip_strut_{side}_{i}']=beam((rail_x(side,ybase),ybase,2.0),side_anchor(side,ytop,ztop),d)
        parts[f'grip_front_tie_{side}']=beam((rail_x(side,22),22,2.0),side_anchor(side,29,17),d)
    parts['right_antidrag_lip']=soft_box(6,34,2.8,1.2,(p['max_width']/2-3,51,3.0))
    parts['right_lip_bridge']=beam((25,60,2),(28,60,3),d)
    for i,spec in enumerate(p['side_buttons']):
        parts[f'fixed_side_button_{i+1}']=soft_box(4.6,spec['length'],4.8,1.2,(-p['grip_width']/2-.25,spec['y'],spec['z']))
        parts[f'side_button_join_{i+1}']=beam(side_anchor(-1,spec['y'],18),(-p['grip_width']/2,spec['y'],spec['z']-1),d)
    # Low rear brace, large open space above it for palm avoidance.
    parts['rear_low_left']=beam((-23,61*sy,2),(0,80*sy,6),d)
    parts['rear_low_right']=beam((25,63*sy,2),(0,80*sy,6),d)
    parts['rear_low_tail']=beam((0,80*sy,6),(*feet[4],1.4),d)
    wheel=p['wheel']; wr=wheel['diameter']/2; wz=wheel['top_z']-wr
    ws=cq.Solid.makeCylinder(wr,wheel['width'],V(wheel['x']-wheel['width']/2,wheel['y'],wz),V(1,0,0))
    parts['fixed_wheel']=cq.Workplane(obj=ws).edges().fillet(1.0).val()
    parts['fixed_wheel_axle']=beam((wheel['x']-7,wheel['y'],wz),(wheel['x']+7,wheel['y'],wz),d)
    for side in [-1,1]:
        parts[f'wheel_support_{side}']=beam((wheel['x']+side*7,wheel['y'],wz),(wheel['x']+side*12,wheel['y']+6,2),d)
        parts[f'wheel_base_tie_{side}']=base_beam((wheel['x']+side*12,wheel['y']+6),(side*21,8*sy),w,bh)
    print('Fusing',len(parts),'components',flush=True)
    # Positive rearward stations become conventional right-handed CAD Y.
    parts={name:s.mirror('XZ') for name,s in parts.items()}
    copied=[s.copy() for s in parts.values()]
    # Keep the valid boolean faces: OCCT's optional same-domain refinement
    # creates a degenerate face at a multi-rib junction in this geometry.
    # Sequential unions avoid an OCCT all-at-once coincidence failure.
    solid=copied[0]
    for component in copied[1:]: solid=solid.fuse(component)
    feet=[(x,-y) for x,y in feet]
    return solid,parts,feet

def envelope_defs(p):
    # All except the cited bare breakout outline are deliberately provisional.
    # These are design-space reservation boxes, NOT a donor reverse-engineering.
    envelopes=[
        dict(name='main_pcb_and_components_EST',size=[38,46,6],center=[2,49,13],color='#e8a441',note='Estimated main PCB + components; actual donor unknown'),
        dict(name='reference_breakout_pcb',size=[15.5,28,1.6],center=[0,48,7.5],color='#45a78f',note='badjeff reference bare PCB outline only; position estimated'),
        dict(name='sensor_package_EST',size=[12,12,4],center=[0,48,5.5],color='#63c4b3',note='Estimated package under reference PCB; not a PixArt package dimension'),
        dict(name='lens_EST',size=[12,14,3.2],center=[0,48,2.6],color='#43b9d1',note='Lens model and optical datum TBD; sensor axis +Z'),
        dict(name='wheel_rotation_EST',size=[6.4,16.4,16.4],center=[p['wheel']['x'],p['wheel']['y'],p['height']+p['wheel']['height_offset']-p['wheel']['diameter']/2],color='#d87e99',note='Estimated rotation clearance, intentionally overlaps fixed tactile wheel'),
        dict(name='encoder_EST',size=[5,12,12],center=[-8,p['wheel']['y'],21],color='#c05989',note='Estimated encoder and shaft; actual height TBD'),
        dict(name='middle_switch_EST',size=[6,6,6],center=[7,p['wheel']['y'],18.5],color='#a55d9f',note='Estimated wheel-click mechanism'),
        dict(name='left_switch_EST',size=[6,13,7],center=[-16,22,23],color='#b681b9',note='Estimated switch, no locating posts'),
        dict(name='right_switch_EST',size=[6,13,7],center=[16,22,22],color='#b681b9',note='Estimated switch, no locating posts'),
        dict(name='side_pcb_EST',size=[3,27,9],center=[-22.5,40,19],color='#dd8662',note='Estimated two-button PCB and switch envelope'),
        dict(name='battery_EST',size=[24,18,6],center=[2,63,22],color='#729cdf',note='Estimated battery, battery retention and rear cover require redesign'),
        dict(name='battery_connector_EST',size=[8,6,4],center=[14,61,19],color='#99b5e8',note='Estimated plug incl. insertion allowance'),
        dict(name='wiring_channel_EST',size=[4,34,5],center=[-15,43,18],color='#edca6e',note='Estimated wire routing allowance, no strain relief designed'),
        dict(name='usb_c_and_plug_EST',size=[12,16,6],center=[0,5,8],color='#8d9eac',note='Estimated connector and cable insertion; no cutout yet'),
        dict(name='power_switch_EST',size=[8,5,5],center=[10,68,6],color='#8da483',note='Estimated actuator/tool reach'),
        dict(name='antenna_keepout_EST',size=[18,15,12],center=[4,76,16],color='#e36363',note='Provisional copper/metal/battery keepout; RF engineer must replace'),
    ]
    for e in envelopes:e['center'][1]*=-1
    return envelopes

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--params',default=str(ROOT/'cad/parameters.json')); args=parser.parse_args()
    p=json.loads(Path(args.params).read_text(encoding='utf8'))
    (ROOT/'.tools').mkdir(exist_ok=True)
    (ROOT/'reports').mkdir(exist_ok=True)
    start=time.time(); solid,parts,feet=create(p)
    print('Valid',solid.isValid(),'solids',len(solid.Solids()),'volume',solid.Volume(),flush=True)
    out=ROOT/'exports';out.mkdir(exist_ok=True)
    cq.exporters.export(solid,str(out/'quietmirror_fingertip_V0.1.step'))
    # Normalize OCCT tolerances through the saved STEP, then tessellate with
    # an absolute 0.02 mm deflection (not edge-length-relative tolerance).
    solid=cq.importers.importStep(str(out/'quietmirror_fingertip_V0.1.step')).val()
    assert solid.isValid() and len(solid.Solids())==1, 'Invalid or disconnected CAD'
    raw=ROOT/'.tools/raw_export.stl'
    solid.exportStl(str(raw),tolerance=.02,angularTolerance=.15,relative=False,parallel=False)
    mesh=trimesh.load_mesh(raw)
    raw_faces=len(mesh.faces)
    # Weld only numerical duplicates at 0.00001 mm; no holes are patched and
    # no disconnected components discarded. Remove zero-area/duplicate facets.
    mesh.merge_vertices(digits_vertex=5)
    mesh.update_faces(mesh.nondegenerate_faces(height=1e-5))
    mesh.update_faces(mesh.unique_faces());mesh.remove_unreferenced_vertices()
    assert mesh.is_watertight and len(mesh.split(only_watertight=False))==1, 'STL mesh QA failed'
    mesh.export(out/'quietmirror_fingertip_V0.1.stl')
    cq.exporters.export(solid,str(out/'quietmirror_fingertip_V0.1.brep'))
    partdir=ROOT/'.tools/parts';partdir.mkdir(exist_ok=True)
    for name,s in parts.items(): s.copy().exportStl(str(partdir/f'{name}.stl'),tolerance=.04,angularTolerance=.2,relative=False)
    assy=cq.Assembly(solid.copy(),name='V0_1_fixed_print_model',color=cq.Color(.65,.7,.75,.26))
    collisions=[]; envs=envelope_defs(p)
    for env in envs:
        es=cq.Workplane('XY').box(*env['size']).val().translate(env['center'])
        color=env['color']; rgb=[int(color[i:i+2],16)/255 for i in (1,3,5)]
        assy.add(es,name=env['name'],color=cq.Color(*rgb,.42))
        hits=[]
        for name,s in parts.items():
            vol=s.copy().intersect(es.copy()).Volume()
            if vol>.05: hits.append(dict(part=name,overlap_mm3=round(vol,3)))
        collisions.append(dict(envelope=env['name'],hits=hits))
    assy.save(str(out/'electronic_envelopes_ESTIMATES.step'))
    # Exact-geometry bounds, independent of cached tessellation tolerances.
    box=Bnd_Box();BRepBndLib.AddOptimal_s(solid.wrapped,box,False,False)
    xmin,ymin,zmin,xmax,ymax,zmax=box.Get()
    metrics=dict(units='mm',dimensions=[xmax-xmin,ymax-ymin,zmax-zmin],bounds=[[xmin,ymin,zmin],[xmax,ymax,zmax]],volume_mm3=solid.Volume(),cad_valid=solid.isValid(),cad_brepcheck=BRepCheck_Analyzer(solid.wrapped).IsValid(),cad_solids=len(solid.Solids()),mesh_cleanup=dict(raw_faces=raw_faces,final_faces=len(mesh.faces),weld_tolerance_mm=1e-5,holes_patched=0,components_discarded=0),feet=[dict(id=i+1,x=x,y=y,diameter=p['foot_diameter'],bottom_z=0) for i,(x,y) in enumerate(feet)],parameters=p,build_seconds=time.time()-start)
    (ROOT/'reports/cad_metrics.json').write_text(json.dumps(metrics,indent=2,ensure_ascii=False),encoding='utf8')
    (ROOT/'reports/envelope_interferences.json').write_text(json.dumps(dict(envelopes=envs,collisions=collisions),indent=2,ensure_ascii=False),encoding='utf8')
    print(json.dumps({k:v for k,v in metrics.items() if k not in ['parameters','feet']},indent=2),flush=True)

if __name__=='__main__': main()
