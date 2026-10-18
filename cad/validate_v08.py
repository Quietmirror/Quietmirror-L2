"""Saved-artifact topology, retained base, assembly and sampled travel tests."""
from pathlib import Path
import json,itertools,math
import numpy as np
from concurrent.futures import ProcessPoolExecutor
import cadquery as cq
import trimesh,pymeshlab
from build_v03 import bounds
from build_v05 import clip_above
from validate_mouse import ray_distances
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'exports/v08';RP=ROOT/'reports/v08'
CACHE=ROOT/'.tools/v08_validation_cache'

def overlap(a,b):
    if not a.Solids() or not b.Solids():return 0.
    aa,bb=bounds(a),bounds(b)
    if any(min(aa[i+3],bb[i+3])-max(aa[i],bb[i])<1e-5 for i in range(3)):return 0.
    return a.intersect(b).Volume(tol=1e-7)

def travel_check(job):
    name,module,partnames,travel,empty=job
    moving=[name+'_KEY',name+'_RETAINER'] if name!='middle' else ['WHEEL_CARRIER','WHEEL','AXLE','AXLE_WASHER','DETENT_LEAF','middle_RETAINER']
    shapes={n:cq.importers.importStep(str(OUT/'placed'/f'{n}.step')).val() for n in partnames if n!='BODY'}
    local={n:(cq.Compound.makeCompound([]) if n in empty else cq.importers.importStep(str(CACHE/(n+'.step'))).val()) for n in moving}
    rows=[]
    for d in np.linspace(0,travel,9):
        vec=(float(d),0,0) if module.get('side') else (0,0,-float(d));hits=[]
        for n in moving:
            moved=shapes[n].translate(vec)
            for fn in partnames:
                if fn in moving:continue
                vol=overlap(moved,local[n] if fn=='BODY' else shapes[fn])
                if vol>.01:hits.append(dict(a=n,b=fn,overlap_mm3=vol))
        rows.append(dict(module=name,travel_mm=float(d),hits=hits))
    return rows

def insertion_check(job):
    n,earlier=job
    wn=('WHEEL_CARRIER','WHEEL','AXLE','AXLE_WASHER','DETENT_LEAF')
    needed=set(wn) | set(earlier) | {n,'BODY'}
    shapes={q:cq.importers.importStep(str(OUT/'placed'/f'{q}.step')).val() for q in needed}
    wheel=cq.Compound.makeCompound([shapes[q] for q in wn])
    target=wheel if n=='WHEEL_CARRIER' else shapes[n]
    installed=[wheel if q=='WHEEL_CARRIER' else shapes[q] for q in earlier]
    rows=[]
    for d in np.linspace(0,30,31):
        vec=(-float(d),0,0) if n.startswith('thumb') else (0,0,float(d))
        s=target.translate(vec);bb=bounds(s)
        region=cq.Workplane('XY').box(*[bb[i+3]-bb[i]+.1 for i in range(3)]).val().translate([(bb[i]+bb[i+3])/2 for i in range(3)])
        vol=overlap(shapes['BODY'].intersect(region),s)+sum(overlap(s,a) for a in installed)
        rows.append(dict(distance_mm=float(d),overlap_mm3=vol))
    return dict(part=n,poses=rows,pass_check=all(a['overlap_mm3']<.01 for a in rows))

def main():
    p=json.loads((ROOT/'cad/parameters_v08.json').read_text(encoding='utf8'))
    metrics=json.loads((RP/'cad_metrics.json').read_text(encoding='utf8'));shapes={};meshes={};rows=[]
    for a in metrics['parts']:
        n=a['name'];s=cq.importers.importStep(str(OUT/'placed'/f'{n}.step')).val();m=trimesh.load_mesh(OUT/'placed'/f'{n}.stl');shapes[n]=s;meshes[n]=m
        ms=pymeshlab.MeshSet();ms.load_new_mesh(str(OUT/'placed'/f'{n}.stl'));ms.compute_selection_by_self_intersections_per_face()
        row=dict(name=n,cad_valid=s.isValid(),solids=len(s.Solids()),watertight=m.is_watertight,winding_consistent=m.is_winding_consistent,components=len(m.split(only_watertight=False)),self_intersecting_faces=ms.current_mesh().selected_face_number(),dimensions_xyz_mm=m.extents.tolist(),volume_mm3=m.volume)
        rows.append(row);print('Mesh',n,row['self_intersecting_faces'],flush=True)
    # Cache a local body for each part's full stroke. This avoids repeatedly
    # intersecting hundreds of distant rear-vent faces with a tiny plunger.
    locals={}
    CACHE.mkdir(parents=True,exist_ok=True)
    for n,s in shapes.items():
        if n=='BODY':continue
        bb=bounds(s);size=[bb[i+3]-bb[i]+3 for i in range(3)];center=[(bb[i]+bb[i+3])/2 for i in range(3)]
        region=cq.Workplane('XY').box(*size).val().translate(center)
        locals[n]=shapes['BODY'].intersect(region)
        if locals[n].Solids():cq.exporters.export(locals[n],str(CACHE/(n+'.step')))
    contacts=[]
    for (an,a),(bn,b) in itertools.combinations(shapes.items(),2):
        v=overlap(locals[bn],b) if an=='BODY' else overlap(a,b)
        if v>.01:contacts.append(dict(a=an,b=bn,overlap_mm3=v,elastic_detent={an,bn}=={'WHEEL','DETENT_LEAF'}))
    print('Static contacts',contacts,flush=True)
    (RP/'static_intersections.json').write_text(json.dumps(contacts,indent=2),encoding='utf8')
    assert not contacts,'Fix every static intersection; V0.8 leaf starts clear of the wheel.'
    paths=[]
    empty=[n for n,s in locals.items() if not s.Solids()]
    jobs=[(name,module,list(shapes),p['mechanism']['travel'],empty) for name,module in p['modules'].items()]
    with ProcessPoolExecutor(max_workers=4) as pool:
        for result in pool.map(travel_check,jobs):
            paths.extend(result)
            print('Travel',result[0]['module'],sum(bool(x['hits']) for x in result),flush=True)
    rotations=[];wheel=p['wheel'];axis=((0,-wheel['y'],wheel['axis_z']),(1,-wheel['y'],wheel['axis_z']))
    # Continuous conservative rotational envelope: every tooth lies inside
    # this annulus and the round bore is invariant under rotation.
    start=cq.Vector(-wheel['width']/2,-wheel['y'],wheel['axis_z']);ax=cq.Vector(1,0,0)
    bore_diameter=p['mechanism']['wheel_bore_diameter']
    swept=cq.Solid.makeCylinder(wheel['diameter']/2,wheel['width'],start,ax).cut(cq.Solid.makeCylinder(bore_diameter/2,wheel['width'],start,ax))
    envelope_hits=[]
    for n in ('BODY','WHEEL_CARRIER','AXLE','AXLE_WASHER','DETENT_LEAF'):
        vol=overlap(swept,locals['WHEEL'] if n=='BODY' else shapes[n])
        if vol>.01:envelope_hits.append(dict(part=n,overlap_mm3=vol))
    for angle in (0,3.75,7.5):
        s=shapes['WHEEL'].rotate(*axis,float(angle));hits=[]
        for n in ('BODY','WHEEL_CARRIER','AXLE','AXLE_WASHER','DETENT_LEAF'):
            v=overlap(s,locals['WHEEL'] if n=='BODY' else shapes[n])
            if v>.01:hits.append(dict(part=n,overlap_mm3=v))
        rotations.append(dict(angle_degrees=float(angle),rigid_hits=hits,detent_interference_mm3=overlap(s,shapes['DETENT_LEAF'])))
    # Ordered installation into the one-piece body. Each path includes the
    # previously installed groups; retainers/trays are installed afterwards.
    insertion=[]
    order=('WHEEL_CARRIER','left_KEY','right_KEY','thumb_front_KEY','thumb_rear_KEY')
    with ProcessPoolExecutor(max_workers=4) as pool:
        for result in pool.map(insertion_check,[(n,order[:i]) for i,n in enumerate(order)]):
            insertion.append(result);print('Insertion',result['part'],result['pass_check'],flush=True)
    hardware=[]
    for mn in p['modules']:
        hs=cq.importers.importStep(str(OUT/'placed'/(mn+'_SWITCH_EXAMPLE.step'))).val();hits=[]
        for n,s in shapes.items():
            vol=overlap(hs,s)
            if vol>.01:hits.append(dict(part=n,overlap_mm3=vol))
        hardware.append(dict(module=mn,rest_intersections=hits))
    old=cq.importers.importStep(str(ROOT/'exports/v07/placed/BODY.step')).val().cut(clip_above(5.4))
    new=shapes['BODY'].cut(clip_above(5.4));base_delta=old.cut(new).Volume(tol=1e-7)+new.cut(old).Volume(tol=1e-7)
    protected=[]
    for x,y in [(-21,-8),(21,-8),(-21.5,-61.5),(21.5,-61.5),(0,-81.5)]:
        region=cq.Solid.makeCylinder(4.4,2.4,cq.Vector(x,y,0))
        a=old.intersect(region);b=new.intersect(region)
        protected.append(dict(name=f'foot_{x}_{y}',difference_mm3=a.cut(b).Volume(tol=1e-7)+b.cut(a).Volume(tol=1e-7)))
    for name,w,l,y in [('sensor',22,26,-48),('power_switch',12,8,-72)]:
        region=cq.Workplane('XY').box(w,l,5.4).val().translate((0,y,2.7));a=old.intersect(region);b=new.intersect(region)
        protected.append(dict(name=name,difference_mm3=a.cut(b).Volume(tol=1e-7)+b.cut(a).Volume(tol=1e-7)))
    front_clearances=[]
    for kn in ('left_KEY','right_KEY'):
        region=cq.Workplane('XY').box(80,20,60).val().translate((0,8,25))
        tip=shapes[kn].intersect(region)
        clearance=tip.translate((0,0,-p['mechanism']['travel'])).distance(shapes['BODY'])
        front_clearances.append(dict(part=kn,full_press_tip_to_body_mm=clearance,tip_region='D <= 2 mm'))
    main_end=max(-bounds(shapes[n])[1] for n in ('left_KEY','right_KEY','left_RETAINER','right_RETAINER'))
    side_start=min(-bounds(shapes[n])[4] for n in ('thumb_front_KEY','thumb_front_RETAINER'))
    side_main_y_gap=side_start-main_end
    # The actual requirement is separated swept intervals, not an arbitrary
    # 1 mm spacing. Require at least the sum of two 0.3 mm design clearances.
    required_y_gap=2*p['mechanism']['radial_clearance']
    feet=[]
    for x,y in [(-21,-8),(21,-8),(-21.5,-61.5),(21.5,-61.5),(0,-81.5)]:
        pts=[(x,y)]+[(x+3.7*math.cos(t),y+3.7*math.sin(t)) for t in np.linspace(0,2*math.pi,8,endpoint=False)]
        hh=ray_distances(meshes['BODY'],[[a,b,-1] for a,b in pts],[[0,0,1]]*9);zz=[h[0]-1 for h in hh if h]
        feet.append(dict(x=x,y=y,samples=len(zz),min_z=min(zz),max_z=max(zz)))
    topo_pass=all(r['cad_valid'] and r['solids']==1 and r['watertight'] and r['winding_consistent'] and r['components']==1 and r['self_intersecting_faces']==0 for r in rows)
    r=dict(version='0.8',units='mm',topology=rows,topology_pass=topo_pass,static_intersections=contacts,sampled_button_paths=paths,wheel_rotations=rotations,wheel_continuous_envelope=dict(outer_diameter_mm=wheel['diameter'],bore_diameter_mm=bore_diameter,width_mm=wheel['width'],rigid_hits=envelope_hits),insertion_paths=insertion,insertion_order='Preassemble wheel group, insert first; then left, right, front thumb, rear thumb. Install retainers and switch trays afterwards.',switch_example_rest_fit=hardware,base_symmetric_difference_mm3=base_delta,base_change_authorized=True,protected_lower_interfaces=protected,front_key_clearance=front_clearances,main_to_front_side_longitudinal_gap_mm=side_main_y_gap,feet=feet,method_limits='No physical print, friction/force, fatigue or elastic FEA. Button paths and insertion are sampled. The 0.4 mm plastic stroke is not the switch rated travel. Detent starts with 0.05 mm nominal gap; engagement requires physical adjustment. Main and thumb moving groups have separated Y intervals, unchanged by their Z/X strokes.')
    r['rigid_motion_pass']=not any(a['hits'] for a in paths) and not any(a['rigid_hits'] for a in rotations) and not envelope_hits
    (RP/'validation.json').write_text(json.dumps(r,indent=2),encoding='utf8')
    print(json.dumps({k:r[k] for k in ('topology_pass','rigid_motion_pass','base_symmetric_difference_mm3','static_intersections')},indent=2),flush=True)
    assert topo_pass and r['rigid_motion_pass'] and all(a['pass_check'] for a in insertion) and all(not a['rest_intersections'] for a in hardware)
    assert all(a['difference_mm3']<.001 for a in protected),protected
    assert all(a['full_press_tip_to_body_mm']>.25 for a in front_clearances)
    assert side_main_y_gap>required_y_gap,(side_main_y_gap,required_y_gap)
    assert all(a['samples']==9 and abs(a['min_z'])<.001 and abs(a['max_z'])<.001 for a in feet)

if __name__=='__main__':main()
