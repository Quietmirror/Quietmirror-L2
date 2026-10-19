"""R4 source-defined integrated frame, removable retainers and D7 lever keys.

Coordinates are mm in the inherited assembly frame. Author evidence remains
unchanged in cad/l2_r4_author; this implementation is independently checked.
"""
import math
from common import *

KEYS=[dict(name='SIDE_FRONT_KEY',short='SF',y0=44.2,y1=56.3,hinge_y=45.3,rod_y=50.25,rod_end=25.97,stop_y=[54.,55.2],stop_x=29.74,sign=1,pad_y_offset=0.2018),
      dict(name='SIDE_REAR_KEY',short='SR',y0=58.1,y1=70.8,hinge_y=69.7,rod_y=64.45,rod_end=26.47,stop_y=[59.3,60.5],stop_x=30.04,sign=-1,pad_y_offset=-0.1617)]
PAD_RADIUS=2.175*2.6/3;PAD_HEIGHT=.6*2.6/3
RETAINER_MOUNTS={'SF':dict(x=16.6,y=45.7,pin_x=17.4,pin_y=54.),'SR':dict(x=16.6,y=70.4,pin_x=17.9,pin_y=56.5)}

def inward_travel(k,theta):
    t=math.radians(theta);x=k['rod_end']-29;y=k['rod_y']+k['pad_y_offset']-k['hinge_y']
    return x-(x*math.cos(t)-y*math.sin(t))

def stop_angle(k):
    lo,hi=0.,12.
    for _ in range(60):
        m=(lo+hi)/2
        if inward_travel(k,k['sign']*m)<.6:lo=m
        else:hi=m
    return k['sign']*(lo+hi)/2
for k in KEYS:k['angle']=stop_angle(k)

def yz_mask(y0,y1,z0,z1,r=1.5):
    return cq.Workplane('XY').box(30,y1-y0,z1-z0).edges('|X').fillet(r).val().translate((28,(y0+y1)/2,(z0+z1)/2))

def integrated_frame(outer):
    f=box(17.3,25.5,41.8,71.2,12.1,13.7)
    for ya,yb in [(46.,54.),(57.5,65.5)]:f=f.cut(box(19.5,23,ya,yb,11.9,13.9))
    bits=[f,box(19.,25.5,54.95,55.75,13.7,19.5)]
    for x0,xb,xt,ya,yb in [(25.5,29.45,29.74,53.6,55.4),(26.,29.9,30.04,59.1,61.1)]:
        bits.extend([box(x0,xb,ya,yb,12.1,15.7),box(x0,xt,ya,yb,15.7,16.4)])
    bits.extend([box(24,28.2,41.8,45.8,10.75,13.7),box(24,29.2,64.9,67.9,10.75,13.7)])
    for ya,yb in [(45.8,53.6),(55.4,59.1),(61.1,64.9),(67.9,71.2)]:bits.append(box(25.5,34,ya,yb,12.1,13.7).intersect(outer))
    bits.append(box(25.5,27.9,41.8,43.25,13.7,14.6))
    for mount in RETAINER_MOUNTS.values():
        bits.append(cyl(2.05,1.6,(mount['x'],mount['y'],12.1)))
        bits.append(cyl(1.5,1.6,(mount['pin_x'],mount['pin_y'],12.1)))
    result=unite(*bits)
    for mount in RETAINER_MOUNTS.values():
        result=result.cut(cyl(1.1,2,(mount['x'],mount['y'],11.9)))
        y=mount['pin_y'];result=result.cut(cyl(.8,1.01,(mount['pin_x'],y,12.7)))
        # An upper entry channel lets the integral locating pin translate
        # above the lower 0.30 mm locating socket before the final Z descent.
        result=result.cut(box(14.5,19.0,y-1.1,y+1.1,13.0,13.71))
    return result.clean()

def retainer(short):
    if short=='SF':
        s=box(17.3,18.5,41.8,55,13.7,19.5)
        terminal_y=[43.17,48.25,53.33]
    else:
        s=box(17.3,19.,55.3,71.2,13.7,19.5)
        terminal_y=[57.37,62.45,67.53]
    m=RETAINER_MOUNTS[short]
    s=unite(s,cyl(1.8,3.5,(m['x'],m['y'],13.7)),cyl(.75,1.,(m['pin_x'],m['pin_y'],12.7)))
    s=s.cut(cyl(.85,3.,(m['x'],m['y'],13.7)))
    # 0.55 mm elevated entry is needed by the locating pin. The larger
    # terminal-slot height gives at least 0.25 mm above its lower lip then.
    for y in terminal_y:s=s.cut(box(14.,19.2,y-.8,y+.8,15.6,17.2))
    return valid(s.clean(),short+'_RETAINER')

def fixed_features(outer):
    adds=[box(28.65,35,56.6,57.8,14.5,21).intersect(outer),box(28.65,35,71.1,72.1,14.5,21).intersect(outer)]
    cuts=[];lands=[]
    for k in KEYS:
        a,b=k['y0']-.3,k['y1']+.3;y=k['hinge_y'];sg=k['sign']
        cuts.append(yz_mask(a,b,15.2,19.8,1.8))
        adds.append(box(28.65,35,a-.3,b+.3,19.8,21).intersect(outer))
        for z0,z1 in [(14.2,15.2),(19.8,20.8)]:adds.append(unite(cyl(1.325,z1-z0,(29,y,z0)),box(29,32.2,y-.9,y+.9,z0,z1).intersect(outer)))
        cuts.extend([cyl(1.55,4.6,(29,y,15.2)),cyl(.475,8,(29,y,13))])
        # The requested +X ear at Z20 is outside the curved mother skin here.
        # Put its radial arm inboard, within the existing side opening, and
        # preserve the complete upper fixed lug instead of cutting its skin.
        ya,yb=(y+.4,y+1.4) if sg>0 else (y-1.4,y-.4)
        stop=unite(box(26.5,27.3,ya,yb,18.6,20.8),box(26.5,29.4,ya,yb,19.8,20.8))
        stop=stop.intersect(outer).cut(cyl(.475,8,(29,y,13)))
        lands.append(stop)
    return adds,cuts,lands

def crown(k,shift=0.):
    y=k['rod_y']+k['pad_y_offset'];end=k['rod_end']+shift
    sphere=cq.Solid.makeSphere(PAD_RADIUS,V(end+PAD_RADIUS,y,16.6),angleDegrees1=-90,angleDegrees2=90)
    return sphere.intersect(box(end,end+PAD_HEIGHT,y-1.31,y+1.31,15.29,17.91))

def key(outer,k,offset=.2):
    mask=yz_mask(k['y0'],k['y1'],15.5,19.5,1.5);surface=outer.translate((offset,0,0))
    cap=surface.cut(outer.translate((offset-1.2,0,0))).intersect(mask).clean()
    edge_finish=False
    try:
        edges=[e for e in cap.Edges() if e.Center().x>30.8 and e.Length()>1]
        rounded=cap.Solids()[0].fillet(.3,edges)
        if rounded.isValid():cap=rounded;edge_finish=True
    except Exception:pass
    # A full-height flat-ended barrel cannot pass the rounded aperture even
    # though its Y projection lies inside the rectangular opening bounds.
    # The 2.2 mm journal preserves diameter/wall and both fixed pin supports.
    y=k['hinge_y'];hinge=cyl(1.25,2.2,(29,y,16.4))
    web=box(29,33,y-.55,y+.55,15.5,19.5).intersect(surface).intersect(mask)
    ear=box(26.7,29,y-.4,y+.4,18.6,19.5)
    # Inboard barrel-to-arm root stays within the R1.55 journal clearance.
    bridge=box(27.7,28.3,y-.4,y+.4,18.3,19.0).intersect(cyl(1.25,.7,(29,y,18.3)))
    rod=cyl(1.20,34-k['rod_end']-.40,(k['rod_end']+.40,k['rod_y'],16.6),(1,0,0)).intersect(surface)
    theta=math.radians(k['angle']);yc=k['stop_y'][1] if theta>0 else k['stop_y'][0]
    stop_x=29+(k['stop_x']-29+(yc-y)*math.sin(theta))/math.cos(theta)
    stop=box(stop_x,34,*k['stop_y'],15.9,16.4).intersect(surface)
    s=unite(cap,hinge,web,ear,bridge,rod,crown(k),stop).cut(cyl(.525,6,(29,y,14.5))).clean()
    return valid(s,k['name']),dict(**k,stop_rib_inner_x=stop_x,edge_R0p3_applied=edge_finish,cap_x_offset=offset,hinge_journal_z=[16.4,18.6],hinge_bridge='inboard root clipped to R1.25; z18.3..19.0',outward_stop_ear='inboard radial arm X26.7..29.0, Z18.6..19.5; existing exterior opening unchanged')

def side_references():
    refs={}
    for k,x0,y0,tip,ys in [(KEYS[0],18.5,41.85,25.62,[43.17,48.25,53.33]),(KEYS[1],19.,56.05,26.12,[57.37,62.45,67.53])]:
        n=k['short'];y=k['rod_y']
        refs[n+'_D2F_01F']=unite(box(x0,x0+6.5,y0,y0+12.8,13.7,19.5),cyl(1,.63,(tip-.63,y,16.6),(1,0,0)),*[box(x0-3.7,x0+.05,t-.45,t+.45,16.4,16.8) for t in ys])
        original=cq.Solid.makeSphere(PAD_RADIUS,V(k['rod_end']+PAD_RADIUS,y+k['pad_y_offset'],16.6),angleDegrees1=-90,angleDegrees2=90)
        shifted=original.translate((-.33,0,0))
        refs[n+'_TUNING_SHIM_0p33']=shifted.cut(original).intersect(box(k['rod_end']-.33,k['rod_end']+PAD_HEIGHT,y+k['pad_y_offset']-1.3,y+k['pad_y_offset']+1.3,15.3,17.9))
        refs[n+'_VERTICAL_PIN']=cyl(.5,5.5,(29,k['hinge_y'],14.75))
    for n,m in RETAINER_MOUNTS.items():
        x,y=m['x'],m['y']
        refs[n+'_RETAINER_M2x5']=unite(cyl(1.,5,(x,y,11.6)),cyl(1.8,.8,(x,y,10.8)))
        refs[n+'_RETAINER_WASHER']=cyl(1.8,.5,(x,y,11.6)).cut(cyl(1.1,.7,(x,y,11.5)))
    return refs

def main():
    outer=load('MOTHER_OUTER_FROM_R32_SURFACE',ROOT/'exports/l2_r2_diagnostic/support_reference');rows=[];params=[]
    for n in ['SF','SR']:rows.append(export(retainer(n),n+'_RETAINER'))
    for k in KEYS:
        s,p=key(outer,k);rows.append(export(s,k['name']));params.append(p)
        f2,_=key(outer,k,.3);cq.exporters.export(f2,str(OUT/'reference'/(k['name']+'_F2_TRIAL.step')))
    for n,s in side_references().items():rows.append(export(s,n,False))
    save('side_module_solids.json',rows)
    save('parameters_implemented.json',dict(version='r4',units='mm',side_keys=params,frame='Integrated source feature of BODY, not a separate printed carrier',retainers=['SF_RETAINER','SR_RETAINER'],retainer_mounts=RETAINER_MOUNTS,pad_radius=PAD_RADIUS,pad_height=PAD_HEIGHT,author_commit='f637118455159515a200e6e0f35c0eea1c7d1633',physical_tests='HARDWARE_PENDING'))
if __name__=='__main__':main()
