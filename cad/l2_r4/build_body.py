"""Rebuild r4 from the original mother surfaces and source feature sequence.

Omit obsolete seats at source, preserve six roof windows and the five foot
datums, then add the r3 bearing/rim features before final interface bores.
"""
import sys,importlib.util,json,time
from common import *
sys.path.insert(0,str(HERE))
from surfaces import make_surfaces
from mechanics import build_mechanics,beam
from interfaces import build_interfaces
from side_module import fixed_features,integrated_frame,KEYS
spec=importlib.util.spec_from_file_location('original_export',ROOT/'cad/rebuild_r2/build.py')
original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)

def main():
    start=time.time();p=json.loads((ROOT/'cad/rebuild_r2/parameters.json').read_text())
    meta=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text())
    outer,inner,_=make_surfaces(p);print('Mother surfaces',time.time()-start,flush=True)
    m=build_mechanics(p,outer,inner);it=build_interfaces(p,outer,m['parts'])
    body=outer.cut(inner).clean()
    for sign in (-1,1):body=body.cut(box(sign*40.8-12.5,sign*40.8+12.5,0,25,7.5,57.5)).clean()
    for i,c in enumerate(m['body_cuts']+it['body_cuts']):
        body=body.cut(c).clean();assert body.isValid(),('cut',i)
    # Keep the original six polygon boundaries. Only the side-band preserve
    # mask changes where the brief explicitly requires room for the new keys.
    windows=[]
    for n,pts,tool in original.window_layout(p):
        if n.endswith('_L'):
            tool=original.window(pts,10.5*p['host']['scale']).cut(box(-38,-24,40,73,10.9,21))
        body=body.cut(tool).clean();assert body.isValid(),n
        windows.append(dict(name=n,xy=pts))
    print('Skin and six windows',time.time()-start,flush=True)
    for i,a in enumerate(m['body_additions']+it['body_additions']):
        body=body.fuse(a,tol=1e-5).clean();assert body.isValid(),('support',i)
        if i%8==0:print('Support',i,time.time()-start,flush=True)
    for c in it['final_cuts']+m['terminal_cuts']:body=body.cut(c,tol=1e-5).clean()
    body=body.mirror('YZ')
    additions,cuts,lands=fixed_features(outer)
    o3_tool=cyl(1.175,82,(-41,50,19),(1,0,0))
    for a in additions:
        a=a.cut(o3_tool)
        body=body.fuse(a,tol=1e-5).clean()
    for c in cuts:body=body.cut(c,tol=1e-5).clean()
    for a in lands:body=body.fuse(a,tol=1e-5).clean()
    # D1 and D4-D6 are features in the source reconstruction sequence. No
    # finished r3 BODY is imported or patched to produce this body.
    for name,a in [('integrated_side_frame',integrated_frame(outer)),
                   ('lower_tie_Y56',cyl(1,80,(-40,56,8.6),(1,0,0)).intersect(outer)),
                   ('bearing_strut_plus',cyl(1.2,4.6,(9.9,40.8,7.4))),
                   ('bearing_strut_minus',cyl(1.2,4.6,(-9.9,40.8,7.4))),
                   ('upper_tie_Y67p5',cyl(1.5,80,(-40,67.5,23),(1,0,0)).intersect(outer))]:
        body=body.fuse(a,tol=1e-5).clean();assert body.isValid(),name
    # Two small upward service reliefs expose the specified vertical pins.
    # Starts at the upper lug top: press-fit bores and lug wall are retained.
    # This changes the local window/rim edge and is reported as a deviation
    # from literal unchanged six-window boundaries, necessary for B7 access.
    for y in (45.3,69.7):body=body.cut(cyl(1.05,15,(29,y,20.8))).clean()
    # Inboard faces of the original main-key fixed bearings: retain their
    # axes/bores, reduce axial width from 2.4 to 2.2 for wheel-carrier clearance.
    for sign in (-1,1):
        xa,xb=sorted([sign*8.65,sign*8.9])
        body=body.cut(box(xa,xb,31,42,10,26)).clean()
    # Local relief of the fixed wheel-bearing front noses. Bore/axis retained;
    # front bearing wall still >=1.325 mm. The original 0.066-mm running gap
    # at Y47.15 is insufficient for the specified FDM clearance.
    for sign in (-1,1):
        xa,xb=sorted([sign*3.4,sign*6.2])
        body=body.cut(box(xa,xb,46,47.5,15,23)).clean()
    # The new top rim must not close the inherited transverse O3 wheel-pin
    # access path, including the small arc above the side aperture.
    # O3 was cut in each new rim feature before joining it to the body.
    # R3 stop corrections and enlarged charging board interface are retained.
    for mo in meta['mechanisms']['motions']:
        if mo['part'] not in ('LEFT_KEY','RIGHT_KEY','WHEEL_CARRIER'):continue
        actor=baseline(mo['part']);ori=mo['origin'];axis=[ori[0]+1,*ori[1:]]
        moved=actor.rotate(ori,axis,mo['end_deg'])
        if mo['part']=='WHEEL_CARRIER':cut=moved.translate((0,0,-.03)).intersect(box(-5.35,-3.35,39,44,10,18))
        else:
            x=mo['actuation_point'][0]/18.3*23
            cut=moved.translate((0,0,-.04)).intersect(box(x-3.5,x+3.5,6,17,7,14))
        body=body.cut(cut).clean()
    for x in (-7.8,7.8):
        body=unite(body,cyl(2.8,2.4,(x,13,5.6)),beam((x,13,6.8),(x,17.5,6.8),1.35)).cut(cyl(.85,3.2,(x,13,5.4))).clean()
    body=body.cut(box(-10.2,10.2,9.8,20.2,8,28)).clean()
    feet=meta['mechanisms']['feet']
    local=unite(*[cyl(4.01,11.2,(*f['center'],-5)) for f in feet])
    body=body.cut(box(-75,75,-31,119,-5,5.2).intersect(local))
    for f in feet:body=body.fuse(cyl(4,1.6,(*f['center'],5.2)))
    # Keep split faces at the foot cylinder interfaces, as in R3.1/R3.2.
    cq.exporters.export(body,str(WORK/'BODY_before_export.step'))
    row=export(body,'BODY');save('body_build.json',dict(solid=row,seconds=time.time()-start,windows=windows,foot_glue_z=5.2,source_changes=['obsolete side socket loop omitted','thumb-side ear arms lowered and holes drilled after joining','Y54 arms removed outside X +/-6','rear diagonals 1.6 x 2.8','r3 side rim and bearing lugs','D1 integrated floor/frame and D4-D6 reinforcements','D7 inboard hidden ear; 2.2mm journal; independent retainer bosses and pin entry pockets'],source_level_rebuild=True))

if __name__=='__main__':main()
