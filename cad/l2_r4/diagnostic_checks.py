"""Exact checks of the actual candidate; failures are data, never a release pass.

The gate aggregation runs only after any reported exceptions have been resolved.
This intentionally keeps the full-body distances, including functional contacts,
visible rather than silently treating every BODY/lever pair as an exception.
"""
import itertools,json,math,time
import numpy as np
import trimesh
from common import *
from side_module import KEYS,RETAINER_MOUNTS

def main():
    parts={p.stem:load(p.stem) for p in sorted((OUT/'parts').glob('*.step'))}
    body=parts['BODY'];rows=[]
    for n,s in parts.items():
        from OCP.BRepAlgoAPI import BRepAlgoAPI_Check
        m=trimesh.load_mesh(OUT/'parts'/(n+'.stl'))
        rows.append(dict(name=n,valid=s.isValid(),solids=len(s.Solids()),
            volume_mm3=vol(s),bounds_mm=bounds(s),closed_mesh=bool(m.is_watertight),
            consistent_winding=bool(m.is_winding_consistent),mesh_components=len(trimesh.graph.connected_components(m.face_adjacency,nodes=np.arange(len(m.faces)),engine='scipy',min_len=1)),
            brep_self_interference_check=bool(BRepAlgoAPI_Check(s.wrapped,True,True).IsValid())))
        print('SOLID',rows[-1],flush=True);save('solids.json',rows)
    feet=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text())['mechanisms']['feet']
    footrows=[]
    for f in feet:
        x,y=f['center'];area=0.;zs=[]
        for face in body.Faces():
            if face.geomType()!='PLANE':continue
            bb=face.BoundingBox()
            if bb.zlen<1e-5 and abs(bb.zmin-5.2)<1e-5 and face.normalAt().z<-.9:
                hit=face.intersect(cyl(4.01,.2,(x,y,5.1)))
                if hit.Area()>1e-7:area+=hit.Area();zs.append(bb.zmin)
        footrows.append(dict(x=x,y=y,z=zs,contact_area_mm2=area,passed=area>40 and all(abs(z-5.2)<1e-5 for z in zs)))
    save('foot_planes.json',dict(feet=footrows,coplanar=all(r['passed'] for r in footrows),glue_z=5.2,skates_mm=.8,ground_z=4.4))
    static=[]
    for (an,a),(bn,b) in itertools.combinations(parts.items(),2):
        row=pair(a,b,an,bn,.3);static.append(row);save('static_pairs.json',static)
        if not row['pass_check']:print('STATIC_REVIEW',row,flush=True)
    # Side cap assembly uses the final BODY and actual pad/ear/root-bridge.
    insertions=[];motions=[]
    for k in KEYS:
        n=k['name'];cap=parts[n];origin=(29,k['hinge_y'],0);axis=(29,k['hinge_y'],1)
        shim=load(k['short']+'_TUNING_SHIM_0p33',OUT/'reference')
        insertion_actor=cq.Compound.makeCompound([cap,shim])
        bb=insertion_actor.BoundingBox()
        insertion_body=body.intersect(box(bb.xmin-.01,bb.xmax+10.01,bb.ymin-.01,bb.ymax+.01,bb.zmin-.01,bb.zmax+.01))
        poses=[]
        for dx in np.arange(10.,-.001,-.25):
            actor=insertion_actor.translate((float(dx),0,0))
            ov=vol(actor.intersect(insertion_body))
            row=dict(a=n+' + PET',b='BODY',overlap_mm3=ov,gap_mm=None,pass_check=ov<=.001,nearest_points_mm=[],method='Exact BRep common volume; complete actor-path bounding region; no distance claim required for cap G6')
            row['dx_mm']=float(dx);poses.append(row)
            if row['overlap_mm3']>.001:print('INSERT_COLLISION',n,dx,row['overlap_mm3'],row['nearest_points_mm'],flush=True)
        insertions.append(dict(part=n,method='exact rigid -X translation at 0.25 mm intervals',samples=poses,
            passed=all(r['overlap_mm3']<=.001 for r in poses)))
        save('key_insertion_exact.json',insertions)
        samples=[]
        angles=sorted(set([float(a) for a in np.linspace(-k['sign']*.5,k['angle']+k['sign']*.3,27)]+[0.,k['angle']]))
        for a in angles:
            actor=cap.rotate(origin,axis,a)
            row=pair(actor,body,n,'BODY',.3)
            row.update(angle_deg=a,beyond_inward_stop=abs(a)>abs(k['angle']) and a*k['sign']>0,
                outward=a*k['sign']<0)
            # This is deliberately a raw contact-inclusive result. The final
            # classifier must prove that any contact is in the specific stop.
            samples.append(row)
        motions.append(dict(part=n,axis=[origin,axis],samples=samples));save('side_motion_raw.json',motions)
        print('SIDE_RAW',n,[(round(r['angle_deg'],3),round(r['overlap_mm3'],6)) for r in samples],flush=True)
    access=[]
    for k in KEYS:
        probe=cyl(1.,14.2,(29,k['hinge_y'],20.8))
        access.append(pair(probe,body,k['short']+'_PIN_TOOL_D2','BODY',0.))
    for n,m in RETAINER_MOUNTS.items():
        access.append(pair(cyl(2.,12.1,(m['x'],m['y'],0)),body,n+'_SCREWDRIVER_D4','BODY',0.))
    save('assembly_access.json',access)
    # Independent numerical rigid-body calculation, rather than importing
    # rounded angles/travel from the author evidence.
    kin=[]
    for k in KEYS:
        x=k['rod_end']-29;dy=k['rod_y']+k['pad_y_offset']-k['hinge_y'];cover=[]
        for a in np.linspace(0,k['angle'],101):
            t=math.radians(float(a));shift_y=x*math.sin(t)+dy*(math.cos(t)-1)+k['pad_y_offset']
            shift_x=x*(math.cos(t)-1)-dy*math.sin(t)
            # The projected rim ellipse contains a circle of radius r*cos(a).
            margin=1.3*math.cos(t)-1.-abs(shift_y)
            cover.append(dict(angle_deg=float(a),inward_mm=-shift_x,lateral_mm=shift_y,conservative_coverage_margin_mm=margin))
        kin.append(dict(part=k['name'],stop_deg=k['angle'],samples=cover,
            pad_coverage_pass=all(r['conservative_coverage_margin_mm']>=0 for r in cover),
            definition='Projection of pad rim onto button YZ plane; 1.3*cos(theta) inscribed radius; button radius 1.0'))
    save('side_kinematics_independent.json',kin)
    print('PAD_COVERAGE',[(r['part'],r['pad_coverage_pass'],min(s['conservative_coverage_margin_mm'] for s in r['samples'])) for r in kin],flush=True)
    save('candidate_diagnostics_status.json',dict(status='REVIEW_REQUIRED',
        note='These measurements are evidence; no CAD-complete claim or release authorization is derived from a successful script exit.'))

if __name__=='__main__':main()
