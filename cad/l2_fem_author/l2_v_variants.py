# Reinforcement candidates on top of L2frametie (frame fused into BODY + lower cross tie d2.0 @ Y56 Z8.6)
#   V1: + vertical struts d2.4 from the lower tie Y40.8 (top Z7.9) up into the inner main-key bearings (X +-9.9, Z 11.8)
#   V2: V1 + Y67.5 high cross tie thickened r1.2 -> r1.5
#   V3: V1 + rear high cross tie r1.2 @ Y75.5 Z21
import sys
from pathlib import Path
import cadquery as cq
H = Path(__file__).resolve().parent; V = cq.Vector
REF = Path(r'D:\Quietmirror_L2\_support\repo_L2_ab2240f3\x\Quietmirror-L2-ab2240f3\exports\l2_r2_diagnostic\support_reference')
outer = cq.importers.importStep(str(REF/'MOTHER_OUTER_FROM_R32_SURFACE.step')).val()
base = cq.importers.importStep(str(H/'variants'/'BODY_L2frametie.step')).val()
def rodx(y, z, r): return cq.Solid.makeCylinder(r, 80, V(-40, y, z), V(1, 0, 0)).intersect(outer)
def strut(x): return cq.Solid.makeCylinder(1.2, 4.6, V(x, 40.8, 7.4), V(0, 0, 1))
def save(name, s):
    s = s.clean(); sol = s.Solids()
    print(name, 'valid', s.isValid(), 'solids', len(sol), [round(q.Volume(), 1) for q in sol][:3], flush=True)
    cq.exporters.export(max(sol, key=lambda q: q.Volume()), str(H/'variants'/f'BODY_{name}.step'))
v1 = base.fuse(strut(9.9)).fuse(strut(-9.9)).clean()
which = sys.argv[1].split(',') if len(sys.argv) > 1 else ['V1', 'V2', 'V3']
if 'V1' in which: save('V1', v1)
if 'V2' in which: save('V2', v1.fuse(rodx(67.5, 23.0, 1.5)))
if 'V3' in which: save('V3', v1.fuse(rodx(75.5, 21.0, 1.2)))
