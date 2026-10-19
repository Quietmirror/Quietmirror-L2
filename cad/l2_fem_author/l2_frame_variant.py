# r4 proposal: side-switch frame printed as part of BODY (floor + divider + stop posts + mount blocks fused to the +X
# ears + floor-to-wall webs + front link into the main outer hinge lug). Back wall becomes a separate retainer part.
#   L2frame     : L2-r3 BODY + frame
#   L2frametie  : + lower cross tie d2.0 @ Y56 Z8.6
import sys, json
from pathlib import Path
import cadquery as cq
H = Path(__file__).resolve().parent
REF = Path(r'D:\Quietmirror_L2\_support\repo_L2_ab2240f3\x\Quietmirror-L2-ab2240f3\exports\l2_r2_diagnostic\support_reference')
V = cq.Vector
def box(x0, x1, y0, y1, z0, z1): return cq.Solid.makeBox(x1-x0, y1-y0, z1-z0, V(x0, y0, z0))
def U(*s):
    r = s[0]
    for t in s[1:]: r = r.fuse(t)
    return r.clean()
outer = cq.importers.importStep(str(REF/'MOTHER_OUTER_FROM_R32_SURFACE.step')).val()
body = cq.importers.importStep(str(H/'variants'/'BODY_L2r3.step')).val()
F = json.load(open(H/'r4_frame.json', encoding='utf-8-sig'))
def frame():
    f = F['floor']; floor = box(*f['x'], *f['y'], *f['z'])
    for w in F['floor_windows']: floor = floor.cut(box(*w['x'], *w['y'], f['z'][0]-1, f['z'][1]+1))
    parts = [floor, box(*F['divider']['x'], *F['divider']['y'], *F['divider']['z'])]
    for k in ('sf', 'sr'):
        p = F['stop_posts'][k]
        parts += [box(*p['x_low'], *p['y'], p['z'][0], p['z_split']), box(*p['x_high'], *p['y'], p['z_split'], p['z'][1])]
    for b in F['blocks']: parts.append(box(*b))
    for w in F['webs']: parts.append(box(w['x'][0], 34.0, *w['y'], *w['z']).intersect(outer))   # run into the wall
    parts.append(box(*F['hinge_link']))
    fr = U(*parts)
    for c in F['retainer_screw_pilots']: fr = fr.cut(cq.Solid.makeCylinder(c['d']/2, 2.0, V(c['x'], c['y'], 11.9)))
    return fr
fr = frame()
cq.exporters.export(fr, str(H/'variants'/'R4_SIDE_FRAME_ONLY.step'))
which = sys.argv[1].split(',') if len(sys.argv) > 1 else ['L2frame', 'L2frametie']
for name in which:
    s = body.fuse(fr)
    if name == 'L2frametie': s = s.fuse(cq.Solid.makeCylinder(1.0, 80, V(-40, 56, 8.6), V(1, 0, 0)).intersect(outer))
    s = s.clean(); sol = s.Solids()
    print(name, 'valid', s.isValid(), 'solids', len(sol), [round(q.Volume(), 1) for q in sol][:4], flush=True)
    cq.exporters.export(max(sol, key=lambda q: q.Volume()), str(H/'variants'/f'BODY_{name}.step'))
