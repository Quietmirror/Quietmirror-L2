# G6 side-key caps: rigid route from outside the BODY to the seated pose (tab first behind the partition end ring).
# Route (seat -> outside): rotate about a vertical axis through the tab region so the hinge end swings out through the
# opening, slide along Y so the tab leaves the end ring, then move +X out of the shell. Checked against V2 BODY voxels
# (0.25 dilation) with the loose parts installed. Key point cloud from the released SIDE_*_KEY BRep.
import json, math
from pathlib import Path
import numpy as np
import cadquery as cq
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN
import path_check as PC
H = Path(__file__).resolve().parent
occ = np.load(H/'BODY_V2_occ_0.25.npy'); h = PC.h; X0, Y0, Z0 = PC.X0, PC.Y0, PC.Z0; nx, ny, nz = occ.shape
spec = json.load(open(H/'loose_parts.json', encoding='utf-8-sig'))
base = occ.copy()
for n in ('SR_switch', 'SF_switch', 'SR_retainer', 'SF_retainer'):
    for (x0, x1, y0, y1, z0, z1) in (spec[n]['boxes'][:2] if n.endswith('switch') else spec[n]['boxes']):
        base[int((x0-X0)/h):int(math.ceil((x1-X0)/h)), int((y0-Y0)/h):int(math.ceil((y1-Y0)/h)), int((z0-Z0)/h):int(math.ceil((z1-Z0)/h))] = True
o = base.copy()   # no dilation: cap fits are 0.3 mm and the tab rests on the end ring by design
def cloud(n):
    s = cq.importers.importBrep(str(H/'asm_brep'/f'{n}.brep')).val(); b = s.BoundingBox()
    g = np.mgrid[b.xmin+0.125:b.xmax:0.25, b.ymin+0.125:b.ymax:0.25, b.zmin+0.125:b.zmax:0.25].reshape(3, -1).T
    c = BRepClass3d_SolidClassifier(s.wrapped); keep = []
    for p in g:
        c.Perform(gp_Pnt(*map(float, p)), 1e-6); keep.append(c.State() == TopAbs_IN)
    return g[np.array(keep)]
def blocked(P):
    i = np.floor((P[:, 0]-X0)/h).astype(int); j = np.floor((P[:, 1]-Y0)/h).astype(int); k = np.floor((P[:, 2]-Z0)/h).astype(int)
    ok = (i >= 0) & (i < nx) & (j >= 0) & (j < ny) & (k >= 0) & (k < nz)
    return bool(o[i[ok], j[ok], k[ok]].any())
def rot(P, piv, deg):
    a = math.radians(deg); R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]]); Q = P.copy()
    Q[:, :2] = (P[:, :2]-piv) @ R.T + piv; return Q
res = {}
for n, piv, sgn, dy in (('SIDE_FRONT_KEY', np.array([28.25, 56.6]), 1, -1.5), ('SIDE_REAR_KEY', np.array([28.25, 57.8]), -1, 1.5)):
    P0 = cloud(n); best = None
    for alpha in (10, 15, 20, 25, 30):
        poses = []
        for a in np.arange(1.0, alpha+0.01, 1.0): poses.append(('rotate', round(sgn*a, 1), rot(P0, piv, sgn*a)))
        Pa = rot(P0, piv, sgn*alpha)
        for t in np.arange(0.25, abs(dy)+0.01, 0.25): poses.append(('slideY', round(math.copysign(t, dy), 2), Pa+np.array([0, math.copysign(t, dy), 0])))
        Pb = Pa+np.array([0, dy, 0]); x = 0.0
        while (Pb[:, 0]+x).min() < 33.6:
            x += 0.25; poses.append(('outX', round(x, 2), Pb+np.array([x, 0, 0])))
        hit = next(((k, v) for k, v, P in poses if blocked(P)), None)
        print(n, 'alpha', alpha, 'poses', len(poses), 'first collision', hit, flush=True)
        if hit is None: best = dict(alpha_deg=sgn*alpha, pivot_xy=piv.tolist(), slide_y_mm=dy, out_x_mm=x, poses=len(poses)); break
    res[n] = best or dict(found=False); print(n, res[n], flush=True)
json.dump(res, open(H/'key_paths.json', 'w'), indent=1)
