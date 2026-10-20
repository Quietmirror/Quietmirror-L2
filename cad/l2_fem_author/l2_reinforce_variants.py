# Build quick attribution / reinforcement test variants on the released L2-r3 BODY (additive fusions only).
#   L2seat : + reconstructed R3.2 old side seat (attribution test only)
#   L2y54  : + Y54 cross-tie outer arms (r1.2 @ Y54 Z23, wall -> |X| 13.7)
#   L2tie  : + lower cross tie d2.0 @ Y56 Z8.6, wall to wall (clipped by the mother outer surface)
import sys
from pathlib import Path
import cadquery as cq
H = Path(__file__).resolve().parent
REF = Path(r'D:\Quietmirror_L2\_support\repo_L2_ab2240f3\x\Quietmirror-L2-ab2240f3\exports\l2_r2_diagnostic\support_reference')
body = cq.importers.importStep(str(H/'variants'/'BODY_L2r3.step')).val()
outer = cq.importers.importStep(str(REF/'MOTHER_OUTER_FROM_R32_SURFACE.step')).val()
inner = cq.importers.importStep(str(REF/'MOTHER_INNER_FROM_R32_SURFACE.step')).val()
V = cq.Vector
def rod(y, z, r, x0=-40, x1=40): return cq.Solid.makeCylinder(r, x1-x0, V(x0, y, z), V(1, 0, 0))
def save(name, s):
    s = s.clean(); sol = s.Solids()
    print(name, 'valid', s.isValid(), 'solids', len(sol), [round(q.Volume(), 1) for q in sol][:4], flush=True)
    main = max(sol, key=lambda q: q.Volume()) if sol else s
    cq.exporters.export(main, str(H/'variants'/f'BODY_{name}.step'))
which = sys.argv[1].split(',') if len(sys.argv) > 1 else ['L2seat', 'L2y54', 'L2tie']
if 'L2seat' in which:
    seat = cq.importers.importStep(r'D:\Quietmirror_L2\l2_r3_check\R32_OLD_SIDE_SEAT_RECONSTRUCTED.step').val()
    save('L2seat', body.fuse(seat.intersect(outer)))
if 'L2y54' in which:
    arms = rod(54, 23, 1.2, 13.7, 40).fuse(rod(54, 23, 1.2, -40, -13.7)).intersect(outer)
    save('L2y54', body.fuse(arms))
if 'L2tie' in which:
    tie = rod(56, 8.6, 1.0).intersect(outer)
    save('L2tie', body.fuse(tie))
