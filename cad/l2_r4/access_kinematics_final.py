"""Exact checks of the actual candidate; failures are data, never a release pass.

The gate aggregation runs only after any reported exceptions have been resolved.
This intentionally keeps the full-body distances, including functional contacts,
visible rather than silently treating every BODY/lever pair as an exception.
"""
import itertools,json,math,time
import numpy as np
import trimesh
from common import *
from exact_distance import pair
from side_module import KEYS,RETAINER_MOUNTS,UPPER_LUG_TOP

def main():
    body=load('BODY')
    access=[]
    for k in KEYS:
        probe=cyl(1.,14.2,(k['hinge_x'],k['hinge_y'],UPPER_LUG_TOP))
        access.append(pair(probe,body,k['short']+'_PIN_TOOL_D2','BODY',0.))
    for n,m in RETAINER_MOUNTS.items():
        access.append(pair(cyl(2.,12.1,(m['x'],m['y'],0)),body,n+'_SCREWDRIVER_D4','BODY',0.))
    save('assembly_access.json',access)
    # Independent numerical rigid-body calculation, rather than importing
    # rounded angles/travel from the author evidence.
    kin=[]
    for k in KEYS:
        x=k['rod_end']-k['hinge_x'];dy=k['rod_y']+k['pad_y_offset']-k['hinge_y'];cover=[]
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

if __name__=='__main__':main()
