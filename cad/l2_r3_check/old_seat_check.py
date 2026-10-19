# Rebuild the R3.2 old side-key seat (mechanics.py 221-287: frame, bridge, flange, shoulders, rails, fence) in assembly
# coordinates and test whether every r3-module / unchanged-BODY overlap lies inside it (i.e. disappears when the seat is deleted).
import json
from pathlib import Path
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
H = Path(__file__).resolve().parent
V = cq.Vector
def vol(s):
    if not s.Solids(): return 0.0
    p = GProp_GProps(); BRepGProp.VolumeProperties_s(s.wrapped, p, 1e-8, True, False); return p.Mass()
def cbox(dx, dy, dz, c):   # centred box, assembly coords
    return cq.Solid.makeBox(dx, dy, dz, V(c[0]-dx/2, c[1]-dy/2, c[2]-dz/2))
meta = json.load(open(r'D:\Quietmirror_L2\_support\repo_L2_ab2240f3\x\Quietmirror-L2-ab2240f3\reports\rebuild_r3_2\design_metadata.json', encoding='utf-8-sig'))
outer = cq.importers.importStep(r'D:\Quietmirror_L2\_support\repo_L2_ab2240f3\x\Quietmirror-L2-ab2240f3\exports\l2_r2_diagnostic\support_reference\MOTHER_OUTER_FROM_R32_SURFACE.step').val()
seat = None; info = []
for m in meta['mechanisms']['side_motions']:
    tx, cy, cz = m['plunger_tip']; wa = tx + 7.12          # construction: tip = wall_x+7.12, mirrored X on export
    X = lambda off: wa - off
    frame = cbox(3.8, 9.2, 7.4, (X(3.2), cy, cz)).cut(cbox(7, 5.85, 4.05, (X(3.8), cy, cz)))
    shoulders = [cbox(2., 1.8, 3.2, (X(2.8), cy+v, cz)) for v in (-4.3, 4.3)]
    bridge = cbox(1.5, 11.4, 7.4, (X(3.8), cy, cz)).cut(cbox(4, 5.85, 4.05, (X(3.8), cy, cz)))
    flange = cbox(3.8, 13.3, 8.7, (X(1.5), cy, cz)).intersect(outer).cut(cbox(10, 10.7, 5.7, (X(1.5), cy, cz)))
    rails = cbox(11.8, 14.4, 1.6, (X(10.4), cy+2., cz-3.75))
    body_near = X(7.72)                                    # assembly X of body_near (construction wall_x+7.72)
    fence = cbox(1.4, 12.4, 4.35, (body_near-7.6, cy+2., 11.825))
    s = frame
    for t in shoulders + [bridge, flange, rails, fence]: s = s.fuse(t)
    seat = s if seat is None else seat.fuse(s)
    info.append(dict(part=m['part'], wall_x_asm=round(wa, 4), cy=cy, cz=cz))
seat = seat.clean()
body = cq.importers.importBrep(r'D:\Quietmirror_L2\l2_repo_scan\brep\BODY.brep').val()
lay = cq.importers.importStep(str(H/'R3_SIDE_MODULE_LAYOUT.step')).val().Solids()
names = ['carrier', 'SF_switch', 'SR_switch', 'SIDE_IO_PCB']
rows = []
for n, s in zip(names, lay[:4]):
    ov = s.intersect(body); rest = ov.cut(seat.translate(V(0, 0, 0))) if ov.Solids() else ov
    # tolerate 0.02 mm modelling offsets: grow the seat slightly
    rest2 = ov.cut(seat.fuse(seat.translate(V(0.02, 0, 0))).fuse(seat.translate(V(-0.02, 0, 0))).fuse(seat.translate(V(0, 0, 0.02))).fuse(seat.translate(V(0, 0, -0.02)))) if ov.Solids() else ov
    parts = []
    for q in rest2.Solids():
        b = q.BoundingBox(); parts.append(dict(volume=round(vol(q), 4), bbox=[round(x, 3) for x in (b.xmin, b.ymin, b.zmin, b.xmax, b.ymax, b.zmax)]))
    rows.append(dict(part=n, overlap_with_unchanged_BODY_mm3=round(vol(ov), 4), outside_old_seat_mm3=round(vol(rest2), 4), outside_pieces=parts))
    print(rows[-1], flush=True)
json.dump(dict(seat=info, seat_volume_mm3=round(vol(seat), 2), results=rows), open(H/'old_seat_check.json', 'w'), indent=1)
cq.exporters.export(seat, str(H/'R32_OLD_SIDE_SEAT_RECONSTRUCTED.step'))
print('seat', info, round(vol(seat), 2))
