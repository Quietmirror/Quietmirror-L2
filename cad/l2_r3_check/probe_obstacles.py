# Map R3.2 BODY obstacles around the +X side-key carrier: main outer hinge, PCB ears, side-wall inner face, rear foot strut.
import json
from pathlib import Path
import numpy as np, cadquery as cq
H = Path(__file__).resolve().parent
body = cq.importers.importBrep(r'D:\Quietmirror_L2\l2_repo_scan\brep\BODY.brep').val()
def zint(x, y):
    e = body.intersect(cq.Edge.makeLine(cq.Vector(x, y, 4.0), cq.Vector(x, y, 32.0)))
    return sorted([round(min(v.Z for v in d.Vertices()), 3), round(max(v.Z for v in d.Vertices()), 3)] for d in e.Edges())
def xint(y, z, x0=5, x1=40):
    e = body.intersect(cq.Edge.makeLine(cq.Vector(x0, y, z), cq.Vector(x1, y, z)))
    return sorted([round(min(v.X for v in d.Vertices()), 3), round(max(v.X for v in d.Vertices()), 3)] for d in e.Edges())
out = {}
# hinge zone: vertical intervals on grid
out['hinge_grid'] = {f'{x},{y}': zint(x, y) for x in (24.5, 25.5, 26.5, 27.5, 28.5, 29.5) for y in (38.0, 40.0, 41.5, 42.5, 43.25, 43.75, 44.5, 45.5, 47.0)}
# X intervals (side wall + internal) at several Y,Z
out['x_lines'] = {f'{y},{z}': xint(y, z) for y in (41.0, 43.0, 44.0, 46.0, 50.0, 54.7, 59.0, 63.0, 66.0, 66.8, 69.0, 71.0) for z in (10.0, 10.9, 11.5, 12.1, 12.9, 13.7, 15.0, 16.4)}
# rear ear zone
out['rear_ear_grid'] = {f'{x},{y}': zint(x, y) for x in (25.0, 26.5, 28.0, 29.5, 30.5) for y in (62.5, 64.0, 66.0, 68.0, 69.5)}
out['front_ear_grid'] = {f'{x},{y}': zint(x, y) for x in (24.0, 25.5, 27.3, 29.0, 30.5) for y in (39.5, 41.0, 43.0, 45.0, 46.5)}
json.dump(out, open(H/'obstacles.json', 'w'), indent=1)
for k, v in out.items():
    print('==', k)
    for kk, vv in v.items(): print(kk, vv)
