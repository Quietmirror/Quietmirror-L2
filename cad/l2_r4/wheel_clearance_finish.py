"""C17 local wheel-group corrections from inherited parameterized parts.

BODY, wheel axis, encoder body, bolt axes and main key outlines are unchanged.
The hypothetical encoder PCB is a NEW custom outline, not a donor-PCB cut.
"""
import json
import numpy as np
from common import *
from contact_audit import rigid_housing

def encoder_pcb():
    pcb=load('ENCODER_ADAPTER_PCB_EST',ROOT/'models/L2_r3/reference')
    outside_land=box(8.6,25,0,70,0,30).cut(cyl(2.1,30,(8.5,26.1,0)))
    pcb=pcb.cut(outside_land).clean()
    line_x=lambda y:(46.-y)*23.22/34.-1.7-max(0.,.35*(34.25-y)/3.25)
    edge_tool=cq.Workplane('XY').polyline([(line_x(20),20),(25,20),(25,40),(line_x(40),40),(line_x(34.25),34.25)]).close().extrude(30).val()
    # C15 diagonal passed but revealed rear-edge approach to the fixed
    # Y35.75 support at maximum click. Keep a planar rear edge atY34.55.
    # C17 tapers the forward diagonal further inward while keeping the
    # rear metal-lug land atY34.25. This remains a planar custom outline.
    return pcb.cut(edge_tool).cut(box(-20,25,34.55,70,0,30)).clean()

def main():
    meta=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text())
    mo=next(m for m in meta['mechanisms']['motions'] if m['part']=='WHEEL_CARRIER')
    origin=mo['origin'];axis=[origin[0]+1,*origin[1:]]
    original=load('WHEEL_CARRIER',ROOT/'models/L2_r3/parts');carrier=original
    housing=rigid_housing(load('SWITCH_MIDDLE',OUT/'reference'),mo);b=housing.BoundingBox()
    tool=box(b.xmin-.32,b.xmax+.32,b.ymin-.32,b.ymax+.32,b.zmin-.32,b.zmax+.32)
    tools=[tool]
    for name in ['LEFT_KEY_M2_SWITCH_1_BOLT','RIGHT_KEY_M2_SWITCH_1_BOLT']:
        b=baseline(name).BoundingBox()
        tools.append(box(b.xmin-.32,b.xmax+.32,b.ymin-.32,b.ymax+.32,b.zmin-.32,b.zmax+.32))
    for tool in tools:
        for angle in np.linspace(-4.4,4.4,45):carrier=carrier.cut(tool.rotate(origin,axis,-float(angle))).clean()
    # Keep the source encoder slot and cradle seat. Only the adjacent rising
    # rail above that cradle is relieved around the rear metal lug. The
    # measured prior ordinary gap was0.14654mm atZ13.4866, outside the seat.
    carrier=carrier.cut(box(5.13,6.37,32.23,34.57,12.2,14.52)).clean()
    rows=[export(carrier,'WHEEL_CARRIER')]
    rows[-1].update(removed_mm3=vol(original)-vol(carrier),change='Local0.32mm rigid middle-switch housing and main-switch fastener clearance across45 design poses; active plunger contact pad retained. Independent motion checks remain required')
    previous=vol(load('ENCODER_ADAPTER_PCB_EST',ROOT/'models/L2_r3/reference'))
    # The remaining rectangular corner crossed the fixed front diagonal at
    # +4.1/+4.4deg. Preserve a2.1mm circular mounting land around the existing
    # (8.5,26.1) hole; remove only material outside that land forX>8.6.
    # This is a planar custom-board outline, not a three-dimensional bevel.
    pcb=encoder_pcb()
    rows.append(export(pcb,'ENCODER_ADAPTER_PCB_EST',False));rows[-1].update(removed_mm3=previous-vol(pcb),change='C17 custom planar PCB: R2.1 front mounting land, tapered forward diagonal and rearY34.55, retaining rear metal-lug land atY34.25. Existing hole/terminal centers and thickness retained; exact full-motion validation required')
    encoder=baseline('ENCODER_EC10E_HOUSING');previous=vol(encoder)
    encoder=encoder.cut(box(-20,20,0,60,0,8.95)).clean()
    rows.append(export(encoder,'ENCODER_EC10E_HOUSING',False));rows[-1].update(removed_mm3=previous-vol(encoder),change='Trim only terminal/lug tails to assembly Z8.95;0.25mm nominal protrusion below1.2mm adapter PCB. Actual soldering and vendor trim permission require physical confirmation; housing/rotor datum unchanged')
    for n in ['LEFT_KEY_STEEL_PIN','RIGHT_KEY_STEEL_PIN']:
        original=baseline(n);b=original.BoundingBox()
        if n.startswith('LEFT'):trim=box(b.xmin-1,b.xmin+.7,b.ymin-1,b.ymax+1,b.zmin-1,b.zmax+1)
        else:trim=box(b.xmax-.7,b.xmax+1,b.ymin-1,b.ymax+1,b.zmin-1,b.zmax+1)
        pin=original.cut(trim).clean();rows.append(export(pin,n,False));rows[-1].update(original_bounds_mm=bounds(original),change='Shorter steel pin at inboard end by0.70mm; diameter and outboard end unchanged; both sides symmetric')
    save('wheel_group_clearance_changes.json',dict(candidate='C17',parts=rows,body_changed=False,scope='Source-level proposed interfaces; no claim of measured supplier or solder geometry. All affected CAD gates must be rechecked.'))

if __name__=='__main__':main()
