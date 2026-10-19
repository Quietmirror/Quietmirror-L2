"""Actual inherited main-key and complete wheel-group motion, exact distances."""
import json
import numpy as np
from common import *

def main():
    inv=json.loads((RP/'assembly_inventory.json').read_text());meta=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text())
    parts={n:load(n) for n in inv['printable']};hw={n:load(n,OUT/'reference') for n in inv['H_hardware']}
    rows=[]
    for mo in meta['mechanisms']['motions']:
        n=mo['part']
        if n not in ['LEFT_KEY','RIGHT_KEY','WHEEL_CARRIER']:continue
        group=[n,*mo.get('moving_children',[]),*mo.get('moving_hardware',[])]
        actors={g:parts[g] if g in parts else hw[g] for g in group}
        fixed={bn:b for bn,b in parts.items() if bn not in group}
        # Strip the compressible plunger only; the fixed rigid housing remains
        # an obstacle at every pose. Original switch-body frame is retained.
        pt=mo['actuation_point'];ax1=[pt[0]+1,*pt[1:]];tilt=mo.get('switch_tilt_deg',0)
        housing=hw[mo['switch']].rotate(pt,ax1,-tilt).intersect(box(-50,50,0,90,0,pt[2]-1.03)).rotate(pt,ax1,tilt)
        fixed[mo['switch']+'_RIGID_HOUSING']=housing
        ori=mo['origin'];axis=[ori[0]+1,*ori[1:]];angles=np.linspace(-4.4,4.4,23) if n=='WHEEL_CARRIER' else np.linspace(-.5,3.1,25)
        samples=[]
        for a in angles:
            pairs=[]
            for an,actor in actors.items():
                moved=actor.rotate(ori,axis,float(a))
                for bn,b in fixed.items():pairs.append(pair(moved,b,an,bn,.3))
            samples.append(dict(angle_deg=float(a),pairs=pairs))
            print('G5_RAW',n,round(float(a),4),'overlaps',[(r['a'],r['b'],round(r['overlap_mm3'],5)) for r in pairs if r['overlap_mm3']>.001],flush=True)
        rows.append(dict(group=n,members=group,origin_mm=ori,axis=axis,samples=samples,
                         scope='Exact at listed poses; rigid housing and complete wheel children. Functional stops and journals still require local contact classification.'))
        save('main_and_wheel_motion_raw.json',rows)

if __name__=='__main__':main()
