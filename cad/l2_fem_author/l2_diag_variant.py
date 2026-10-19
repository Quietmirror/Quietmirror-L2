# frame + lower tie + rear diagonals restored to d2.6 round (cylinders over the 1.6x2.8 rectangles)
import cadquery as cq
from pathlib import Path
H = Path(__file__).resolve().parent; V = cq.Vector
s = cq.importers.importStep(str(H/'variants'/'BODY_L2frametie.step')).val()
for sx in (1, -1):
    a = V(sx*24.84, 62.64, 6.5); b = V(0, 46, 6.5); d = b - a
    s = s.fuse(cq.Solid.makeCylinder(1.3, d.Length, a, d.normalized()))
s = s.clean(); sol = s.Solids()
print('L2frametiedia valid', s.isValid(), 'solids', len(sol), [round(q.Volume(), 1) for q in sol][:3], flush=True)
cq.exporters.export(max(sol, key=lambda q: q.Volume()), str(H/'variants'/'BODY_L2frametiedia.step'))
