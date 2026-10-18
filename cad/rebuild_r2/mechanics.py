"""New R2 pinned keys and suspended supports; no inherited v0.9 mechanisms.

All dimensions are millimetres.  Purchased switch envelopes are documented
installation references, not a claim to fit an unmeasured Fenrir donor PCB.
"""
from __future__ import annotations

import math
import cadquery as cq
from surfaces import half_width, roof_height, roof_z

V = cq.Vector


def box(dx, dy, dz, center):
    return cq.Workplane('XY').box(dx, dy, dz).val().translate(center)


def cylinder(radius, length, point, direction=(0, 0, 1)):
    return cq.Solid.makeCylinder(radius, length, V(*point), V(*direction))


def join(*shapes):
    result = shapes[0]
    for item in shapes[1:]:
        result = result.fuse(item)
    return result.clean()


def beam(a, b, radius):
    direction = V(*b)-V(*a)
    return join(cq.Solid.makeCylinder(radius, direction.Length, V(*a), direction.normalized()),
                cq.Solid.makeSphere(radius, V(*a)), cq.Solid.makeSphere(radius, V(*b)))


def check(shape, name, single=True):
    if not shape.isValid() or (single and len(shape.Solids()) != 1):
        raise ValueError(f'{name}: valid={shape.isValid()}, solids={len(shape.Solids())}')
    return shape


def top(outer, x, y):
    line = cq.Edge.makeLine(V(x, y, 0), V(x, y, 65))
    points = outer.intersect(line).Vertices()
    if not points:
        return roof_z(x, y)
    return max(v.Z for v in points)


def rounded_block(dx, dy, dz, center, radius=.55):
    w = cq.Workplane('XY').box(dx, dy, dz)
    try:
        w = w.edges().fillet(radius)
    except Exception:
        pass
    return w.val().translate(center)


def build_mechanics(p, outer, inner):
    additions, cuts, parts, hardware = [], [], {}, {}
    bolt_paths=[]; fastener_cuts=[]; fastener_meta=[]; terminal_cuts=[]
    from fasteners import m2_set
    meta = dict(feet=[], main_hinges=[], side_motions=[], motions=[],
                printed_interfaces=[], installation=[], hardware_limitations=[])
    mh = p['main']; hh = p['hardware']
    root_y = float(mh.get('root_y', 35.0))+.5
    travel_deg = max(2.1,float(mh.get('travel_deg', 2.0)))
    skin = float(mh.get('skin', 2.0))
    pin_d = float(mh.get('pin_diameter', 2.0))
    bore = float(mh.get('pin_hole', 2.35))
    gutter = float(mh.get('gutter_half', 4.2))
    outer_x = float(mh.get('cap_outer', 26.0))
    main_x = float(mh.get('switch_x', 18.3))
    cap_end = root_y-1.0

    # Every low horizontal cut contains only five disks/their own stems.
    for i, (x, y) in enumerate(p['feet']['centers'], 1):
        foot = cylinder(p['feet']['diameter']/2, p['feet']['height'], (x,y,0))
        stem_top = min(8.3,roof_height(y,p)-.3) if i==5 else (7.4 if y<20 else 8.3)
        stem = cylinder(p['feet']['stem_diameter']/2, stem_top-1.5, (x,y,1.5))
        if i == 5:
            end_y = 70.2*p['host']['scale']
            end = (0., end_y, roof_height(end_y,p)-2.2)
            radius = 1.8
        else:
            yy = 10.0 if y < 20 else y
            end = (math.copysign(half_width(yy,p)-2.1,x), yy,
                   6.8 if y < 20 else 11.2)
            radius = 1.4 if y<20 else 1.7
        start_z = max(5.01+radius,stem_top-.8) if i==5 else (6.8 if y<20 else 7.4)
        strut = beam((x,y,start_z),end,radius)
        support = check(join(foot,stem,strut),f'FOOT_{i}_SUPPORT')
        additions.append(support)
        meta['feet'].append(dict(index=i,center=[x,y],diameter_mm=p['feet']['diameter'],
             contact_z=0.,pad_top_z=p['feet']['height'],stem_diameter_mm=p['feet']['stem_diameter'],
             upper_connection=list(end),load_path='vertical foot stem to raised side/crown brace; no bottom plate'))

    roof_skin = outer.cut(outer.translate((0,0,-skin)))
    roof_pocket = outer.cut(outer.translate((0,0,-skin-1.8)))
    for sign, name, sw_name in ((-1,'LEFT_KEY','SWITCH_LEFT'),(1,'RIGHT_KEY','SWITCH_RIGHT')):
        cx = sign*(gutter+outer_x)/2
        cap_mask = box(outer_x-gutter,cap_end,60,(cx,cap_end/2,30))
        cap = roof_skin.intersect(cap_mask)
        # Trim only the very low side sliver; keep the contoured upper touch face.
        cap = cap.intersect(box(80,90,55,(0,40,38.1)))
        # Local wheel/encoder access bay. The solid contact area over the
        # main microswitch remains at |X|=15; only the inner edge retreats.
        # Carry this notch through the rear cap edge; a closed notch left a
        # fragile 0.6 mm tongue at Y36.9..37.5 in the wall-thickness audit.
        notch = rounded_block(19.8,20.8,50.,(0,28.0,27.),1.0)
        cap = cap.cut(notch).clean()
        # The outer key edge slopes down. Set the pin beneath that edge,
        # rather than beneath the higher centre of the key, so the fixed
        # outside bearing cannot pierce the moving touch skin.
        pivot_z = top(outer,sign*(main_x+8.4),root_y)-7.1
        pivot = [0.,root_y,pivot_z]
        barrel = cylinder(2.65,13.2,(sign*main_x-6.6,root_y,pivot_z),(1,0,0))
        web_y = root_y-1.7
        web_top = top(outer,sign*main_x,web_y)-.4
        web = box(11.8,3.0,max(2.,web_top-pivot_z),(sign*main_x,web_y,(web_top+pivot_z)/2))
        cap = join(cap,barrel,web)
        cap = cap.cut(cylinder(bore/2,18,(sign*main_x-9,root_y,pivot_z),(1,0,0))).clean()
        parts[name] = check(cap,name)
        pocket_mask = box(outer_x-gutter+.6,root_y+.8,60,(cx,(root_y+.2)/2,30))
        cuts.append(pocket_mask.intersect(box(100,110,60,(0,45,37.5))))
        # Fixed axle bearings are outside the moving barrel, attached behind
        # the key aperture by tall roof-intersecting lugs.
        ears=[]
        for ax in (sign*main_x-8.4, sign*main_x+8.4):
            ear = cylinder(2.85,2.4,(ax-1.2,root_y,pivot_z),(1,0,0))
            roof_t = top(outer,ax,root_y+3.3)
            lug = box(2.4,4.5,roof_t-pivot_z+.5,(ax,root_y+2.5,(roof_t+pivot_z+.5)/2))
            ear = join(ear,lug).intersect(outer)
            ear = ear.cut(cylinder(bore/2,4,(ax-2,root_y,pivot_z),(1,0,0))).clean()
            ears.append(check(ear,name+'_FIXED_BEARING'))
        additions.extend(ears)
        hardware[name+'_STEEL_PIN'] = cylinder(pin_d/2,21.8,(sign*main_x-10.9,root_y,pivot_z),(1,0,0))
        # Actual lateral tool/pin entry through the retained fixed side skin.
        cuts.append(cylinder(bore/2,82.,(-41.,root_y,pivot_z),(1,0,0)))

        # Conservative complete D2F envelope + separate visible plunger.  This
        # is an explicitly generic socket, not a donor-PCB hole pattern.
        sw_y = 24.0
        touch_z = top(outer,sign*main_x,sw_y)-skin
        switch_base = touch_z-8.53
        tilt=18.0
        tilt_origin=(0.,sw_y,touch_z-.03)
        tilt_axis=(1.,sw_y,touch_z-.03)
        def tilted(shape):return shape.rotate(tilt_origin,tilt_axis,tilt)
        def tilted_point(point):
            x,y,z=point;dy=y-sw_y;dz=z-(touch_z-.03);a=math.radians(tilt)
            return [x,sw_y+dy*math.cos(a)-dz*math.sin(a),touch_z-.03+dy*math.sin(a)+dz*math.cos(a)]
        # Lower the rigid switch housing by 1 mm; a local actuator boss
        # reaches the plunger while the laterally curved key clears the case.
        tip=tilted_point((sign*main_x,sw_y,switch_base+7.5))
        normal=(0.,-math.sin(math.radians(tilt)),math.cos(math.radians(tilt)))
        contact=[tip[j]+.03*normal[j] for j in range(3)]
        boss=cylinder(1.3,1.5,contact,normal)
        parts[name]=check(join(parts[name],boss),name+'_ACTUATOR_BOSS')
        # D2F drawing: the plunger is 4.4 from the front, mounting-hole
        # centres -1.3/+5.2 from it, 1.5 above the housing bottom.
        switch = box(5.8,12.8,6.5,(sign*main_x,sw_y+2.,switch_base+3.25))
        switch = join(switch,cq.Solid.makeSphere(1.1,V(sign*main_x,sw_y,switch_base+6.4)))
        tray=box(9.5,15.4,1.8,(sign*main_x,sw_y+2.,switch_base-.9))
        holders=[]
        holes=[]
        for jj,dy in enumerate((-1.3,5.2)):
            cy=sw_y+dy;hz=switch_base+1.5
            switch=switch.cut(cylinder(1.0,9.,(sign*main_x-4.5,cy,hz),(1,0,0)))
            for dx in (-4.3,4.3):
                inward = dx*sign < 0
                hx=sign*main_x+math.copysign(3.85,dx)
                holder=box(1.8,5.6,5.6,(hx,cy,switch_base+1.5))
                holder=holder.cut(cylinder(1.175,4.,(hx-2,cy,hz),(1,0,0)))
                holders.append(holder)
            local_hw={};local_cuts=[]
            fm=m2_set(name+f'_M2_SWITCH_{jj+1}',(sign*main_x,cy,hz),(sign,0,0),4.75,local_hw,local_cuts)
            hardware.update({k:tilted(v) for k,v in local_hw.items()});fastener_cuts.extend(tilted(v) for v in local_cuts)
            fm['center_mm']=tilted_point((sign*main_x,cy,hz));fm['tilt_about_x_deg']=tilt;fastener_meta.append(fm)
            bolt_paths.append(tilted(cylinder(1.2,82.,(-41.,cy,hz),(1,0,0))))
            holes.append(tilted_point((sign*main_x,cy,hz)))
        for ty in (sw_y+2.-5.08,sw_y+2.,sw_y+2.+5.08):
            switch=join(switch,box(.6,1.5,3.7,(sign*main_x,ty,switch_base-1.65)))
            terminal_cuts.append(tilted(box(1.2,2.0,4.6,(sign*main_x,ty,switch_base-2.1))))
        tray=tilted(join(tray,*holders))
        anchor=tilted_point((sign*(main_x+5.5),sw_y+2.0,switch_base-.9))
        sidewall_x=sign*(half_width(anchor[1],p)-2.1)
        arm=beam(anchor,(sidewall_x,anchor[1],anchor[2]),1.6)
        tray=join(tray,arm)
        if tray.BoundingBox().zmin < 5.01:
            raise ValueError(f'{name} tilted socket violates open band: {tray.BoundingBox().zmin}')
        additions.append(check(tray,name+'_SUSPENDED_TRAY'))
        hardware[sw_name]=check(tilted(switch.clean()),sw_name)

        # Narrow end-stop shoe near the outside of each cap. Its upper face
        # matches a selected point of the key at the final angle, and joins
        # the retained low side skin below the key pocket.
        stop_x,stop_y = sign*23.,11.5
        stop_initial = [stop_x,stop_y,top(outer,stop_x,stop_y)-skin]
        a = math.radians(travel_deg)
        dy,dz = stop_initial[1]-root_y,stop_initial[2]-pivot_z
        stop_z = pivot_z+dy*math.sin(a)+dz*math.cos(a)-.04
        sx = sign*(half_width(stop_y,p)-1.2)
        stop_arm=beam((stop_x,stop_y,6.8),(sx,stop_y,6.8),.85)
        shoe=box(2.,2.,max(.8,stop_z-6.8),(stop_x,stop_y,(stop_z+6.8)/2))
        stop=join(shoe,stop_arm)
        pressed=parts[name].rotate(pivot,[1.,root_y,pivot_z],travel_deg).translate((0,0,-.06))
        stop=stop.cut(pressed).clean()
        additions.append(check(stop,name+'_HARD_STOP'))
        end_displacement = abs((contact[1]-root_y)*math.sin(a)+(contact[2]-pivot_z)*(math.cos(a)-1))
        info=dict(part=name,origin=pivot,axis=[1,0,0],end_deg=travel_deg,
           pin_diameter_mm=pin_d,bore_diameter_mm=bore,diametral_clearance_mm=bore-pin_d,
           actuation_point=contact,switch=sw_name,
           nominal_actuator_gap_mm=.03,calculated_contact_travel_mm=end_displacement-.03,
           stop_reference_point=stop_initial,stop_reference_z=stop_z,
           switch_tilt_deg=tilt,switch_mount_holes=holes,
           switch_mount='local 18 degree tilted socket; two M2 transverse bolts through actual D2F mounting holes; nuts/washers purchased separately')
        meta['main_hinges'].append(info)
        meta['motions'].append(dict(info,kind='rotate'))

    # Both side buttons are captured sliding keys with a removable steel
    # cross-pin behind the guide. The frame shoulders provide hard stops.
    for index,(cy,name,sw_name) in enumerate(zip(p['side']['centers_y'],
         ('SIDE_FRONT_KEY','SIDE_REAR_KEY'),('SWITCH_SIDE_FRONT','SWITCH_SIDE_REAR'))):
        cz=float(p['side']['z']); h=roof_height(cy,p); w=half_width(cy,p)
        fraction=max(0.,min(1.,(cz-5)/(h-5)))
        wall_x=-w*max(0.,1-fraction**3.4)**(1/3.4)
        cap=rounded_block(2.,10.,5.,(wall_x+.2,cy,cz),.55)
        # Two shallow, broad compression lands meet the trimmed guide face
        # at X=wall+2.15 after 0.60 mm travel. They stop the cap before its
        # tongue can drive the switch into the rigid housing.
        cap=join(cap,*[box(.38,1.0,2.8,(wall_x+1.36,cy+dy,cz)) for dy in (-3.9,3.9)])
        tongue=box(6.1,5.2,3.4,(wall_x+4.05,cy,cz))
        key=join(cap,tongue)
        pin_x=wall_x+4.64
        key=key.cut(cylinder(.86,8,(pin_x,cy,cz-4))).clean()
        parts[name]=check(key,name)
        hardware[name+'_CAPTURE_PIN']=cylinder(.75,5.6,(pin_x,cy,cz-2.8))
        cuts.append(box(22,10.7,5.7,(wall_x+3,cy,cz)))
        frame=box(3.8,9.2,7.4,(wall_x+3.2,cy,cz))
        frame=frame.cut(box(7,5.85,4.05,(wall_x+3.8,cy,cz)))
        shoulders=[box(2.,1.8,3.2,(wall_x+2.8,cy+v,cz)) for v in (-4.3,4.3)]
        bridge=box(1.5,11.4,7.4,(wall_x+3.8,cy,cz)).cut(box(4,5.85,4.05,(wall_x+3.8,cy,cz)))
        flange=box(3.8,13.3,8.7,(wall_x+1.5,cy,cz)).intersect(outer)
        flange=flange.cut(box(10,10.7,5.7,(wall_x+1.5,cy,cz)))
        frame=join(frame,bridge,flange,*shoulders)
        # Side switch's long axis is +Y and its plunger points outwards -X.
        body_near=wall_x+7.72
        sw=box(6.5,12.8,5.8,(body_near+3.25,cy+2.,cz))
        sw=join(sw,cylinder(1.0,.62,(body_near+.02,cy,cz),(-1,0,0)))
        # Small upper/bottom rails and a far-end fence form the socket; these
        # remain local rather than spanning the underside as a floor.
        # The top clamp is removable: a fully enclosed socket could contain
        # the switch but obstruct its insertion. Keep the original M2 stack.
        rails=[box(11.8,14.4,1.6,(wall_x+10.4,cy+2.,cz-3.75))]
        clamp=box(9.,14.4,1.6,(body_near+5.,cy+2.,cz+3.75))
        # Low backstop reacts switch force below the horizontal terminals.
        # Its open top lets the case/pins descend before the clamp is fitted.
        fence=box(1.4,12.4,4.35,(body_near+7.6,cy+2.,11.825))
        frame=join(frame,*rails,fence)
        side_holes=[]
        for jj,dy in enumerate((-1.3,5.2)):
            hx,hy=body_near+5.,cy+dy
            sw=sw.cut(cylinder(1.,8.,(hx,hy,cz-4.)))
            frame=frame.cut(cylinder(1.2,12.,(hx,hy,cz-6.)))
            clamp=clamp.cut(cylinder(1.2,5.,(hx,hy,cz+1.5)))
            fastener_meta.append(m2_set(name+f'_M2_SWITCH_{jj+1}',(hx,hy,cz),(0,0,1),4.55,hardware,fastener_cuts))
            side_holes.append([hx,hy,cz])
        for ty in (cy+2.-5.08,cy+2.,cy+2.+5.08):
            sw=join(sw,box(3.7,1.5,.6,(body_near+8.15,ty,cz)))
            terminal_cuts.append(box(4.6,2.0,1.2,(body_near+8.6,ty,cz)))
        hardware[sw_name]=check(sw.clean(),sw_name)
        parts[name+'_SWITCH_CLAMP']=check(clamp.clean(),name+'_SWITCH_CLAMP')
        capture_channel=join(cylinder(.86,6.,(pin_x,cy,cz-3.)),cylinder(.86,6.,(pin_x+.6,cy,cz-3.)),box(.6,1.72,6.,(pin_x+.3,cy,cz)))
        frame=frame.cut(capture_channel).cut(cylinder(.86,10.,(pin_x,cy,cz+2.7))).clean()
        cuts.append(capture_channel)
        cuts.append(cylinder(.86,30.,(pin_x,cy,cz+2.7)))
        additions.append(check(frame,name+'_GUIDE_AND_SUSPENDED_SOCKET'))
        move=float(p['side']['travel'])
        m=dict(part=name,kind='translate',end_vector=[move,0.,0.],switch=sw_name,
             actuation_point=[wall_x+7.1,cy,cz],plunger_tip=[body_near-.6,cy,cz],
             nominal_actuator_gap_mm=.02,hard_stop_travel_mm=move,
             guide_clearance_per_side_mm=.325,capture_pin_diameter_mm=1.5,
             capture_pin_hole_mm=1.72,capture_slot_length_mm=2.32,minimum_tongue_pin_end_web_mm=1.60,
             switch_mount_holes=side_holes,switch_mount='two M2 bolts along Z through D2F mounting holes and local suspended top/bottom rails',
             assembly='Insert key from exterior, then 1.5 mm steel capture pin along Z from open top before switch socket is filled')
        meta['side_motions'].append(m);meta['motions'].append(m)

    from wheel_mechanism import build_wheel
    wm=build_wheel(p,outer)
    parts.update(wm['parts']);hardware.update(wm['hardware'])
    additions.extend(wm['additions']);cuts.extend(wm['cuts'])
    meta['wheel']=wm['wheel'];meta['motions'].append(wm['motion'])
    terminal_cuts.extend(wm['terminal_cuts'])
    for j,hole in enumerate(wm['motion']['switch_mount_holes'],1):
        hardware.pop(f'WHEEL_M2_SWITCH_BOLT_{j}')
        fastener_meta.append(m2_set(f'WHEEL_M2_SWITCH_{j}',hole,(1,0,0),4.75,hardware,fastener_cuts))
    meta['fasteners']=fastener_meta
    cuts.extend(fastener_cuts)

    # Four small adjustable M2 ears, tied directly to adjacent side skin.
    # There is deliberately no PCB-shaped plate and no invented donor holes.
    mounting=[]
    for yy in (43.,66.):
        for sign in (-1,1):
            xx=sign*(half_width(yy,p)-4.0)
            ear=box(7.6,7.6,2.5,(xx,yy,9.5))
            slot=join(cylinder(1.2,5,(xx,yy-.8,7)),cylinder(1.2,5,(xx,yy+.8,7)),box(2.4,1.6,5,(xx,yy,9.5)))
            ear=ear.cut(slot)
            arm=beam((xx,yy,9.5),(sign*(half_width(yy,p)-2.0),yy,9.5),1.3)
            additions.append(check(join(ear,arm),'PCB_LOCAL_M2_EAR'))
            mounting.append(dict(center=[xx,yy,9.5],slot_width_mm=2.4,slot_length_mm=4.0))
    # Initial FEM exposed excessive lateral compliance. Two high cross-ties
    # transfer grip loads between the sides above the switches/optical volume.
    # A raised front tie couples the middle-switch tray to both side walls.
    cross_ties=[]
    for yy,zz,rr in ((54.,23.,1.2),(67.5,23.,1.2),(40.8,6.6,1.3)):
        probe=cq.Edge.makeLine(V(-45,yy,zz),V(45,yy,zz))
        edges=outer.intersect(probe).Vertices()
        reach=max(abs(q.X) for q in edges)-2.0
        tie=beam((-reach,yy,zz),(reach,yy,zz),rr)
        additions.append(check(tie,'RAISED_CROSS_TIE'))
        cross_ties.append(dict(center_yz_mm=[yy,zz],diameter_mm=2*rr,span_mm=2*reach))
    meta['raised_cross_ties']=cross_ties
    # Raised diagonal ties connect all four side feet into triangles in plan.
    # These axial load paths address the large in-plane frame sway found by
    # the real FEM. Their lowest point is 5.2 mm, preserving the entire Z0..5
    # exclusion band; there is no plate, perimeter floor or low lattice.
    diagonal_ties=[]
    hub=(0.,46.,6.5)
    additions.append(check(box(8.,6.,2.6,hub),'LOCAL_MIDDLE_TRAY_HUB'))
    for x,y in p['feet']['centers'][:4]:
        a=(float(x),float(y),6.5)
        additions.append(check(beam(a,hub,1.3),'RAISED_DIAGONAL_TIE'))
        diagonal_ties.append(dict(start=list(a),end=list(hub),diameter_mm=2.6))
    meta['raised_diagonal_ties']=diagonal_ties
    meta['generic_electronics_mounts']=dict(ears=mounting,
        status='Four generic local slotted M2 attachment ears; board adaptor, sensor carrier, battery retention and charging PCB remain donor-specific and require measurement. No bottom plate supplied.')
    meta['hardware_reference']=dict(switch='Omron D2F pin-plunger envelope, conservative 12.8 x 5.8 x 6.5 mm',
       source='https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2f.pdf',
       pretravel_max_mm=.5,overtravel_min_mm=.25,
       important='The shell uses generic envelope positioning. Exact free position, operating point, terminals, PCB holes and retention must be calibrated to the purchased switch. Do not infer Fenrir PCB compatibility.')
    meta['hardware_limitations']=[
       'Original Fenrir Pro PCB, sensor lens, battery and charging circuit have not been measured or verified.',
       'Alps EC10E1220505 geometry and pin pattern use its public outline drawing, not formal supply specifications or a measured sample.',
       'Integral PLA 1.67 mm AF encoder hex drive needs a torsion/fit coupon; a machined metal drive shaft is advised if long-term durability is required.',
       'Five D2F sockets use explicit M2 bolts, washers and nuts. Actual switch travel, wire exit and printed fits must still be calibrated on the purchased components.',
       'No universal claim of safe switch overtravel: supplied gaps/stops are geometric starting values; shim contact height to actual PT/OP before use.'
    ]
    meta['installation']=[
       {'step':1,'parts':['BODY'],'action':'Inspect five pads and raised supports; no removable bottom plate is required.'},
       {'step':2,'parts':['SWITCH_SIDE_REAR','SIDE_REAR_KEY_SWITCH_CLAMP','SWITCH_SIDE_FRONT','SIDE_FRONT_KEY_SWITCH_CLAMP'],'action':'Rear switch first. Enter through the open nose, temporarily inboard and raised; follow the staged routes in insertion_checks.json. Lower into the open socket, slide its removable clamp from the front, then fit its M2 hardware.'},
       {'step':3,'parts':['SWITCH_MIDDLE','SWITCH_LEFT','SWITCH_RIGHT'],'action':'Middle switch enters from the nose 4 mm raised, then lowers its terminals through the tray. Main switches descend along the 18 degree tilted socket normal. Fit two M2 x 12 bolts, two washers and one nut per bolt.'},
       {'step':4,'parts':['WHEEL','WHEEL_CARRIER','ENCODER_EC10E_HOUSING','WHEEL_CARRIER_STEEL_PIN'],'action':'Preassemble encoder and wheel outside body. Slide from the open nose 0.4 mm above its final level, lower, then insert the 2 mm hinge pin from the right-hand side; the left-side clamps obstruct the opposite insertion direction.'},
       {'step':5,'parts':['LEFT_KEY','RIGHT_KEY','SIDE_FRONT_KEY','SIDE_REAR_KEY'],'action':'Main keys enter from above 3 mm forward, lower to 5 mm above the final height, then move diagonally rearward/down into the hinge. Fit hinge pins from each outer side. Side keys enter from the exterior, followed by vertical 1.5 mm capture pins. Retain pin ends using a removable adhesive spot outside all bearings; no permanent clip grooves are designed.'},
       {'step':6,'parts':['BODY'],'action':'Fit measured electronic board/adaptors to four local M2 slots; keep sensor downward view unobstructed and set measured lens height. Electronics and adaptor are not included as verified donor parts.'},
       {'step':7,'parts':['BODY'],'action':'Affix five PTFE pads after confirming coplanarity; calibrate key stops and test return motion before powering.'}
    ]
    meta['open_bottom']='Only five foot disks and their own stems below Z=5 mm. All other load routes are raised; no continuous bottom skin, perimeter floor ring or grid is added.'
    # Later braces must never refill a previously defined pin/tool path.
    pin_paths=[cylinder(bore/2,82.,(-41.,h['origin'][1],h['origin'][2]),(1,0,0)) for h in meta['main_hinges']]
    pin_paths.append(cylinder(1.175,82.,(-41.,50.,19.),(1,0,0)))
    cuts.extend(bolt_paths)
    for k,shape in enumerate(additions):
        for path in pin_paths+bolt_paths+fastener_cuts:
            shape=shape.cut(path)
        additions[k]=check(shape.clean(),f'FIXED_SUPPORT_{k}')
    for name,shape in parts.items():check(shape,name)
    return dict(body_additions=additions,body_cuts=cuts,parts=parts,hardware=hardware,metadata=meta,terminal_cuts=terminal_cuts)
