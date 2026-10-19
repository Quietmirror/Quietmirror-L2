# Guided G6 check: verify given waypoint routes (offset mm from the seated pose, yaw deg about Z through the part centre)
# against the V2 BODY voxels (dilated 0.25 mm) plus already-installed loose parts. Segments sampled every 0.25 mm,
# yaw changes every 5 deg. Route listed outside -> seated is checked; first pose must be below the rim (Z<4.8).
import json, math, sys
from pathlib import Path
import numpy as np
import path_check as PC
H = Path(__file__).resolve().parent
occ = np.load(H/'BODY_V2_occ_0.25.npy'); h = PC.h; X0, Y0, Z0 = PC.X0, PC.Y0, PC.Z0
nx, ny, nz = occ.shape
spec = json.load(open(H/'loose_parts.json', encoding='utf-8-sig'))
routes = json.load(open(H/'guided_routes.json', encoding='utf-8-sig'))
def mark(o, boxes):
    for (x0, x1, y0, y1, z0, z1) in boxes:
        i0, i1 = int((x0-X0)/h), int(math.ceil((x1-X0)/h)); j0, j1 = int((y0-Y0)/h), int(math.ceil((y1-Y0)/h)); k0, k1 = int((z0-Z0)/h), int(math.ceil((z1-Z0)/h))
        o[max(i0, 0):i1, max(j0, 0):j1, max(k0, 0):k1] = True
base = occ.copy(); res = {}
for step in routes['sequence']:
    name = step['part']; p = spec[name]
    o = base.copy()
    for ax in range(3): o |= np.roll(base, 1, ax) | np.roll(base, -1, ax)      # 0.25 mm clearance
    pts = PC.part_points(p['boxes']); c = pts.mean(0)
    def blocked(d, yaw):
        a = math.radians(yaw); R = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
        P = (pts - c) @ R.T + c + np.array(d)
        i = np.floor((P[:, 0]-X0)/h).astype(int); j = np.floor((P[:, 1]-Y0)/h).astype(int); k = np.floor((P[:, 2]-Z0)/h).astype(int)
        ok = (i >= 0) & (i < nx) & (j >= 0) & (j < ny) & (k >= 0) & (k < nz)
        if (~ok & ((k >= 0) | (i < 0) | (i >= nx) | (j < 0) | (j >= ny))).any(): return True
        return bool(o[i[ok], j[ok], k[ok]].any())
    way = step['route']; bad = []; n = 0
    for (a, b) in zip(way, way[1:]):
        da = np.array(a[:3], float); db = np.array(b[:3], float)
        L = np.linalg.norm(db-da); m = max(1, int(math.ceil(L/0.25)))
        for t in np.linspace(0, 1, m+1):
            d = da + (db-da)*t; n += 1
            if blocked(d, a[3]): bad.append([round(v, 2) for v in d] + [a[3]]); break
        if b[3] != a[3]:
            for yy in np.arange(a[3], b[3], 5 if b[3] > a[3] else -5):
                n += 1
                if blocked(db, yy): bad.append([round(v, 2) for v in db] + [float(yy)]); break
    first_out = float(((pts - c) + c + np.array(way[0][:3]))[:, 2].max())
    r = dict(poses_checked=n, collisions=bad, starts_below_rim=first_out < 4.8, start_top_z=round(first_out, 2), ok=(not bad and first_out < 4.8))
    res[name] = r; print(name, r, flush=True)
    if r['ok']: mark(base, p['boxes'][:2] if name.endswith('switch') else p['boxes'])   # switch terminals pass through retainer slots by design
json.dump(res, open(H/'guided_paths.json', 'w'), indent=1)
print('ALL_OK', all(r['ok'] for r in res.values()))
