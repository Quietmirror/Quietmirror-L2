# Side-key cap route: exact BRep distance check of every pose (key solid vs V2 BODY) for the tab-first route.
# Route (seated -> outside): rotate +a (SF) / -a (SR) about a vertical axis through the tab region (hinge end swings out),
# slide along Y so the tab leaves the end ring, then move +X until the key is outside the BODY bbox.
import json, math, sys
from pathlib import Path
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
def vol(s):
    if not s.Solids(): return 0.0
    p = GProp_GProps(); BRepGProp.VolumeProperties_s(s.wrapped, p, 1e-6, True, False); return p.Mass()
H = Path(__file__).resolve().parent; V = cq.Vector
body = cq.importers.importStep(r'D:\Quietmirror_L2\fem3d\variants\BODY_V2.step').val()
alpha = float(sys.argv[1]) if len(sys.argv) > 1 else 15.0
res = {}
for n, (px, py), sg, dy in (('SIDE_FRONT_KEY', (28.25, 56.6), 1, -1.5), ('SIDE_REAR_KEY', (28.25, 57.8), -1, 1.5)):
    k = cq.importers.importBrep(str(H/'asm_brep'/f'{n}.brep')).val()
    poses = [('rotate', a, k.rotate(V(px, py, 0), V(px, py, 1), sg*a)) for a in [0.5, 1, 2, 3, 4, 6, 8, 10, 12.5, alpha]]
    ka = poses[-1][2]
    poses += [('slideY', t, ka.translate(V(0, math.copysign(t, dy), 0))) for t in (0.5, 1.0, abs(dy))]
    kb = ka.translate(V(0, dy, 0)); xmin = kb.BoundingBox().xmin; need = 33.3 - xmin
    poses += [('outX', x, kb.translate(V(x, 0, 0))) for x in [0.5, 1, 2, 3, 4, 6, max(need, 6.5)]]
    rows = []
    for kind, v, s in poses:
        d = s.distance(body); ov = vol(s.intersect(body)) if d < 1e-6 else 0.0; rows.append(dict(step=kind, value=round(v, 2), gap_mm=round(d, 4), overlap_mm3=round(ov, 4))); print(n, rows[-1], flush=True)
    res[n] = dict(alpha_deg=sg*alpha, pivot_xy=[px, py], slide_y_mm=dy, out_x_mm=round(max(need, 6.5), 2), poses=rows,
                  min_gap_mm=min(r['gap_mm'] for r in rows), max_overlap_mm3=max(r['overlap_mm3'] for r in rows), ok=all(r['overlap_mm3'] <= 0.001 for r in rows))
json.dump(res, open(H/f'key_paths_exact_{alpha:g}.json', 'w'), indent=1)
print({n: (r['ok'], r['max_overlap_mm3']) for n, r in res.items()})
