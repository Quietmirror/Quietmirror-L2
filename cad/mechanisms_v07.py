"""Original replaceable click cartridges and wheel, CERN-OHL-P-2.0, mm.

The 6 x 6 x 5 mm tactile switch is a mechanical test-kit example, NOT an
ATK/PAW3950 component decision. Real travel/preload must be calibrated.
Local +Z is outwards; pressing is -Z. Guide upper surface is Z=0.
"""
import math
import cadquery as cq
from build_mouse import rounded_box, beam
V=cq.Vector

def union(parts):
    s=parts[0]
    for a in parts[1:]:s=s.fuse(a)
    return s.clean()

def cyl(r,h,c,axis=(0,0,1)):
    return cq.Solid.makeCylinder(r,h,V(*c),V(*axis))

def pose(s,m):
    if m.get('side'):s=s.rotate((0,0,0),(0,1,0),-90)
    return s.translate(m['origin'])

def cartridge(q):
    g=q['radial_clearance'];w,l=q['stem_xy'];travel=q['travel']
    guide=rounded_box(w+4.8,l+4.8,3,1,(0,0,-1.5))
    guide=guide.cut(rounded_box(w+2*g,l+2*g,12,.7,(0,0,-1.5)))
    bosses=[cyl(2.3,9.6,(x,0,-9.6)) for x in (-6.5,6.5)]
    frame=union([guide]+bosses)
    frame=frame.cut(rounded_box(w+2*g,l+2*g,12,.7,(0,0,-1.5)))
    seat=6+2*q.get('switch_seat_clearance_per_side',.3)
    frame=frame.cut(rounded_box(seat,seat,3.8,.4,(0,0,-7.7)))
    for x in (-6.5,6.5):frame=frame.cut(cyl(.85,6.1,(x,0,-9.7)))
    stem=rounded_box(w,l,9,.45,(0,0,1.5))
    shoulder=rounded_box(w+q.get('shoulder_extra_x',3.2),l+3.2,1.6,1,(0,0,travel+.8))
    plunger=union([stem,shoulder]).cut(cyl(.85,5.5,(0,0,-3.01)))
    retainer=rounded_box(w+2.4,l+3.6,1.6,1,(0,0,-3.8))
    retainer=retainer.cut(cyl(1.1,3,(0,0,-5))).cut(cq.Solid.makeCone(2.05,1.1,1.05,V(0,0,-4.601),V(0,0,1)))
    tray=rounded_box(9.8,9.8,1.6,1,(0,0,-10.4))
    tray=union([tray]+[cyl(2.3,1.6,(x,0,-11.2)) for x in (-6.5,6.5)])
    rim=rounded_box(9.8,9.8,3.3,.8,(0,0,-7.95)).cut(rounded_box(seat,seat,6,.4,(0,0,-7.95)))
    for x in (-6.5,6.5):rim=rim.cut(cyl(2.65,7,(x,0,-11.3)))
    tray=tray.fuse(rim)
    for x in (-6.5,6.5):tray=tray.cut(cyl(1.15,5,(x,0,-12)))
    # Four generous terminal slots; these are lead clearance, not a PCB drill.
    for x in (-3.25,3.25):
        for y in (-2.25,2.25):tray=tray.cut(rounded_box(1.7,1.8,4,.25,(x,y,-10.4)))
    # Example body and centre actuator. Terminals are separate reserved volume.
    switch=rounded_box(6,6,3.5,.25,(0,0,-7.85)).fuse(cyl(1.75,1.5,(0,0,-6.1)))
    leads=rounded_box(8,6,3.6,.2,(0,0,-11.4))
    return dict(frame=frame,plunger=plunger,retainer=retainer,tray=tray,switch=switch,terminal_reserve=leads)

def side_face(length=12):
    # Slim joined visual band, slightly tapered ends, no copied Razer geometry.
    pts=[(-2.15,-length/2),(1.75,-length/2),(2.3,length/2-1.1),(.8,length/2),(-1.75,length/2-.8)]
    s=cq.Workplane('XY').polyline(pts).close().extrude(2).edges('|Z').fillet(.65).edges('>Z').fillet(.4).val().translate((0,0,4.2))
    return s

def wheel_parts(p):
    w=p['wheel'];y=-w['y'];z=w['axis_z'];width=w['width'];q=p['mechanism']
    points=[]
    for i in range(576):
        a=2*math.pi*i/576;r=w['diameter']/2-.2+.2*math.cos(24*a)
        points.append((r*math.cos(a),r*math.sin(a)))
    wheel=cq.Workplane('YZ').polyline(points).close().extrude(width).val().translate((-width/2,y,z))
    wheel=wheel.cut(cyl(q['wheel_bore_diameter']/2,20,(-10,y,z),(1,0,0)))
    axle=union([cyl(q['printed_axle_diameter']/2,14.4,(-7.2,y,z),(1,0,0)),cyl(1.9,1.4,(-8.6,y,z),(1,0,0))])
    axle=axle.cut(cyl(.85,4.1,(3.2,y,z),(1,0,0)))
    washer=cyl(1.9,1.2,(7.2,y,z),(1,0,0)).cut(cyl(1.1,2,(7,y,z),(1,0,0)))
    m=p['modules']['middle'];unit=cartridge(q)
    carrier=pose(unit['plunger'],m).cut(cq.Workplane('XY').box(100,100,50).val().translate((0,-35,48.5)))
    items=[carrier,rounded_box(11,6,2,1,(0,-26,9.5))]
    for sign in (-1,1):
        x=sign*4.4
        items += [beam((sign*2,-35,21.7),(x,-27.2,21.2),2.4),beam((x,-27.2,21.2),(x,-27.2,11),2.4),beam((x,-27.2,11),(x,y,z),2.4),beam((x,-27.2,11),(x,-26,9.5),2.4)]
        ear=cyl(2.6,2.8,(sign*3.3 if sign>0 else -6.1,y,z),(1,0,0))
        items.append(ear)
    carrier=union(items).cut(cyl(q['bearing_bore_diameter']/2,20,(-10,y,z),(1,0,0)))
    carrier=carrier.cut(cyl(.85,5,(0,-27.2,7))).cut(rounded_box(2.9,1.5,5,.2,(0,-24.9,10)))
    # Separate replaceable 0.8 mm leaf. Designed interference at tooth peaks
    # is an elastic detent, never described as rigid collision-free rotation.
    leaf=rounded_box(6,5,1.6,.6,(0,-26.5,7.7)).cut(cyl(1.1,4,(0,-27.2,6)))
    leaf=leaf.fuse(rounded_box(2.4,.8,z-.4-7.7,.2,(0,-24.9,(z-.4+7.7)/2)))
    leaf=leaf.fuse(beam((0,-24.9,z-.6),(0,-24.9,z),1.2))
    return dict(wheel=wheel,axle=axle,axle_washer=washer,wheel_carrier=carrier,detent_leaf=leaf)
