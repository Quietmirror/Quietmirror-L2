"""Final-artifact static and sampled-motion audit. No physical-fit assertion."""
import json,itertools,math,time,sys
import numpy as np
from common import *
from side_module import KEYS

def motion_pair(a,b,an,bn,minimum=.3,intended=False):
    # Static clearance is measured separately. At each motion pose this
    # check evaluates exact solid intersection only, not minimum distance.
    ba=a.BoundingBox();bb=b.BoundingBox()
    possible=all(getattr(ba,c+'max')>=getattr(bb,c+'min') and getattr(bb,c+'max')>=getattr(ba,c+'min') for c in 'xyz')
    overlap=vol(a.intersect(b)) if possible else 0.
    return dict(a=an,b=bn,gap_mm=None,overlap_mm3=overlap,required_mm=None,intended_contact=intended,pass_check=overlap<=.001,distance_kind='not_measured_during_motion; static clearance reported separately')
def main():
    start=time.time();parts={p.stem:load(p.stem) for p in (OUT/'parts').glob('*.step')}
    resume='--resume' in sys.argv
    body=parts['BODY']
    if resume:
        cached=json.loads((RP/'solids.json').read_text())
        assert len(cached)==8
        for r in cached:
            p=OUT/'parts'/(r['name']+'.step')
            assert r['cad_step_size_mtime']==[p.stat().st_size,p.stat().st_mtime_ns]
        assert all(p.stat().st_mtime_ns <= (RP/'solids.json').stat().st_mtime_ns for p in (OUT/'reference').glob('*.step'))
        assert len(json.loads((RP/'static_pairs.json').read_text()))==28
        print('Resuming only unfinished motion groups; immutable artifact timestamps checked',flush=True)
    if not resume:
        rows=[]
        previous={r['name']:r for r in json.loads((RP/'solids.json').read_text())} if (RP/'solids.json').exists() else {}
        for n,s in parts.items():
            import trimesh
            mesh=trimesh.load_mesh(OUT/'parts'/(n+'.stl'))
            si=None;error=None
            fingerprint=[(OUT/'parts'/(n+'.step')).stat().st_size,(OUT/'parts'/(n+'.step')).stat().st_mtime_ns]
            if previous.get(n,{}).get('cad_step_size_mtime')==fingerprint:
                si=previous[n]['brep_self_interference_check'];error=previous[n]['check_error']
            else:
                try:
                    from OCP.BRepAlgoAPI import BRepAlgoAPI_Check
                    si=bool(BRepAlgoAPI_Check(s.wrapped,True,True).IsValid())
                except Exception as e:error=str(e)
            rows.append(dict(name=n,valid=s.isValid(),solids=len(s.Solids()),volume_mm3=vol(s),bounds_mm=bounds(s),closed_mesh=bool(mesh.is_watertight),consistent_winding=bool(mesh.is_winding_consistent),mesh_components=len(mesh.split(only_watertight=False)),brep_self_interference_check=si,check_error=error))
            rows[-1]['cad_step_size_mtime']=fingerprint
            print('G1',n,si,flush=True)
        save('solids.json',rows)
        static=[]
        for (an,a),(bn,b) in itertools.combinations(parts.items(),2):
            intended=('BODY' in [an,bn] and ('SIDE_' in an or 'SIDE_' in bn)) or set([an,bn])=={'WHEEL','WHEEL_CARRIER'}
            row=pair(a,b,an,bn,.3,intended);static.append(row)
            save('static_pairs.json',static)
            if row['overlap_mm3']>.001:print('COLLISION',an,bn,row['overlap_mm3'],flush=True)
        save('static_pairs.json',static)
        electronics=[]
        for p in (OUT/'reference').glob('*.step'):
            n=p.stem
            if 'F2_TRIAL' in n or n.endswith('_EST') is False and n not in ['SF_D2F_01F','SR_D2F_01F','SIDE_IO_PCB']:continue
            s=load(n,p.parent)
            for an,a in parts.items():
                intended=(an=='SIDE_SWITCH_CARRIER' and n in ['SF_D2F_01F','SR_D2F_01F','SIDE_IO_PCB']) or (an=='WHEEL_CARRIER' and n=='ENCODER_ADAPTER_PCB_EST')
                row=pair(a,s,an,n,.5 if an in ['BODY','SIDE_SWITCH_CARRIER'] else .3,intended)
                electronics.append(row)
            save('component_pairs.json',electronics)
            print('G7',n,flush=True)
        save('component_pairs.json',electronics)
        body=parts['BODY'];feet=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text())['mechanisms']['feet']
        footrows=[]
        for f in feet:
            x,y=f['center'];area=0.;zs=[]
            for face in body.Faces():
                if face.geomType()!='PLANE':continue
                b=face.BoundingBox()
                if b.zlen<1e-5 and abs(b.zmin-5.2)<1e-5 and face.normalAt().z<-.9:
                    hit=face.intersect(cyl(4.01,.2,(x,y,5.1)))
                    if hit.Area()>1e-7:area+=hit.Area();zs.append(b.zmin)
            footrows.append(dict(x=x,y=y,z=zs,contact_area_mm2=area,passed=area>40 and all(abs(z-5.2)<1e-5 for z in zs)))
        save('foot_planes.json',dict(feet=footrows,coplanar=all(r['passed'] for r in footrows),glue_z=5.2,skates_mm=.8,ground_z=4.4))
    motions=json.loads((RP/'motion_samples.json').read_text()) if resume else [];done={r['part'] for r in motions};meta=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text())
    for mo in meta['mechanisms']['motions']:
        if mo['part'] not in ['LEFT_KEY','RIGHT_KEY','WHEEL_CARRIER']:continue
        if mo['part'] in done:continue
        n=mo['part'];origin=mo['origin'];axis=[origin[0]+1,*origin[1:]]
        obstacles={bn:b for bn,b in parts.items() if bn!=n and not(n=='WHEEL_CARRIER' and bn=='WHEEL')}
        samples=[]
        for theta in np.linspace(0,mo['end_deg'],21):
            moved=parts[n].rotate(origin,axis,float(theta))
            samples.append(dict(angle_deg=float(theta),pairs=[motion_pair(moved,b,n,bn,.3,bn=='BODY') for bn,b in obstacles.items()]))
            print('POSE',n,round(theta,3),flush=True)
        motions.append(dict(part=n,samples=samples,domain='21 sampled poses only; not continuous swept-volume proof'))
        save('motion_samples.json',motions);print('G5',n,'done',flush=True)
    for k in KEYS:
        if k['name'] in done:continue
        n=k['name'];origin=(29,k['hinge_y'],0);axis=(29,k['hinge_y'],1)
        obstacles={bn:b for bn,b in parts.items() if bn!=n}
        samples=[]
        for theta in list(np.linspace(0,k['angle'],21))+[k['angle']+math.copysign(.3,k['angle'])]:
            moved=parts[n].rotate(origin,axis,float(theta))
            samples.append(dict(angle_deg=float(theta),beyond_stop=bool(abs(theta)>abs(k['angle'])+1e-8),pairs=[motion_pair(moved,b,n,bn,.3,bn in ['BODY','SIDE_SWITCH_CARRIER']) for bn,b in obstacles.items()]))
            print('POSE',n,round(theta,3),flush=True)
        motions.append(dict(part=n,samples=samples,domain='21 normal poses plus 0.3 degree beyond stop; stop contact explicitly intentional'))
        save('motion_samples.json',motions);print('G5',n,'done',flush=True)
    insertion=[]
    for k in KEYS:
        # Probe from the top opening down to fixed upper bearing. The steel
        # press fit itself is excluded from the line-of-sight test.
        probe=cyl(1.,35-20.8,(29,k['hinge_y'],20.8))
        insertion.append(dict(name=k['short']+'_top_pin_access',probe_diameter_mm=2,overlap_body_mm3=vol(probe.intersect(body))))
    save('assembly_access.json',dict(pin_access=insertion,cap_slanted_insertion='UNVERIFIED: no complete rigid route yet proved',carrier_bottom_insertion='UNVERIFIED: final fasteners/board assembly requires route checking'))
    save('validation_runtime.json',dict(seconds=time.time()-start))
if __name__=='__main__':main()
