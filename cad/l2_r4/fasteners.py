"""Explicit generic M2 fastening envelopes, in mm; confirm purchased hardware.

Pan head Ø3.8 x 1.6, nut AF4 x 1.6, washer Ø5/Ø2.2 x 0.3.
These are selected design envelopes rather than a vendor part certification.
"""
import math
import cadquery as cq

def m2_set(prefix,center,axis,half_stack,hardware,clearances):
    def place(s):
        if axis==(1,0,0):s=s.rotate((0,0,0),(0,1,0),90)
        elif axis==(-1,0,0):s=s.rotate((0,0,0),(0,1,0),-90)
        elif axis==(0,0,-1):s=s.rotate((0,0,0),(1,0,0),180)
        return s.translate(center)
    def cyl(r,h,z):return cq.Solid.makeCylinder(r,h,cq.Vector(0,0,z))
    face=half_stack+.3
    shaft=cyl(1.,12.,face-12.)
    hardware[prefix+'_BOLT']=place(shaft.fuse(cyl(1.9,1.6,face)).clean())
    for sign in (-1,1):
        z=half_stack if sign>0 else -face
        hardware[prefix+('_WASHER_HEAD' if sign>0 else '_WASHER_NUT')]=place(cyl(2.5,.3,z).cut(cyl(1.1,.5,z-.1)))
    nut=cq.Workplane('XY').polygon(6,8/math.sqrt(3)).extrude(1.6).val().translate((0,0,-face-1.6))
    hardware[prefix+'_NUT']=place(nut.cut(cyl(1.,2.,-face-1.8)))
    # Do not remove the holder or washer seating face. The driver approaches
    # the head from outside. This is a geometric access hole, not a promise
    # about a particular screwdriver handle fitting the complete assembly.
    clearances.append(place(cyl(2.15,38.,face)))
    clearances.append(place(cyl(2.65,.31,half_stack)))
    clearances.append(place(cyl(2.65,.31,-face-.01)))
    clearances.append(place(cyl(2.55,1.65,-face-1.65)))
    return dict(prefix=prefix,center_mm=list(center),outward_axis=list(axis),
        screw='generic M2 x 12 pan head',head_envelope_mm=[3.8,1.6],
        nut_af_height_mm=[4.,1.6],washer_od_id_thickness_mm=[5.,2.2,.3],
        printed_stack_mm=2*half_stack,nominal_thread_protrusion_mm=12-(2*half_stack+.6+1.6))
