"""C11 local wheel-group corrections from inherited parameterized parts.

BODY, wheel axis, encoder body, bolt axes and main key outlines are unchanged.
The hypothetical encoder PCB is a NEW custom outline, not a donor-PCB cut.
"""
import json
import numpy as np
from common import *
from contact_audit import rigid_housing

def main():
    meta=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text())
    mo=next(m for m in meta['mechanisms']['motions'] if m['part']=='WHEEL_CARRIER')
    origin=mo['origin'];axis=[origin[0]+1,*origin[1:]]
    original=load('WHEEL_CARRIER',ROOT/'models/L2_r3/parts');carrier=original
    housing=rigid_housing(load('SWITCH_MIDDLE',OUT/'reference'),mo);b=housing.BoundingBox()
    tool=box(b.xmin-.32,b.xmax+.32,b.ymin-.32,b.ymax+.32,b.zmin-.32,b.zmax+.32)
    for angle in np.linspace(-4.4,4.4,45):carrier=carrier.cut(tool.rotate(origin,axis,-float(angle))).clean()
    rows=[export(carrier,'WHEEL_CARRIER')]
    rows[-1].update(removed_mm3=vol(original)-vol(carrier),change='Local0.32mm rigid middle-switch housing clearance; active plunger contact pad retained')
    pcb=load('ENCODER_ADAPTER_PCB_EST',ROOT/'models/L2_r3/reference');previous=vol(pcb)
    pcb=pcb.cut(box(10.9,25,0,70,0,30)).cut(box(8.6,25,28.8,45,0,30)).clean()
    rows.append(export(pcb,'ENCODER_ADAPTER_PCB_EST',False));rows[-1].update(removed_mm3=previous-vol(pcb),change='Custom PCB edge x<=10.9; rear/east notch x>8.6,y>28.8; original mounting and terminal holes retained')
    encoder=baseline('ENCODER_EC10E_HOUSING');previous=vol(encoder)
    encoder=encoder.cut(box(-20,20,0,60,0,8.95)).clean()
    rows.append(export(encoder,'ENCODER_EC10E_HOUSING',False));rows[-1].update(removed_mm3=previous-vol(encoder),change='Trim only terminal/lug tails to assembly Z8.95;0.25mm nominal protrusion below1.2mm adapter PCB. Actual soldering and vendor trim permission require physical confirmation; housing/rotor datum unchanged')
    for n in ['LEFT_KEY_STEEL_PIN','RIGHT_KEY_STEEL_PIN']:
        original=baseline(n);b=original.BoundingBox()
        if n.startswith('LEFT'):trim=box(b.xmin-1,b.xmin+.7,b.ymin-1,b.ymax+1,b.zmin-1,b.zmax+1)
        else:trim=box(b.xmax-.7,b.xmax+1,b.ymin-1,b.ymax+1,b.zmin-1,b.zmax+1)
        pin=original.cut(trim).clean();rows.append(export(pin,n,False));rows[-1].update(original_bounds_mm=bounds(original),change='Shorter steel pin at inboard end by0.70mm; diameter and outboard end unchanged; both sides symmetric')
    save('wheel_group_clearance_changes.json',dict(candidate='C11',parts=rows,body_changed=False,scope='Source-level proposed interfaces; no claim of measured supplier or solder geometry. All affected CAD gates must be rechecked.'))

if __name__=='__main__':main()
