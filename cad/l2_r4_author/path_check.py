# G6 for the r4 architecture (side frame printed in BODY): insertion routes for the small loose parts.
# BODY (V2) -> tessellation -> Z-ray parity voxels (h mm). Parts sampled as interior points.
# BFS state = (ix, iy, iz, yaw) with yaw in {0, 90} deg about Z; a yaw change is allowed only if every 5 deg step is free.
# Start = seated pose retreated by `retreat` along `retreat_dir`; goal = all points below Z 4.8 (outside, under the rim).
import sys, json, time, math
from pathlib import Path
from collections import deque
import numpy as np
import cadquery as cq
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location

H = Path(__file__).resolve().parent
h = 0.25
X0, X1, Y0, Y1, Z0, Z1 = -14.0, 34.0, 26.0, 88.0, 3.0, 27.0

def tess(shape, lin=0.03):
    BRepMesh_IncrementalMesh(shape.wrapped, lin, False, 0.2, True)
    tris = []
    for f in shape.Faces():
        loc = TopLoc_Location(); t = BRep_Tool.Triangulation_s(f.wrapped, loc)
        if t is None: continue
        tr = loc.Transformation()
        p = np.array([[q.X(), q.Y(), q.Z()] for q in (t.Node(i).Transformed(tr) for i in range(1, t.NbNodes()+1))])
        ix = np.array([t.Triangle(i).Get() for i in range(1, t.NbTriangles()+1)]) - 1
        tris.append(p[ix])
    return np.vstack(tris)

def voxelize(tri):
    nx, ny, nz = int((X1-X0)/h), int((Y1-Y0)/h), int((Z1-Z0)/h)
    xs = X0 + (np.arange(nx)+0.5)*h; ys = Y0 + (np.arange(ny)+0.5)*h; zs = Z0 + (np.arange(nz)+0.5)*h
    hits = [[] for _ in range(nx*ny)]
    A, B, C = tri[:, 0], tri[:, 1], tri[:, 2]
    for k in range(len(tri)):
        a, b, c = A[k], B[k], C[k]
        x0, x1 = min(a[0], b[0], c[0]), max(a[0], b[0], c[0]); y0, y1 = min(a[1], b[1], c[1]), max(a[1], b[1], c[1])
        i0, i1 = max(0, int(math.ceil((x0-X0)/h-0.5))), min(nx-1, int(math.floor((x1-X0)/h-0.5)))
        j0, j1 = max(0, int(math.ceil((y0-Y0)/h-0.5))), min(ny-1, int(math.floor((y1-Y0)/h-0.5)))
        if i1 < i0 or j1 < j0: continue
        d = (b[1]-c[1])*(a[0]-c[0]) + (c[0]-b[0])*(a[1]-c[1])
        if abs(d) < 1e-12: continue
        for i in range(i0, i1+1):
            px = xs[i]
            for j in range(j0, j1+1):
                py = ys[j]
                l1 = ((b[1]-c[1])*(px-c[0]) + (c[0]-b[0])*(py-c[1]))/d; l2 = ((c[1]-a[1])*(px-c[0]) + (a[0]-c[0])*(py-c[1]))/d; l3 = 1-l1-l2
                if l1 >= 0 and l2 >= 0 and l3 >= 0: hits[i*ny+j].append(l1*a[2]+l2*b[2]+l3*c[2])
    occ = np.zeros((nx, ny, nz), bool)
    for idx, zl in enumerate(hits):
        if len(zl) < 2: continue
        zl = np.unique(np.round(np.sort(zl), 5))
        if len(zl) % 2: zl = zl[:-1]
        i, j = divmod(idx, ny)
        for za, zb in zip(zl[0::2], zl[1::2]): occ[i, j, (zs >= za) & (zs <= zb)] = True
    return occ

def part_points(boxes, step=0.25):
    pts = []
    for (x0, x1, y0, y1, z0, z1) in boxes:
        g = np.mgrid[x0+step/2:x1:step, y0+step/2:y1:step, z0+step/2:z1:step].reshape(3, -1).T
        pts.append(g)
    return np.unique(np.round(np.vstack(pts), 4), axis=0)

def main(body_step, parts_json):
    t0 = time.time()
    cache = H/(Path(body_step).stem + f'_occ_{h}.npy')
    if cache.exists(): occ = np.load(cache)
    else:
        body = cq.importers.importStep(body_step).val(); tri = tess(body); print('triangles', len(tri), flush=True)
        occ = voxelize(tri); np.save(cache, occ)
    # dilate by 1 voxel -> conservative 0.25 mm clearance for loose parts during insertion
    occd = occ.copy()
    for ax in range(3):
        occd |= np.roll(occ, 1, ax) | np.roll(occ, -1, ax)
    print('voxels', occ.sum(), f'{time.time()-t0:.0f}s', flush=True)
    nx, ny, nz = occ.shape
    def blocked(P):
        i = np.floor((P[:, 0]-X0)/h).astype(int); j = np.floor((P[:, 1]-Y0)/h).astype(int); k = np.floor((P[:, 2]-Z0)/h).astype(int)
        inside = (i >= 0) & (i < nx) & (j >= 0) & (j < ny) & (k >= 0) & (k < nz)
        if not inside.all():
            # outside the grid only allowed below the BODY (k<0); other exits = blocked
            if ((k[~inside] >= 0) | (i[~inside] < 0) | (i[~inside] >= nx) | (j[~inside] < 0) | (j[~inside] >= ny)).any(): return True
        return occd[i[inside], j[inside], k[inside]].any()
    spec = json.load(open(parts_json, encoding='utf-8-sig')); results = {}
    for name, p in spec.items():
        pts = part_points(p['boxes']); c = pts.mean(0)
        def pose(d, yaw):
            a = math.radians(yaw); R = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
            return (pts - c) @ R.T + c + np.array(d)*h
        st = tuple(round(v/h) for v in p['retreat']) + (0,)
        seated_ok = not blocked(pose(st[:3], 0))
        q = deque([st]); prev = {st: None}; goal = None; lim = 34/h
        while q:
            s = q.popleft()
            P = pose(s[:3], s[3])
            if P[:, 2].max() < 4.8: goal = s; break
            nbrs = [(s[0]+1, s[1], s[2], s[3]), (s[0]-1, s[1], s[2], s[3]), (s[0], s[1]+1, s[2], s[3]), (s[0], s[1]-1, s[2], s[3]),
                    (s[0], s[1], s[2]+1, s[3]), (s[0], s[1], s[2]-1, s[3]), (s[0], s[1], s[2], 90-s[3])]
            for e in nbrs:
                if e in prev or max(abs(e[0]), abs(e[1]), abs(e[2])) > lim: continue
                if e[3] != s[3]:
                    if any(blocked(pose(e[:3], a)) for a in range(5, 90, 5)) or blocked(pose(e[:3], e[3])): continue
                elif blocked(pose(e[:3], e[3])): continue
                prev[e] = s; q.append(e)
        r = dict(points=len(pts), seated_retreat_free=seated_ok, found=goal is not None, states=len(prev))
        if goal:
            path = []; s = goal
            while s is not None: path.append([round(s[0]*h, 2), round(s[1]*h, 2), round(s[2]*h, 2), s[3]]); s = prev[s]
            path = path[::-1]                                       # outside -> seated
            way = [path[0]]
            for a, b, cc in zip(path, path[1:], path[2:]):
                if np.any(np.sign(np.subtract(b, a)) != np.sign(np.subtract(cc, b))): way.append(b)
            way.append(path[-1]); r['waypoints_offset_mm_yaw'] = way; r['steps'] = len(path)
        results[name] = r; print(name, {k: v for k, v in r.items() if k != 'waypoints_offset_mm_yaw'}, r.get('waypoints_offset_mm_yaw'), f'{time.time()-t0:.0f}s', flush=True)
    json.dump(results, open(H/'path_check.json', 'w'), indent=1)

if __name__ == '__main__': main(sys.argv[1], sys.argv[2])
