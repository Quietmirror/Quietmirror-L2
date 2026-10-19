"""All23 wheel-click poses for only the changed conceptual PCB.

This diagnosis is additional to the final complete wheel-group verification.
"""
import json
import numpy as np
from common import *
from bounded_scene import scene_pairs
from contact_audit import rigid_housing

def main():
    inv=json.loads((RP/'assembly_inventory.json').read_text());meta=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text())
    mo=next(m for m in meta['mechanisms']['motions'] if m['part']=='WHEEL_CARRIER')
    group=[mo['part'],*mo.get('moving_children',[]),*mo.get('moving_hardware',[])]
    parts={n:load(n) for n in inv['printable']};hw={n:load(n,OUT/'reference') for n in inv['H_hardware']}
    fixed={n:s for n,s in {**parts,**hw}.items() if n not in group and n!=mo['switch']}
    fixed[mo['switch']+'_RIGID_HOUSING']=rigid_housing(hw[mo['switch']],mo)
    ori=mo['origin'];axis=[ori[0]+1,*ori[1:]];pcb=hw['ENCODER_ADAPTER_PCB_EST'];rows=[]
    for angle in np.linspace(-4.4,4.4,23):
        r=scene_pairs(pcb.rotate(ori,axis,float(angle)),fixed,'ENCODER_ADAPTER_PCB_EST',.3)
        rows.append(dict(angle_deg=float(angle),**r));print('PCB_POSE',angle,r['exact_global_minimum_mm'],r['passed'],flush=True)
    save('encoder_pcb_23_pose_probe.json',dict(samples=rows,passed=all(r['passed'] for r in rows),scope='Changed PCB diagnosis only; full-group acceptance is separate.'))

if __name__=='__main__':main()
