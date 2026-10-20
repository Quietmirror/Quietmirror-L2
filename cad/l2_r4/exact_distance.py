"""Full-original-solid BRep distance; no Boolean-clipped frame substitutes.

Independent regression found lost geometry in some OCCT BODY intersections
used as distance crops. A geometric padding argument cannot certify a faulty
Boolean result. All final distance checks use the original supplied shapes.
"""
from common import vol
from OCP.BRepExtrema import BRepExtrema_DistShapeShape

def pair(a,b,an,bn,minimum=.5,intended=False):
    op=BRepExtrema_DistShapeShape(a.wrapped,b.wrapped)
    if not op.IsDone():raise RuntimeError(f'Full original BRep distance failed {an}/{bn}')
    d=op.Value();overlap=vol(a.intersect(b)) if d<1e-6 else 0.;near=[]
    if op.NbSolution():
        for p in [op.PointOnShape1(1),op.PointOnShape2(1)]:near.append([p.X(),p.Y(),p.Z()])
    return dict(a=an,b=bn,gap_mm=d,overlap_mm3=overlap,required_mm=minimum,intended_contact=intended,
        pass_check=overlap<=.001 and (intended or d>=minimum-1e-5),
        distance_kind='BRepExtrema_original_supplied_shapes_no_body_crop',nearest_points_mm=near)
