"""Exact local mother-profile containment of D7 bearings and hidden ears."""
import json
from common import *
from surfaces import make_surfaces
from side_module import KEYS,EAR_RADIUS,UPPER_LUG_TOP

def main():
    cfg=json.loads((ROOT/'cad/rebuild_r2/parameters.json').read_text());outer,_,_=make_surfaces(cfg)
    body=load('BODY');rows=[]
    for k in KEYS:
        y=k['hinge_y'];hx=k.get('hinge_x',29.);cap=load(k['name']);pin=load(k['short']+'_VERTICAL_PIN',OUT/'reference')
        region=box(hx-3,hx+3,y-1.5,y+1.5,14.2,20.8)
        fixed=body.intersect(region);outside=fixed.cut(outer);ear=cap.intersect(box(hx-EAR_RADIUS,hx,y-.4,y+.4,18.6,19.5))
        sampled=[]
        for z in [19.8,20.,20.25,20.6,20.8]:
            hit=outer.intersect(cq.Edge.makeLine(V(0,y,z),V(40,y,z)))
            xmax=max([max(e.startPoint().x,e.endPoint().x) for e in hit.Edges()])
            sampled.append(dict(z=z,outer_x=xmax,axis_to_outer_wall_mm=xmax-hx,fixed_bore_wall_mm=xmax-hx-.475))
        rows.append(dict(part=k['name'],fixed_bearing_region_outside_mother_mm3=vol(outside),outside_regions=[bounds(s) for s in outside.Solids()],
                         moving_inboard_ear_outside_mother_mm3=vol(ear.cut(outer)),pin_outside_mother_mm3=vol(pin.cut(outer)),upper_profile_samples=sampled,
                         passed=max(vol(outside),vol(ear.cut(outer)),vol(pin.cut(outer)))<=.001,evidence='Exact current final BODY and original mother surface; cap exterior offset is intentionally excluded from hidden-feature containment.'))
    save('D7_exterior_containment.json',rows);print(json.dumps(rows,indent=2),flush=True)

if __name__=='__main__':main()
