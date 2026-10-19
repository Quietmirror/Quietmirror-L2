# Render the r3 side module (carrier, switch envelopes, PCB, r3 ears) in the R3.2 shell context + list R3.2 overlaps (old seat).
import json, sys
from pathlib import Path
import numpy as np, cadquery as cq
sys.path.insert(0, r'D:\Quietmirror_L2\l2_repo_scan')
H = Path(__file__).resolve().parent
import importlib.util
spec = importlib.util.spec_from_file_location('sm', r'D:\Quietmirror_L2\l2_repo_scan\scan_mesh.py')
# reuse tessellate() without running scan_mesh's main body
src = open(r'D:\Quietmirror_L2\l2_repo_scan\scan_mesh.py', encoding='utf-8').read().split('rows = []')[0].replace('REPO = Path(sys.argv[1])', 'REPO = Path(".")')
ns = {'__file__': str(H/'_scan_stub.py')}; exec(src, ns); tess = ns['tessellate']
import render_views as RV
lay = cq.importers.importStep(str(H/'R3_SIDE_MODULE_LAYOUT.step')).val().Solids()
names = ['L2_CARRIER_DIAG', 'L2_SF_SWITCH_DIAG', 'L2_SR_SWITCH_DIAG', 'L2_SIDE_IO_PCB_DIAG', 'EAR_FRONT_R3', 'EAR_REAR_R3']
mesh = H/'mesh'; mesh.mkdir(exist_ok=True)
RV.HERE = H; RV.OUT = H/'views'; RV.OUT.mkdir(exist_ok=True)
for n, s in zip(names, lay):
    v, t, f = tess(s); np.savez_compressed(mesh/f'{n}.npz', v=v, t=t, face=f)
for n in ('BODY', 'LEFT_KEY', 'WHEEL_CARRIER', 'WHEEL'):
    d = np.load(Path(r'D:\Quietmirror_L2\l2_repo_scan\mesh')/f'{n}.npz'); np.savez_compressed(mesh/f'{n}.npz', **d)
base_color = RV.color
RV.color = lambda n: (0.45, 0.62, 0.45) if n.startswith('EAR_') else base_color(n)
allnames = ['BODY', 'LEFT_KEY', 'WHEEL_CARRIER', 'WHEEL'] + names
tri, part, face = RV.load(allnames)
shell = np.array([allnames[i] in ('BODY', 'LEFT_KEY') for i in part])
keep = ~(shell & (tri[:, :, 0].min(1) > 17.0))
t2, p2, f2 = RV.subdivide(tri[keep], part[keep], face[keep], 1.4)
RV.render(t2, p2, f2, allnames, 'right', title='r3 侧键模块：+X 侧剖视（BODY 在 X>17 移除）', sub='橙 托架 / 红 微动包络 / 紫 SIDE_IO_PCB / 绿 r3 安装耳；R3.2 旧侧键座仍在 BODY 内（灰）').save(RV.OUT/'R3_cut_right.png')
mod = names
tri, part, face = RV.load(mod); tri, part, face = RV.subdivide(tri, part, face, 1.0)
for v in ('top', 'right', 'front', 'iso'):
    RV.render(tri, part, face, mod, v, title=f'r3 侧键模块 {RV.VIEWS[v][3]}', sub='托架 + 微动包络 + PCB + r3 安装耳').save(RV.OUT/f'R3_module_{v}.png')
body = cq.importers.importBrep(r'D:\Quietmirror_L2\l2_repo_scan\brep\BODY.brep').val()
rows = []
for n, s in zip(names[:4], lay[:4]):
    c = s.intersect(body)
    for q in c.Solids():
        b = q.BoundingBox(); rows.append(dict(part=n, volume=round(q.Volume(), 3), bbox=[round(x, 2) for x in (b.xmin, b.ymin, b.zmin, b.xmax, b.ymax, b.zmax)]))
json.dump(rows, open(H/'r3_context_overlaps.json', 'w'), indent=1)
for r in rows: print(r)
