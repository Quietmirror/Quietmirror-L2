"""Development checks of hidden D7 features; not a substitute for final G5."""
import json
import numpy as np
from common import *
from exact_distance import pair
from side_module import KEYS,UPPER_LUG_TOP

def main():
    body=load('BODY');rows=[]
    for k in KEYS:
        cap=load(k['name']);shim=load(k['short']+'_TUNING_SHIM_0p33',OUT/'reference')
        actor=cq.Compound.makeCompound([cap,shim]);bb=actor.BoundingBox()
        # The full straight translated actor is inside this region. Therefore
        # every possible intersection with BODY is retained.
        region=box(bb.xmin-.01,bb.xmax+10.01,bb.ymin-.01,bb.ymax+.01,bb.zmin-.01,bb.zmax+.01)
        local=body.intersect(region)
        insert=[dict(dx_mm=float(dx),overlap_mm3=vol(actor.translate((float(dx),0,0)).intersect(local))) for dx in np.arange(10.,-.001,-.25)]
        ori=(k['hinge_x'],k['hinge_y'],0);axis=(k['hinge_x'],k['hinge_y'],1)
        motion=[]
        for a in [0.,k['angle']*.5,k['angle'],-k['sign']*.5,k['angle']+k['sign']*.3]:
            moved=actor.rotate(ori,axis,a)
            raw=pair(moved,body,k['name']+'+PET','BODY',0.)
            common=moved.intersect(body) if raw['overlap_mm3']>.001 else cq.Compound.makeCompound([])
            motion.append(dict(angle_deg=a,body=raw,intersection_regions=[dict(volume_mm3=vol(s),bounds_mm=bounds(s)) for s in common.Solids()]))
        access=pair(cyl(1.,14.2,(k['hinge_x'],k['hinge_y'],UPPER_LUG_TOP)),body,k['short']+'_PIN_TOOL','BODY',0.)
        r=dict(part=k['name'],axis=[ori,axis],insertion=insert,insertion_pass=max(x['overlap_mm3'] for x in insert)<=.001,motion=motion,pin_access=access,
               scope='Five development motion poses only. Full final G5/functional-clearance/assembly/FEM checks remain mandatory.')
        rows.append(r);save('D7_development_checks.json',rows)
        print(k['short'],'insertion',r['insertion_pass'],'motion',[(x['angle_deg'],x['body']['overlap_mm3']) for x in motion],flush=True)

if __name__=='__main__':main()
