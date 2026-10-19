# Inner side-wall X (mother inner surface, from the L2 repo reference STEP) and LEFT_KEY swept envelope near the carrier.
import json, math
from pathlib import Path
import cadquery as cq
REF = Path(r'D:\Quietmirror_L2\_support\repo_L2_ab2240f3\x\Quietmirror-L2-ab2240f3\exports\l2_r2_diagnostic')
inner = cq.importers.importStep(str(REF/'support_reference'/'MOTHER_INNER_FROM_R32_SURFACE.step')).val()
outer = cq.importers.importStep(str(REF/'support_reference'/'MOTHER_OUTER_FROM_R32_SURFACE.step')).val()
def xmax(sol, y, z):
    e = sol.intersect(cq.Edge.makeLine(cq.Vector(0, y, z), cq.Vector(45, y, z)))
    xs = [v.X for d in e.Edges() for v in d.Vertices()]
    return round(max(xs), 3) if xs else None
rows = {}
for y in (41.0, 41.8, 43.0, 44.0, 45.8, 50.0, 54.7, 58.0, 59.0, 60.0, 64.0, 66.0, 68.0, 70.0, 71.2):
    rows[y] = {z: (xmax(inner, y, z), xmax(outer, y, z)) for z in (8.25, 9.5, 10.75, 11.5, 12.1, 13.0, 13.7, 15.2, 16.4)}
    print(y, rows[y], flush=True)
# LEFT_KEY (+X main key) swept about its hinge axis (X dir, Y 38.5, Z 14.32): 0..2.8 deg, front goes down
key = cq.importers.importBrep(r'D:\Quietmirror_L2\l2_repo_scan\brep\LEFT_KEY.brep').val()
kb = key.BoundingBox(); print('LEFT_KEY bbox', [round(c, 3) for c in (kb.xmin, kb.ymin, kb.zmin, kb.xmax, kb.ymax, kb.zmax)])
probe = cq.Solid.makeBox(10, 8, 9, cq.Vector(16.5, 39.0, 11.5))   # around the carrier front end X16.5-26.5, Y39-47, Z11.5-20.5
for a in (0, 0.7, 1.4, 2.1, 2.8, -0.5):
    k = key.rotate(cq.Vector(0, 38.5, 14.32), cq.Vector(1, 38.5, 14.32), a)
    c = k.intersect(probe)
    if c.Solids():
        b = c.BoundingBox(); print('key rot', a, 'in probe ymax', round(b.ymax, 3), 'bbox', [round(v, 3) for v in (b.xmin, b.ymin, b.zmin, b.xmax, b.ymax, b.zmax)], flush=True)
    else: print('key rot', a, 'none in probe', flush=True)
json.dump({str(k): {str(z): v for z, v in d.items()} for k, d in rows.items()}, open(Path(__file__).parent/'wall_x.json', 'w'), indent=1)
