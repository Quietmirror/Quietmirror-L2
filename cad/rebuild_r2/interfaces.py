"""Locked USB-C and sensor reservations, above the completely open low band.

The USB4105 envelope is based on GCT's public dimensional drawing. The small
board and sensor hole pattern are explicit generic adapter interfaces, not
invented manufacturer PCB data. Neither is an electrical design.
"""
import cadquery as cq
from mechanics import beam, box, cylinder, join, check
from surfaces import half_width


def build_interfaces(p,outer,parts):
    additions=[];cuts=[];hardware={};gauges={};details={};final_cuts=[]
    # Absolute dimensions: none of these scale when the host is enlarged.
    port_w,port_h=p['fixed_interfaces']['usb_port_opening_mm']
    front=10.5;board_bottom=8.0;board_top=9.0;usb_center=board_top+3.31/2
    connector=box(8.94,7.35,3.31,(0,front+7.35/2,usb_center))
    pcb=box(16,10,1,(0,15.0,8.5))
    for x in (-6.2,6.2):pcb=pcb.cut(cylinder(1.2,3,(x,17.5,7)))
    hardware['USB_C_REFERENCE']=connector
    hardware['USB_ADAPTER_PCB_REFERENCE']=pcb
    socket=box(port_w,9.0,port_h,(0,7.0,usb_center))
    collar=box(14.8,40,8.8,(0,-15.7,usb_center))
    cuts.extend([socket,collar,box(8.0,16.0,50.0,(0,12.0,25.0))])
    # Do not let pressing a main key crush the plugged-in cable or receptacle.
    # The nose gutter widens locally; finger pads at X≈15 remain unchanged.
    key_relief=join(box(14.8,9,40,(0,1.8,20)),box(10.6,15,40,(0,12.0,20)))
    for n in ('LEFT_KEY','RIGHT_KEY'):
        parts[n]=check(parts[n].cut(key_relief).clean(),n+'_USB_CLEARANCE')
    for sign in (-1,1):
        x=sign*6.2
        post=cylinder(2.8,2.4,(x,17.5,5.6))
        # Direct connection to the existing raised main-switch tray, never a
        # bottom sheet across the mouse footprint.
        arm=beam((x,17.5,6.8),(sign*21.5,22.,6.8),1.25).intersect(outer)
        pilot=cylinder(p['hardware']['pilot']/2,3,(x,17.5,5.4))
        additions.append(check(join(post,arm).cut(pilot).cut(box(16.4,10.4,20.,(0,15.,18.))).clean(),'USB_LOCAL_STANDOFF'))
    plug_body=box(14.0,20.,8.0,(0,-6.,usb_center))
    plug_metal=box(8.4,6.5,2.56,(0,7.25,usb_center))
    gauges['USB_PLUG_GAUGE']=join(plug_body,plug_metal)
    details['usb']={
        'connector':'GCT USB4105 dimensional envelope; not a complete charger',
        'source':'https://gct.co/files/drawings/usb4105.pdf',
        'connector_width_depth_height_mm':[8.94,7.35,3.31],
        'port_opening_width_height_mm':[port_w,port_h],
        'face_y_mm':front,'axis_z_mm':usb_center,
        'adapter_pcb_width_depth_thickness_mm':[16,10,1],
        'adapter_holes_mm':[[-6.2,17.5],[6.2,17.5]],
        'mount':'Two M2 screws into 1.7mm pilots in raised posts. PCB outline/hole pattern is a proposed custom adapter, not a catalog board.',
        'plug_body_gauge_mm':[14,20,8],
        'electrical_status':'Mechanical reservation only. No charging circuit, battery or firmware has been designed or verified.'}
    # Four small local tabs surround the downward optical view. They do not
    # constitute a sensor-sized floor or continuous raised ring.
    sensor_y=66.;w,l=p['fixed_interfaces']['sensor_optical_clearance_mm']
    gauge=box(w,l,9.0,(0,sensor_y,9.7))
    gauges['SENSOR_RESERVED_VOLUME']=gauge
    optical=box(14.0,18.0,19.0,(0,sensor_y,4.5))
    gauges['SENSOR_DOWNWARD_OPTICAL_PATH']=optical
    tabs=[]
    for yy,anchor_y in ((55.,55.),(75.5,75.)):
        for sign in (-1,1):
            xx=sign*12.5
            pad=box(6.,8.6,2.4,(xx,yy,11.6))
            slot=join(cylinder(1.2,5,(xx,yy-1.3,9)),cylinder(1.2,5,(xx,yy+1.3,9)),box(2.4,2.6,5,(xx,yy,11.5)))
            pad=pad.cut(slot)
            # Join beyond the slotted bore, with positive material overlap;
            # a beam starting tangent to the slot can leave a Boolean seam.
            if yy==55.:
                arm=join(beam((sign*14.4,yy,11.6),(sign*14.4,yy,6.8),1.2),beam((sign*14.4,yy,6.8),(sign*16.5,yy+3.,6.8),1.2),beam((sign*16.5,yy+3.,6.8),(sign*(half_width(anchor_y+3.,p)-1.3),anchor_y+3.,6.8),1.2))
            else:
                arm=beam((sign*14.4,yy,11.6),(sign*(half_width(anchor_y,p)-1.3),anchor_y,11.6),1.2)
            additions.append(check(join(pad,arm).cut(slot).clean(),'SENSOR_LOCAL_TAB'))
            tabs.append([xx,yy,12.8])
            final_cuts.append(join(cylinder(1.2,15.,(xx,yy-1.3,9)),cylinder(1.2,15.,(xx,yy+1.3,9)),box(2.4,2.6,15.,(xx,yy,16.5))))
    details['sensor']={'reserved_center':[0,sensor_y,9.7],'reserved_size_mm':[w,l,9.0],
        'downward_optical_path_mm':[14.0,18.0],'mount_slots':tabs,'slot_width_mm':2.4,
        'status':'Generic sensor reservation and adjustable M2 adapter tabs, not measured Fenrir sensor/PCB holes. Actual lens working distance and board adapter must be measured.',
        'load_route':'Four local tabs into raised side attachments; no lower sensor plate or ring.'}
    return {'body_additions':additions,'body_cuts':cuts,'final_cuts':final_cuts,'hardware':hardware,'gauges':gauges,'metadata':details}
