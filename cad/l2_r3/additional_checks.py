"""Local wall samples, pin paths and shim-to-housing travel interference."""
import json,math
import numpy as np
from common import *
from side_module import KEYS
def line_segments(shape,p,q):
    hit=shape.intersect(cq.Edge.makeLine(V(*p),V(*q)))
    return [dict(length_mm=e.Length(),a=e.startPoint().toTuple(),b=e.endPoint().toTuple()) for e in hit.Edges()]
def main():
    body=load('BODY');walls=[]
    access=[]
    for k in KEYS:
        probe=cyl(1,14.2,(29,k['hinge_y'],20.8));hit=body.intersect(probe)
        access.append(dict(key=k['short'],overlap_mm3=vol(hit),overlap_regions=[bounds(s) for s in hit.Solids()]))
    save('pin_access_precheck.json',access);print('Pin access',access,flush=True)
    for n,ys in [('LEFT_KEY',[16,20,28,34]),('RIGHT_KEY',[16,20,28,34])]:
        sign=1 if n=='LEFT_KEY' else -1
        for y in ys:walls.append(dict(part=n,location=[18.3*sign,y],direction='Z',segments=line_segments(load(n),(18.3*sign,y,9),(18.3*sign,y,35))))
    for k in KEYS:
        for y in [k['y0']+3,k['y1']-3]:walls.append(dict(part=k['name'],location=[y,17.5],direction='X',segments=line_segments(load(k['name']),(23,y,17.5),(36,y,17.5))))
    for y in [45,50,60,70]:walls.append(dict(part='BODY',location=[30,y],direction='Z_rim',segments=line_segments(body,(30,y,19.6),(30,y,22))))
    save('wall_samples.json',dict(samples=walls,scope='Finite straight-ray sections; not a global minimum-thickness proof',specified=[dict(feature='side hinge barrel wall',mm=.8),dict(feature='carrier floor',mm=1.6),dict(feature='main ribs',mm=.9),dict(feature='side cap X thickness',mm=1.2)],global_minimum='UNVERIFIED'))
    o3=vol(body.intersect(cyl(1.175,82,(-41,50,19),(1,0,0))))
    save('openings_check.json',dict(O3_body_intersection_mm3=o3,O3_body_pass=o3<=.001,old_side_seats='Omitted at source; no full reverse-equivalence proof against absent author reconstruction',old_M2_tool_paths='Omitted with old side loop',PH1_PH2='Old capture-pin bores omitted',six_windows='Original source polygon coordinates retained; r3 B9 side-band keep-mask intentionally updated',roof_boundary_exact_equivalence='UNVERIFIED'))
    checks=[]
    for k,x0,y0 in [(KEYS[0],18.5,41.85),(KEYS[1],19,56.05)]:
        cap=load(k['name']);shim=load(k['short']+'_TUNING_SHIM_0p33',OUT/'reference')
        case=box(x0,x0+6.5,y0,y0+12.8,13.7,19.5)
        samples=[]
        for a in np.linspace(0,k['angle'],21):
            axis0=(29,k['hinge_y'],0);axis1=(29,k['hinge_y'],1)
            c=cap.rotate(axis0,axis1,float(a));s=shim.rotate(axis0,axis1,float(a))
            samples.append(dict(angle_deg=float(a),key_housing_intersection_mm3=vol(c.intersect(case)),shim_housing_intersection_mm3=vol(s.intersect(case))))
        checks.append(dict(part=k['name'],samples=samples,shim_mm=.33,limits='Housing rectangular envelope; plunger compression and compliant adhesive excluded; physical FP/OP/TTP unknown'))
    save('side_actuation_housing_check.json',checks)
    print('Additional section and actuation checks done',flush=True)
if __name__=='__main__':main()
