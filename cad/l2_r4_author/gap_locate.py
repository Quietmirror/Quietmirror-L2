# Locate the four sub-threshold gaps of the released L2-r3 (final BODY vs wheel carrier / estimated electronics envelopes)
import json
from pathlib import Path
import cadquery as cq
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
H = Path(__file__).resolve().parent; INP = H/'inputs'
env = json.load(open(r'D:\Quietmirror_L2\_support\l2r3\electronic_envelopes.json', encoding='utf-8-sig'))
body = cq.importers.importStep(str(INP/'BODY.step')).val()
wc = cq.importers.importStep(str(INP/'WHEEL_CARRIER.step')).val()
def box(c, s): return cq.Solid.makeBox(s[0], s[1], s[2], cq.Vector(c[0]-s[0]/2, c[1]-s[1]/2, c[2]-s[2]/2))
items = {'WHEEL_CARRIER': wc}
for grp in env.values():
    if not isinstance(grp, list): continue
    for e in grp:
        if e.get('name') in ('ANTENNA_KEEPOUT_EST', 'BATTERY_SERVICE_EST', 'USB_ROUTE_EST', 'BATTERY_CELL_EST', 'ANTENNA_EST'):
            items[e['name']] = box(e['center'], e['size']); print(e)
out = {}
for n, s in items.items():
    d = BRepExtrema_DistShapeShape(body.wrapped, s.wrapped); d.Perform()
    sols = []
    for i in range(1, min(d.NbSolution(), 6)+1):
        p, q = d.PointOnShape1(i), d.PointOnShape2(i)
        sols.append(dict(body=[round(p.X(), 3), round(p.Y(), 3), round(p.Z(), 3)], other=[round(q.X(), 3), round(q.Y(), 3), round(q.Z(), 3)]))
    out[n] = dict(gap=round(d.Value(), 4), points=sols); print(n, out[n], flush=True)
json.dump(out, open(H/'gap_locate.json', 'w'), indent=1)
