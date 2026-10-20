# Side keys vs the BODY-integrated side frame from 0 deg up to the hard stop (SF +6.80, SR -6.37 deg about vertical pins).
import json
from pathlib import Path
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
H = Path(__file__).resolve().parent; V = cq.Vector
def vol(s):
    if not s.Solids(): return 0.0
    p = GProp_GProps(); BRepGProp.VolumeProperties_s(s.wrapped, p, 1e-6, True, False); return p.Mass()
frame = cq.importers.importStep(r'D:\Quietmirror_L2\fem3d\variants\R4_SIDE_FRAME_ONLY.step').val()
out = {}
for n, (x, y), sg, stop in (('SIDE_FRONT_KEY', (29, 45), 1, 6.80), ('SIDE_REAR_KEY', (29, 70), -1, 6.37)):
    k = cq.importers.importBrep(str(H/'asm_brep'/f'{n}.brep')).val(); rows = []
    for a in [0, 1, 2, 3, 4, 5, 6, round(stop-0.05, 2), stop]:
        s = k.rotate(V(x, y, 0), V(x, y, 1), sg*a); d = s.distance(frame); ov = vol(s.intersect(frame)) if d < 1e-6 else 0.0
        rows.append(dict(angle=a, gap_mm=round(d, 4), overlap_mm3=round(ov, 5))); print(n, rows[-1], flush=True)
    out[n] = rows
json.dump(out, open(H/'side_key_stop_check.json', 'w'), indent=1)
