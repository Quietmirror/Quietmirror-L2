"""Independent transcription and completion of the supplied r3 side module.

Not the missing author's model. Added definitions: terminal Z=16.6, mating
hinge lands, rounded aperture, rear pushrod disk, PCB retention pilot holes.
All assumptions are written into parameters_implemented.json.
"""
import math
from common import *

KEYS=[dict(name='SIDE_FRONT_KEY',short='SF',y0=44.2,y1=56.3,hinge_y=45.,rod_y=50.25,rod_end=25.97,rod_inner=30.36,stop_y=[54.,55.2],stop_x=29.74,angle=6.8,tab=[27.85,28.65,56.,57.1,17.7,19.2],rib=[28.65,30.3,56.,56.3,17.7,19.2]),
      dict(name='SIDE_REAR_KEY',short='SR',y0=58.1,y1=70.8,hinge_y=70.,rod_y=64.45,rod_end=26.47,rod_inner=31.02,stop_y=[59.3,60.5],stop_x=30.04,angle=-6.37,tab=[27.85,28.65,57.35,58.4,15.8,17.3],rib=[28.65,30.9,58.1,58.4,15.8,17.3])]

def yz_mask(y0,y1,z0,z1,r=1.5):
    return cq.Workplane('XY').box(30,y1-y0,z1-z0).edges('|X').fillet(r).val().translate((28,(y0+y1)/2,(z0+z1)/2))

def carrier():
    floor=box(17.3,25.5,41.8,71.2,12.1,13.7)
    for ya,yb in [(46.,54.),(57.5,65.5)]:floor=floor.cut(box(19,23,ya,yb,11.9,13.9))
    wall=box(17.3,18.5,41.8,71.2,12.1,19.5)
    rear_seat=box(18.5,19.,56.05,68.85,13.7,19.5)
    divider=box(18.5,25.5,54.95,55.75,13.7,19.5)
    bits=[floor,wall,rear_seat,divider]
    for x0,xb,xt,y0,y1 in [(25.5,29.45,29.74,53.6,55.4),(26.,29.9,30.04,59.1,61.1)]:
        bits += [box(x0,xb,y0,y1,13.4,15.7),box(x0,xt,y0,y1,15.7,16.4),box(25.5,26.8,y0,y1,12.1,13.7)]
    bits += [box(24,28.2,41.8,45.8,10.75,13.7),box(24,29.2,64.9,67.9,10.75,13.7)]
    for a,b in [(44.4,46),(54.95,55.75),(68.65,70)]:bits.append(box(16.2,17.3,a,b,14.1,15.7))
    result=unite(*bits)
    for x,y in [(25.73,43.3),(27.,66.3)]:result=result.cut(cyl(.85,5,(x,y,9.5)))
    before_slots=vol(result)
    for y in [43.17,48.25,53.33,57.37,62.45,67.53]:result=result.cut(box(16.9,19.1,y-.8,y+.8,16.,17.2))
    # Blind pilots from the accessible PCB side; matching PCB clearance holes.
    # The middle 0.8-wide seat cannot support M1.4, so only the two end seats
    # receive fasteners. Middle seat remains an intentional supporting contact.
    for y in [45.2,69.3]:result=result.cut(cyl(.5,1.5,(16.15,y,14.9),(1,0,0)))
    return valid(result.clean(),'SIDE_SWITCH_CARRIER'),dict(before_terminal_slots_mm3=before_slots,final_mm3=vol(result))

def fixed_features(outer):
    additions=[];cuts=[]
    # Flat shared end-ring land supports both anti-rattle tabs.
    additions.append(box(28.65,35,56.6,57.8,14.5,21).intersect(outer))
    additions.append(box(28.65,35,71.1,72.1,14.5,21).intersect(outer))
    for k in KEYS:
        a,b=k['y0']-.3,k['y1']+.3
        cuts.append(yz_mask(a,b,15.2,19.8,1.8))
        # Continuous top rim, no front or lower protruding lip.
        additions.append(box(28.65,35,a-.3,b+.3,19.8,21).intersect(outer))
        y=k['hinge_y']
        for z0,z1 in [(14.2,15.2),(19.8,20.8)]:
            lug=unite(cyl(1.325,z1-z0,(29,y,z0)),box(29,32.2,y-.9,y+.9,z0,z1).intersect(outer))
            additions.append(lug)
        # Concealed circular bearing relief; touch cap retains rounded outline.
        cuts.append(cyl(1.675,4.6,(29,y,15.2)))
        cuts.append(cyl(.475,8,(29,y,13)))
    return additions,cuts

def key(outer,k,offset=.2):
    mask=yz_mask(k['y0'],k['y1'],15.5,19.5,1.5)
    surface=outer.translate((offset,0,0))
    cap=surface.cut(outer.translate((offset-1.2,0,0))).intersect(mask).clean()
    # Contact-edge finishing is limited to the exposed perimeter. A failed
    # fillet is reported, never silently represented as a finished radius.
    edge_finish=False
    try:
        edges=[e for e in cap.Edges() if e.Center().x>30.8 and e.Length()>1]
        if edges:
            rounded=cap.Solids()[0].fillet(.3,edges)
            if rounded.isValid():cap=rounded;edge_finish=True
    except Exception:pass
    hinge=cyl(1.325,4,(29,k['hinge_y'],15.5))
    web=box(29,33,k['hinge_y']-.55,k['hinge_y']+.55,15.5,19.5).intersect(surface).intersect(mask)
    rod=cyl(1.25,34-k['rod_end']-.55,(k['rod_end']+.55,k['rod_y'],16.6),(1,0,0)).intersect(surface)
    # A flat Ø3 pad with the required 0.33 shim hits the switch housing during
    # rotation. Use a Ø3, 0.6-high spherical crown (R2.175), keeping its tip
    # coordinate and the rod force path. This is an explicit design correction.
    radius=2.175
    disk=cq.Solid.makeSphere(radius,V(k['rod_end']+radius,k['rod_y'],16.6),angleDegrees1=-90,angleDegrees2=90).intersect(box(k['rod_end'],k['rod_end']+.6,k['rod_y']-1.51,k['rod_y']+1.51,15.09,18.11))
    tab=box(*k['tab']);rb=list(k['rib']);rb[1]=34
    rib=box(*rb).intersect(surface).intersect(mask)
    theta=math.radians(k['angle']);yc=k['stop_y'][1] if theta>0 else k['stop_y'][0]
    stop_x=29+(k['stop_x']-29+(yc-k['hinge_y'])*math.sin(theta))/math.cos(theta)
    stop=box(stop_x,34,*k['stop_y'],15.9,16.4).intersect(surface)
    result=unite(cap,hinge,web,rod,disk,tab,rib,stop).cut(cyl(.525,6,(29,k['hinge_y'],14.5))).clean()
    return valid(result,k['name']),dict(**k,stop_rib_inner_x=stop_x,outer_x_offset_mm=offset,normal_offset_approximation='X translation of mother surface; normal distance measured separately',edge_R0p3_applied=edge_finish,connection_correction='Rod and tab rib extended to intersect actual mother-derived cap. Document inner-X estimates otherwise leave a disconnected component; endpoints and tab dimensions retained.')

def electronic_side():
    refs={}
    for n,x0,y0,rod_y,tip,ys in [('SF',18.5,41.85,50.25,25.62,[43.17,48.25,53.33]),('SR',19.,56.05,64.45,26.12,[57.37,62.45,67.53])]:
        sw=box(x0,x0+6.5,y0,y0+12.8,13.7,19.5)
        # Envelope + round plunger; actual FP/OP/TTP still requires measurement.
        sw=unite(sw,cyl(1.,.63,(tip-.63,rod_y,16.6),(1,0,0)),
            *[box(x0-3.7,x0+.05,y-.45,y+.45,16.4,16.8) for y in ys])
        refs[n+'_D2F_01F']=sw
        rod_end=tip+.35;radius=2.175
        original=cq.Solid.makeSphere(radius,V(rod_end+radius,rod_y,16.6),angleDegrees1=-90,angleDegrees2=90)
        shifted=original.translate((-.33,0,0))
        refs[n+'_TUNING_SHIM_0p33']=shifted.cut(original).intersect(box(rod_end-.33,rod_end+.6,rod_y-1.5,rod_y+1.5,15.1,18.1))
    pcb=box(15.2,16.2,42,70,13.3,18.8)
    for y in [43.17,48.25,53.33,57.37,62.45,67.53]:pcb=pcb.cut(cyl(.6,2,(14.7,y,16.6),(1,0,0)))
    for y in [45.2,69.3]:pcb=pcb.cut(cyl(.6,2,(14.7,y,14.9),(1,0,0)))
    refs['SIDE_IO_PCB']=pcb
    for k in KEYS:refs[k['short']+'_VERTICAL_PIN']=cyl(.5,5.5,(29,k['hinge_y'],14.75))
    for i,(x,y) in enumerate([(25.73,43.3),(27,66.3)],1):
        refs[f'CARRIER_M2x5_{i}']=unite(cyl(1.,5,(x,y,8.25)),cyl(1.8,1.2,(x,y,7.05)))
    return refs

def main():
    outer=load('MOTHER_OUTER_FROM_R32_SURFACE',ROOT/'exports/l2_r2_diagnostic/support_reference')
    c,info=carrier();rows=[export(c,'SIDE_SWITCH_CARRIER')];keys=[]
    for k in KEYS:
        s,p=key(outer,k);rows.append(export(s,k['name']));keys.append(p)
        f2,_=key(outer,k,.3);cq.exporters.export(f2,str(OUT/'reference'/(k['name']+'_F2_TRIAL.step')))
    for n,s in electronic_side().items():rows.append(export(s,n,False))
    save('side_module_solids.json',rows)
    save('parameters_implemented.json',dict(source='Independent r3 transcription; author JSON absent',units='mm',side_keys=keys,carrier=info,corrections=['Stop rib Z15.9..16.4 gives 0.5 mm height','Nominal 0.35 gap requires 0.33 conforming PET shim for 0.02 residual gap','Flat pad replaced by R2.175 spherical crown: diameter3, crown height0.6, tip coordinate retained; fixes housing contact during rotation','Two M1.2 end PCB fasteners; middle narrow seat is support only','X-offset cap is an approximation to normal offset','Added concealed hinge relief and explicit lug Z spans; check resulting body'],physical_switch_validation='UNVERIFIED'))

if __name__=='__main__':main()
