"""Remove the measured inherited rib/plunger overlap without changing key outline."""
import json,math
import numpy as np
from common import *
from exact_distance import pair

def main():
    meta=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text());rows=[]
    for mo in meta['mechanisms']['motions']:
        name=mo['part']
        if name not in ['LEFT_KEY','RIGHT_KEY']:continue
        old=load(name,ROOT/'models/L2_r3/parts');point=np.array(mo['actuation_point']);tilt=mo['switch_tilt_deg']
        normal=np.array([0.,-math.sin(math.radians(tilt)),math.cos(math.radians(tilt))])
        center=point-1.13*normal
        clearance=cq.Solid.makeSphere(1.13,V(*center),angleDegrees1=-90,angleDegrees2=90)
        result=old.cut(clearance).clean()
        switch=load(mo['switch'],OUT/'reference');ax1=[point[0]+1,*point[1:]]
        rigid=switch.rotate(point.tolist(),ax1,-tilt).intersect(box(-50,50,0,90,0,point[2]-1.03));bb=rigid.BoundingBox()
        expanded=box(bb.xmin-.3,bb.xmax+.3,bb.ymin-.3,bb.ymax+.3,bb.zmin-.3,bb.zmax+.3).rotate(point.tolist(),ax1,tilt)
        ori=mo['origin'];axis=[ori[0]+1,*ori[1:]]
        for angle in np.linspace(-.5,3.1,25):result=result.cut(expanded.rotate(ori,axis,-float(angle))).clean()
        row=export(result,name);row.update(original_volume_mm3=vol(old),removed_volume_mm3=vol(old)-vol(result),
            correction='R1.13 clearance around inherited R1.10 spherical plunger; 0.30 mm rigid housing relief across -0.5..3.1 degrees. Original external key surface and footprint retained.',
            unpressed_switch_check=pair(result,switch,name,mo['switch'],0.))
        rows.append(row)
    save('main_key_local_relief.json',rows)

if __name__=='__main__':main()
