"""Rear-centred D2F wheel click, leaving the front USB-C corridor open."""
import math
import cadquery as cq
from mechanics import box, cylinder, beam, join, check, top
from surfaces import half_width
V=cq.Vector

def build_wheel(p,outer):
    h=p['hardware']; parts={}; hardware={}; additions=[]; cuts=[]; terminal_cuts=[]
    wy,wz=28.,19.; py=50.; pivot=[0.,py,wz]
    def hex_prism(af,length,x):
        rr=af/math.sqrt(3)
        v=[V(x,wy+rr*math.cos(k*math.pi/3),wz+rr*math.sin(k*math.pi/3)) for k in range(6)]
        return cq.Solid.extrudeLinear(cq.Wire.makePolygon(v+[v[0]]),[],V(length,0,0))
    wheel=join(cylinder(h['wheel_diameter']/2,h['wheel_width'],(-h['wheel_width']/2,wy,wz),(1,0,0)),
               hex_prism(1.67,6.,-8.85),cylinder(1.,4.2,(3.05,wy,wz),(1,0,0)))
    parts['WHEEL']=check(wheel,'WHEEL')
    encx=-5.75
    yz=[(-4.9,-5.),(-4.9,1.3),(-2.2,3.6),(2.2,3.6),(4.9,1.3),(4.9,-5.)]
    pts=[V(encx-2.2,wy+y,wz+z) for y,z in yz]
    enc=cq.Solid.extrudeLinear(cq.Wire.makePolygon(pts+[pts[0]]),[],V(4.4,0,0))
    enc=enc.cut(cylinder(1.6,7,(encx-3.5,wy,wz),(1,0,0)))
    for yy in (-2.5,0.,2.5):
        enc=join(enc,box(.5,.8,5.7,(encx+2.,wy+yy,wz-7.65)))
    for yy in (-5.4,5.4):
        enc=join(enc,box(.6,1.7,5.7,(encx,wy+yy,wz-7.65)))
    hardware['ENCODER_EC10E_HOUSING']=check(enc,'EC10E')
    hardware['ENCODER_EC10E_ROTOR']=check(cylinder(1.49,4.4,(encx-2.2,wy,wz),(1,0,0)).cut(hex_prism(1.73,7,encx-3.5)),'ROTOR')
    cb=wz-7.
    # >=1.6 mm webs around the lug slots and three terminal holes. The
    # inboard ledge is local to the pins, below the wheel's running envelope.
    cradle=join(box(5.8,16.0,1.6,(encx,wy,cb-.8)),box(2.7,10.,1.6,(-2.85,wy,cb-.8)))
    for yy in (-2.5,0.,2.5):cradle=cradle.cut(cylinder(.625,4,(encx+2.,wy+yy,cb-3)))
    for yy in (-5.4,5.4):cradle=cradle.cut(box(2.35,1.95,4,(encx,wy+yy,cb-1.)))
    bearing=cylinder(2.8,2.4,(4.3,wy,wz),(1,0,0)).cut(cylinder(1.175,4,(3.5,wy,wz),(1,0,0)))
    barrel=cylinder(2.6,6.,(-3.,py,wz),(1,0,0))
    # Left and right rails pass outside the middle-switch housing.
    pad=box(9.5,3.,1.6,(0,41.5,17.38))
    carrier=join(cradle,bearing,barrel,pad,
       beam((encx-2.35,34.,cb-.4),(-5.5,37.5,17.38),1.35),
       beam((-5.5,37.,17.38),(-5.5,43.,18.),1.35),
       beam((-5.5,43.,18.),(-2.,46.8,wz),1.35),
       beam((-2.,46.8,wz),(-2.,py,wz),1.35),
       beam((5.5,wy,18.5),(5.5,43.,18.),1.35),
       beam((5.5,43.,18.),(2.,46.8,wz),1.35),
       beam((2.,46.8,wz),(2.,py,wz),1.35))
    # Full wheel/driver rotational envelope, not just the neutral angle.
    carrier=carrier.cut(cylinder(h['wheel_diameter']/2+.3,h['wheel_width']+.5,(-h['wheel_width']/2-.25,wy,wz),(1,0,0)))
    carrier=carrier.cut(cylinder(1.175,18.,(-9.,wy,wz),(1,0,0)))
    carrier=carrier.cut(cylinder(1.175,10.,(-5.,py,wz),(1,0,0))).clean()
    parts['WHEEL_CARRIER']=check(carrier,'CARRIER')
    hardware['WHEEL_CARRIER_STEEL_PIN']=cylinder(1.,13.8,(-6.9,py,wz),(1,0,0))
    for x in (-4.8,4.8):
        ear=cylinder(2.85,2.4,(x-1.2,py,wz),(1,0,0))
        tz=top(outer,x,py+3)
        lug=box(2.4,4.,tz-wz+.5,(x,py+2.5,(tz+wz+.5)/2))
        ear=join(ear,lug).cut(cylinder(1.175,4,(x-2,py,wz),(1,0,0)))
        additions.append(check(ear,'CARRIER_EAR'))
    cuts.append(cylinder(1.175,82.,(-41,py,wz),(1,0,0)))
    mx,my,mb=.4,41.5,9.05
    switch=box(5.8,12.8,6.5,(mx,my+2,mb+3.25))
    switch=join(switch,cq.Solid.makeSphere(1.1,V(mx,my,mb+6.4)))
    tray=box(9.5,15.5,1.8,(mx,my+2,mb-.9))
    holes=[]
    for jj,dy in enumerate((-1.3,5.2)):
        yy=my+dy;zz=mb+1.5
        switch=switch.cut(cylinder(1.,10.,(-5,yy,zz),(1,0,0)))
        for xx in (mx-3.85,mx+3.85):
            holder=box(1.8,5.6,5.6,(xx,yy,zz)).cut(cylinder(1.2,4,(xx-2,yy,zz),(1,0,0)))
            tray=join(tray,holder)
        hardware[f'WHEEL_M2_SWITCH_BOLT_{jj+1}']=cylinder(1.,12.,(-6,yy,zz),(1,0,0))
        holes.append([mx,yy,zz])
    for ty in (my+2.-5.08,my+2.,my+2.+5.08):
        switch=join(switch,box(.6,1.5,3.7,(mx,ty,mb-1.65)))
        terminal_cuts.append(box(1.2,2.,4.6,(mx,ty,mb-2.1)))
    hardware['SWITCH_MIDDLE']=check(switch,'SWITCH_MIDDLE')
    for sign in (-1,1):
        tray=join(tray,beam((sign*4.,46.,mb-.9),(sign*(half_width(46.,p)-.3),46.,mb-.9),1.25).intersect(outer))
    additions.append(check(tray,'MIDDLE_TRAY'))
    angle=3.8
    # A positive stop under the carrier pad. Its top is machined by the
    # displaced pad itself; this avoids a flat stop intersecting a tilted pad.
    stop=box(.8,2.4,4.,(4.35,41.5,14.))
    pressed=carrier.rotate(pivot,[1.,py,wz],angle).translate((0,0,-.03))
    stop=stop.cut(pressed)
    stop=join(stop,beam((4.35,41.5,12.5),(4.35,42.,8.15),.5))
    additions.append(check(stop,'MIDDLE_STOP'))
    cuts.append(box(19.8,17.8,32.,(0,wy,17.)))
    motion=dict(part='WHEEL_CARRIER',kind='rotate',origin=pivot,axis=[1,0,0],end_deg=angle,
       moving_children=['WHEEL'],moving_hardware=['ENCODER_EC10E_HOUSING','ENCODER_EC10E_ROTOR'],
       switch='SWITCH_MIDDLE',actuation_point=[mx,my,16.58],nominal_actuator_gap_mm=.03,
       switch_mount_holes=holes,calculated_contact_travel_mm=8.5*math.sin(math.radians(angle))+2.42*(math.cos(math.radians(angle))-1)-.03,
       assembly='M2 switch fixing before carrier; steel hinge along X at Y50 Z19. Open rear-centre switch seat.')
    wm=dict(part='WHEEL',axis_origin=[0,wy,wz],axis=[1,0,0],axle_diameter_mm=2.,bearing_hole_mm=2.35,
       hex_af_mm=1.67,encoder_hex_af_min_mm=1.73,minimum_z_mm=wz-h['wheel_diameter']/2,wheel_crown_z_mm=wz+h['wheel_diameter']/2,
       encoder=dict(model='Alps EC10E1220505',mount_height_mm=7.,body_width_mm=9.8,body_thickness_mm=4.4,above_axis_mm=3.6,
          three_terminal_pitch_mm=2.5,designed_clearance_hole_mm=1.25,
          source='https://tech.alpsalpine.com/cms.media/product_catalog_ec_03_ec10e_en_a9ede251c7.pdf'),
       installation='Preassemble on bench; insert integral hex driver along X into encoder rotor, then fit rear click hinge. Pin dimensions are not scaled.')
    return dict(parts=parts,hardware=hardware,additions=additions,cuts=cuts,motion=motion,wheel=wm,terminal_cuts=terminal_cuts)
