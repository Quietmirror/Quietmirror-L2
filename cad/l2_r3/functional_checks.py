"""Housing/encoder motion and simple insertion attempts, with finite scope."""
import json,math
import numpy as np
from common import *
from validate import motion_pair
from side_module import KEYS

def main():
    parts={p.stem:load(p.stem) for p in (OUT/'parts').glob('*.step')}
    meta=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text())
    checks=[]
    for mo in meta['mechanisms']['motions']:
        n=mo['part']
        if n not in ['LEFT_KEY','RIGHT_KEY','WHEEL_CARRIER']:continue
        sw=load(mo['switch'],OUT/'reference');point=mo['actuation_point'];tilt=mo.get('switch_tilt_deg',0)
        axis1=[point[0]+1,*point[1:]]
        flat=sw.rotate(point,axis1,-tilt)
        # The generic rigid body top is 1.03 below the actuator reference;
        # the free plunger protrusion is intentionally excluded.
        housing=flat.intersect(box(-50,50,0,90,0,point[2]-1.03)).rotate(point,axis1,tilt)
        samples=[];ori=mo['origin'];ax=[ori[0]+1,*ori[1:]]
        child_poses={};child_targets={}
        if n=='WHEEL_CARRIER':
            for child in ['WHEEL',*mo['moving_hardware']]:
                source=parts[child] if child in parts else load(child,OUT/'reference')
                poses=[source.rotate(ori,ax,float(v)) for v in np.linspace(0,mo['end_deg'],21)]
                boxes=[v.BoundingBox() for v in poses]
                region=box(min(v.xmin for v in boxes)-.01,max(v.xmax for v in boxes)+.01,min(v.ymin for v in boxes)-.01,max(v.ymax for v in boxes)+.01,min(v.zmin for v in boxes)-.01,max(v.zmax for v in boxes)+.01)
                child_poses[child]=poses
                child_targets[child]={target:parts[target].intersect(region) for target in ['BODY','LEFT_KEY','RIGHT_KEY','SIDE_SWITCH_CARRIER']}
                print('Prepared local exact obstacles',child,flush=True)
        for index,angle in enumerate(np.linspace(0,mo['end_deg'],21)):
            actor=parts[n].rotate(ori,ax,float(angle))
            rows=[motion_pair(actor,housing,n,mo['switch']+'_RIGID_HOUSING')]
            if n=='WHEEL_CARRIER':
                for child in ['WHEEL',*mo['moving_hardware']]:
                    moved=child_poses[child][index]
                    for target,obstacle in child_targets[child].items():
                        if obstacle.Solids():rows.append(motion_pair(moved,obstacle,child,target))
                        else:rows.append(dict(a=child,b=target,overlap_mm3=0.,pass_check=True,distance_kind='AABB union excludes obstacle at all tested poses'))
            samples.append(dict(angle_deg=float(angle),pairs=rows))
            if n=='WHEEL_CARRIER':print('Wheel group pose',index,flush=True)
        checks.append(dict(part=n,samples=samples));print('Functional housing/group',n,flush=True)
    save('functional_motion.json',dict(groups=checks,scope='21 sampled rigid-body poses; flexible wiring, compressed plunger and true hardware tolerances not simulated'))
    carrier=cq.Compound.makeCompound([parts['SIDE_SWITCH_CARRIER'],load('SIDE_IO_PCB',OUT/'reference'),load('SF_D2F_01F',OUT/'reference'),load('SR_D2F_01F',OUT/'reference')])
    route=[]
    for z in np.linspace(-12,0,25):route.append(dict(z_offset_mm=float(z),overlap_mm3=vol(carrier.translate((0,0,float(z))).intersect(parts['BODY']))))
    save('insertion_attempts.json',dict(carrier_straight_up=route,status='Straight route tested only; a collision means this route is unusable, not that every tilted path is impossible',cap_hooked_route='UNVERIFIED; complete hooked/tilted route not proved'))
    force=[]
    for k in KEYS:
        rows=[]
        for y in [k['y0']+1,(k['y0']+k['y1'])/2,k['y1']-1]:
            arm=abs(y-k['hinge_y']);rows.append(dict(y=y,ideal_force_N=None if arm<.1 else .74*abs(k['rod_y']-k['hinge_y'])/arm))
        force.append(dict(part=k['name'],positions=rows))
    save('side_force_estimate.json',dict(switch_max_operating_force_assumption_N=.74,source='https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2f.pdf',model='F_touch = OF * |rod_y-hinge_y| / |touch_y-hinge_y|; no friction, compliance, stop contact or tolerance',results=force,physical_force='UNVERIFIED'))
    dname=json.loads((RP/'assembly_inventory.json').read_text())['D_reference'][0]
    d=load(dname,OUT/'reference')
    save('donor_placeholder_check.json',dict(name=dname,status='FIT_NOT_CERTIFIED',pairs=[motion_pair(d,s,dname,n) for n,s in parts.items()],scope='Placeholder board only; positive intersection applies to this assumed outline/height, not to the unknown real donor PCB'))

if __name__=='__main__':main()
