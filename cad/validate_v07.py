"""Saved-artifact topology, retained base, assembly and sampled travel tests."""
from pathlib import Path
import json,itertools,math
import numpy as np
import cadquery as cq
import trimesh,pymeshlab
from build_v03 import bounds
from build_v05 import clip_above
from validate_mouse import ray_distances
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'exports/v07';RP=ROOT/'reports/v07'

def overlap(a,b):
    if not a.Solids() or not b.Solids():return 0.
    aa,bb=bounds(a),bounds(b)
    if any(min(aa[i+3],bb[i+3])-max(aa[i],bb[i])<1e-5 for i in range(3)):return 0.
    return a.intersect(b).Volume(tol=1e-7)

def main():
    p=json.loads((ROOT/'cad/parameters_v07.json').read_text(encoding='utf8'))
    metrics=json.loads((RP/'cad_metrics.json').read_text(encoding='utf8'));shapes={};meshes={};rows=[]
    for a in metrics['parts']:
        n=a['name'];s=cq.importers.importStep(str(OUT/'placed'/f'{n}.step')).val();m=trimesh.load_mesh(OUT/'placed'/f'{n}.stl');shapes[n]=s;meshes[n]=m
        ms=pymeshlab.MeshSet();ms.load_new_mesh(str(OUT/'placed'/f'{n}.stl'));ms.compute_selection_by_self_intersections_per_face()
        row=dict(name=n,cad_valid=s.isValid(),solids=len(s.Solids()),watertight=m.is_watertight,winding_consistent=m.is_winding_consistent,components=len(m.split(only_watertight=False)),self_intersecting_faces=ms.current_mesh().selected_face_number(),dimensions_xyz_mm=m.extents.tolist(),volume_mm3=m.volume)
        rows.append(row);print('Mesh',n,row['self_intersecting_faces'],flush=True)
    # Cache a local body for each part's full stroke. This avoids repeatedly
    # intersecting hundreds of distant rear-vent faces with a tiny plunger.
    locals={}
    for n,s in shapes.items():
        if n=='BODY':continue
        bb=bounds(s);size=[bb[i+3]-bb[i]+3 for i in range(3)];center=[(bb[i]+bb[i+3])/2 for i in range(3)]
        region=cq.Workplane('XY').box(*size).val().translate(center)
        locals[n]=shapes['BODY'].intersect(region)
    contacts=[]
    for (an,a),(bn,b) in itertools.combinations(shapes.items(),2):
        v=overlap(locals[bn],b) if an=='BODY' else overlap(a,b)
        if v>.01:contacts.append(dict(a=an,b=bn,overlap_mm3=v,elastic_detent={an,bn}=={'WHEEL','DETENT_LEAF'}))
    print('Static contacts',contacts,flush=True)
    (RP/'static_intersections.json').write_text(json.dumps(contacts,indent=2),encoding='utf8')
    assert not any(not a['elastic_detent'] for a in contacts),'Fix rigid static intersections before sampled travel validation.'
    paths=[]
    for name,module in p['modules'].items():
        names=[name+'_KEY',name+'_RETAINER'] if name!='middle' else ['WHEEL_CARRIER','WHEEL','AXLE','AXLE_WASHER','DETENT_LEAF','middle_RETAINER']
        fixed={n:s for n,s in shapes.items() if n not in names}
        for d in np.linspace(0,p['mechanism']['travel'],9):
            vec=(float(d),0,0) if module.get('side') else (0,0,-float(d))
            hits=[]
            for n in names:
                for fn,fs in fixed.items():
                    v=overlap(shapes[n].translate(vec),locals[n] if fn=='BODY' else fs)
                    if v>.01:hits.append(dict(a=n,b=fn,overlap_mm3=v))
            paths.append(dict(module=name,travel_mm=float(d),hits=hits))
        print('Travel',name,sum(bool(x['hits']) for x in paths if x['module']==name),flush=True)
    rotations=[];wheel=p['wheel'];axis=((0,-wheel['y'],wheel['axis_z']),(1,-wheel['y'],wheel['axis_z']))
    # Continuous conservative rotational envelope: every tooth lies inside
    # this annulus and the round bore is invariant under rotation.
    start=cq.Vector(-wheel['width']/2,-wheel['y'],wheel['axis_z']);ax=cq.Vector(1,0,0)
    bore_diameter=p['mechanism']['wheel_bore_diameter']
    swept=cq.Solid.makeCylinder(wheel['diameter']/2,wheel['width'],start,ax).cut(cq.Solid.makeCylinder(bore_diameter/2,wheel['width'],start,ax))
    envelope_hits=[]
    for n in ('BODY','WHEEL_CARRIER','AXLE','AXLE_WASHER'):
        vol=overlap(swept,locals['WHEEL'] if n=='BODY' else shapes[n])
        if vol>.01:envelope_hits.append(dict(part=n,overlap_mm3=vol))
    for angle in (0,3.75,7.5):
        s=shapes['WHEEL'].rotate(*axis,float(angle));hits=[]
        for n in ('BODY','WHEEL_CARRIER','AXLE','AXLE_WASHER'):
            v=overlap(s,locals['WHEEL'] if n=='BODY' else shapes[n])
            if v>.01:hits.append(dict(part=n,overlap_mm3=v))
        rotations.append(dict(angle_degrees=float(angle),rigid_hits=hits,detent_interference_mm3=overlap(s,shapes['DETENT_LEAF'])))
    # Installation into the one-piece body, with retainers/trays/other keys
    # removed. Hardware is installed afterwards through the open underside.
    insertion=[]
    for n in ('left_KEY','right_KEY','thumb_front_KEY','thumb_rear_KEY','WHEEL_CARRIER'):
        records=[]
        for d in np.linspace(0,30,31):
            vec=(-float(d),0,0) if n.startswith('thumb') else (0,0,float(d))
            s=shapes[n].translate(vec);bb=bounds(s);region=cq.Workplane('XY').box(*[bb[i+3]-bb[i]+.1 for i in range(3)]).val().translate([(bb[i]+bb[i+3])/2 for i in range(3)])
            vol=overlap(shapes['BODY'].intersect(region),s)
            records.append(dict(distance_mm=float(d),overlap_mm3=vol))
        insertion.append(dict(part=n,poses=records,pass_check=all(a['overlap_mm3']<.01 for a in records)))
        print('Insertion',n,insertion[-1]['pass_check'],flush=True)
    hardware=[]
    for mn in p['modules']:
        hs=cq.importers.importStep(str(OUT/'placed'/(mn+'_SWITCH_EXAMPLE.step'))).val();hits=[]
        for n,s in shapes.items():
            vol=overlap(hs,s)
            if vol>.01:hits.append(dict(part=n,overlap_mm3=vol))
        hardware.append(dict(module=mn,rest_intersections=hits))
    old=cq.importers.importStep(str(ROOT/'exports/v06/quietmirror_fingertip_V0.6_SHELL.step')).val().cut(clip_above(5.4))
    new=shapes['BODY'].cut(clip_above(5.4));base_delta=old.cut(new).Volume(tol=1e-7)+new.cut(old).Volume(tol=1e-7)
    feet=[]
    for x,y in [(-21,-8),(21,-8),(-21.5,-61.5),(21.5,-61.5),(0,-81.5)]:
        pts=[(x,y)]+[(x+3.7*math.cos(t),y+3.7*math.sin(t)) for t in np.linspace(0,2*math.pi,8,endpoint=False)]
        hh=ray_distances(meshes['BODY'],[[a,b,-1] for a,b in pts],[[0,0,1]]*9);zz=[h[0]-1 for h in hh if h]
        feet.append(dict(x=x,y=y,samples=len(zz),min_z=min(zz),max_z=max(zz)))
    topo_pass=all(r['cad_valid'] and r['solids']==1 and r['watertight'] and r['winding_consistent'] and r['components']==1 and r['self_intersecting_faces']==0 for r in rows)
    r=dict(version='0.7',units='mm',topology=rows,topology_pass=topo_pass,static_intersections=contacts,sampled_button_paths=paths,wheel_rotations=rotations,wheel_continuous_envelope=dict(outer_diameter_mm=wheel['diameter'],bore_diameter_mm=bore_diameter,width_mm=wheel['width'],rigid_hits=envelope_hits),insertion_paths=insertion,switch_example_rest_fit=hardware,base_symmetric_difference_mm3=base_delta,base_frozen_through_z_mm=5.4,feet=feet,method_limits='No printed prototype, friction, force, durability or elastic FEA test. Tactile compression and optional detent interference are intentional elastic interactions. Nine button poses and 31 insertion positions per key/carrier are sampled, not a continuous proof. Wheel rotation separately uses a conservative continuous annular envelope; three tooth phases quantify the intentional detent contact.')
    r['rigid_motion_pass']=not any(a['hits'] for a in paths) and not any(a['rigid_hits'] for a in rotations) and not envelope_hits
    (RP/'validation.json').write_text(json.dumps(r,indent=2),encoding='utf8')
    print(json.dumps({k:r[k] for k in ('topology_pass','rigid_motion_pass','base_symmetric_difference_mm3','static_intersections')},indent=2),flush=True)
    assert topo_pass and base_delta<.01 and r['rigid_motion_pass'] and all(a['pass_check'] for a in insertion) and all(not a['rest_intersections'] for a in hardware)

if __name__=='__main__':main()
