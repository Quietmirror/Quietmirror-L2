# Locate the two r3 failures: carrier-wall gap and carrier-hinge overlap
import cadquery as cq
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from pathlib import Path
import r3_carrier_check as R
V = cq.Vector
car, blocks = R.carrier()
body = cq.importers.importBrep(str(R.SCAN/'BODY.brep')).val()
inner = cq.importers.importStep(str(R.REF/'support_reference'/'MOTHER_INNER_FROM_R32_SURFACE.step')).val()
outer = cq.importers.importStep(str(R.REF/'support_reference'/'MOTHER_OUTER_FROM_R32_SURFACE.step')).val()
skin = outer.cut(inner); wall = skin.intersect(R.box(10, 40, 35, 75, 8, 21))
for o in R.P['side_openings']: wall = wall.cut(R.box(20, 40, *o['y'], *o['z']))
hinge = body.intersect(R.box(25.0, 30.0, 35.0, 43.4, 11.0, 22.0)).cut(skin)
d = BRepExtrema_DistShapeShape(car.wrapped, wall.wrapped); d.Perform()
for i in range(1, d.NbSolution()+1):
    p, q = d.PointOnShape1(i), d.PointOnShape2(i); print('wall', round(d.Value(), 4), (round(p.X(), 3), round(p.Y(), 3), round(p.Z(), 3)), (round(q.X(), 3), round(q.Y(), 3), round(q.Z(), 3)))
c = car.intersect(hinge)
for s in c.Solids():
    b = s.BoundingBox(); print('hinge overlap', round(s.Volume(), 5), [round(v, 3) for v in (b.xmin, b.ymin, b.zmin, b.xmax, b.ymax, b.zmax)])
hb = hinge.BoundingBox(); print('hinge ref bbox', [round(v, 3) for v in (hb.xmin, hb.ymin, hb.zmin, hb.xmax, hb.ymax, hb.zmax)])
for s in hinge.Solids():
    b = s.BoundingBox(); print('  hinge part', round(s.Volume(), 3), [round(v, 3) for v in (b.xmin, b.ymin, b.zmin, b.xmax, b.ymax, b.zmax)])
