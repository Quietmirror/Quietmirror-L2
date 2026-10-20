# Build R3.2 BODY roof-cutout variants P0 / P1 / P7 for 3D FEM comparison.
# Method (only the top cutouts change; every other R3.2 feature is kept):
#   skin  = R2 mother outer.cut(inner)  (the same surfaces R3.2 rebuild_body() uses)
#   fill  = skin ∩ (R3.2 window prisms − keep masks)      -> restores the roof inside the six windows
#   cut   = skin ∩ (new hole prisms − keep masks)          -> new holes go through the skin only, so
#           internal supports added after the windows in R3.2 (sensor tabs etc.) are preserved
#   BODY_V = BODY_R32 ∪ fill − cut
# Window prisms start at Z 11.34 like R3.2 (lower_cut_z = 10.5 * 1.08).
import json, math, os, sys, time
from pathlib import Path
import numpy as np
import cadquery as cq
from shapely.geometry import Polygon, box, LineString
from shapely.ops import unary_union

TMP = Path(os.environ.get('QM_SUPPORT', r'D:\Quietmirror_L2\_support'))
SRC = TMP/'src'/'R3_2_SOURCE'/'cad'/'rebuild_r2'
sys.path.insert(0, str(SRC))
from surfaces import make_surfaces, half_width, roof_height   # noqa: E402
HERE = Path(__file__).resolve().parent
OUT = HERE/'variants'; OUT.mkdir(exist_ok=True)
BODY_STEP = TMP/'src'/'R3_2_STEP'/'exports'/'rebuild_r3_2'/'assembly'/'BODY.step'
meta = json.load(open(TMP/'qm'/'reports__rebuild_r3_2__design_metadata.json', encoding='utf-8-sig'))
p = json.load(open(SRC/'parameters.json', encoding='utf-8-sig'))
Z_CUT = 10.5*1.08
P0 = [Polygon(w['xy']) for w in meta['windows']]     # symmetric set; unmirrored labels do not matter here

def wall_x(y, z):
    w = half_width(y, p); h = roof_height(y, p)
    return w*max(0.0, 1-((z-5)/(h-5))**3.4)**(1/3.4) if h > z else 0.0

def fillet_equal_area(P, r):
    from shapely.affinity import scale
    Q = P.buffer(-r, join_style=1).buffer(r, join_style=1, quad_segs=16)
    lo, hi = 1.0, 1.3
    for _ in range(60):
        m = (lo+hi)/2
        if scale(Q, m, m, origin='centroid').area < P.area: lo = m
        else: hi = m
    return scale(Q, lo, lo, origin='centroid')

def isogrid_p7(P=14.0, w=1.0, fillet=0.5):
    X0, X1, Y0 = -31.0, 31.0, 61.776-20.5
    Y1 = Y0+41.0
    D = box(X0+2, Y0+2, X1-2, Y1-2).difference(box(-3.3, Y0-1, 3.3, Y1+1))
    # keep holes off the grip side walls: stay 2.0 mm inside the outer wall line at Z 13 (rear-slope
    # cuts are allowed, as the R3.2 REAR windows also cut the rear slope down to Z 11.34)
    ys = np.arange(38.0, 88.0, 0.25)
    xs = [max(0.0, wall_x(y, 13.0)-2.0) for y in ys]
    top = Polygon([(x, y) for x, y in zip(xs, ys)] + [(-x, y) for x, y in zip(xs[::-1], ys[::-1])]).buffer(0)
    D = D.intersection(top)
    cx, cy = 0.0, 61.776; ribs = []; L = 200
    for ang in (0, 60, 120):
        a = math.radians(ang); nx, ny = -math.sin(a), math.cos(a)
        for k in range(-40, 41):
            ox, oy = cx+nx*k*P, cy+ny*k*P
            ribs.append(LineString([(ox-L*math.cos(a), oy-L*math.sin(a)), (ox+L*math.cos(a), oy+L*math.sin(a))]).buffer(w/2, cap_style=2))
    holes = D.difference(unary_union(ribs))
    # solid pads where internal parts hang from the roof (found by list_roof_dependents.py):
    # Y67.5 cross-tie ends (touch the roof at x=+-22.07), the central hub behind the wheel-carrier
    # pivot (roof contact x=+-3.6..6, Y50.5-54.5) and the Y54 tie ends. Without them P7 disconnects
    # the Y67.5 tie (the LC3 load path).
    pads = unary_union([box(20.0, 65.3, 27.5, 69.7), box(-27.5, 65.3, -20.0, 69.7),
                        box(-7.0, 49.5, 7.0, 55.5),
                        box(22.5, 52.0, 27.5, 56.0), box(-27.5, 52.0, -22.5, 56.0)])
    holes = holes.difference(pads)
    out = []
    for g in (holes.geoms if hasattr(holes, 'geoms') else [holes]):
        if g.area < 1.0 or g.buffer(-1.0).is_empty: continue
        g = g.buffer(-fillet).buffer(fillet, quad_segs=8)
        for h in (g.geoms if hasattr(g, 'geoms') else [g]):
            if not h.is_empty and h.area >= 1.0 and not h.buffer(-1.0).is_empty: out.append(h)
    return out

def prism(poly, z0=Z_CUT, h=30.0):
    # 0.05 mm chord tolerance: 0.02 left near-coincident plane/fillet faces on P1 hole walls (gmsh overlap error)
    pts = [tuple(map(float, c)) for c in poly.simplify(0.05).exterior.coords][:-1]
    return cq.Workplane('XY').workplane(offset=z0).polyline(pts).close().extrude(h).val()

def masks():
    s = 1.08
    # construction-space keep boxes from rebuild_r2/build.py window_layout(), mirrored to assembly (X -> -X)
    a = cq.Workplane('XY').box(14, 28, 10).val().translate((29*s, 53.5*s, 14.75*s))    # side<0 box -> +X side keys
    b = cq.Workplane('XY').box(14, 33, 8).val().translate((-29*s, 48*s, 13*s))        # other box -> -X
    return a.fuse(b)

def union(solids):
    u = solids[0]
    for s in solids[1:]: u = u.fuse(s)
    return u.clean()

def main():
    t0 = time.time()
    outer, inner, _ = make_surfaces(p)
    skin = outer.cut(inner).clean()
    print('skin', round(skin.Volume(), 1), 'valid', skin.isValid(), f'{time.time()-t0:.0f}s', flush=True)
    body = cq.importers.importStep(str(BODY_STEP)).val()
    print('R3.2 BODY', round(body.Volume(), 2), 'valid', body.isValid(), 'solids', len(body.Solids()), flush=True)
    M = masks()
    fill = skin.intersect(union([prism(q) for q in P0]).cut(M)).clean()
    print('fill (roof inside R3.2 windows)', round(fill.Volume(), 1), flush=True)
    variants = {
        'P0': P0,
        'P1': [fillet_equal_area(q, 1.3) for q in P0],
        'P7': isogrid_p7(),
    }
    report = {}
    for name, polys in variants.items():
        cutter = skin.intersect(union([prism(q) for q in polys]).cut(M)).clean()
        v = body.fuse(fill).clean().cut(cutter).clean()
        sol = v.Solids()
        frags = []
        if len(sol) > 1:
            sol = sorted(sol, key=lambda s: -s.Volume())
            for s in sol[1:]:
                bb = s.BoundingBox()
                frags.append(dict(volume=round(s.Volume(), 4), bbox=[round(bb.xmin, 2), round(bb.ymin, 2), round(bb.zmin, 2), round(bb.xmax, 2), round(bb.ymax, 2), round(bb.zmax, 2)]))
            print('   fragments (discarded, disconnected from BODY):', frags, flush=True)
            if all(f['volume'] < 5.0 for f in frags):
                v = sol[0]; sol = [v]
        ok = v.isValid() and len(sol) == 1
        vol = v.Volume()
        report[name] = dict(holes=len(polys), projected_area_mm2=round(float(unary_union(polys).area), 2),
                            cutter_volume_mm3=round(cutter.Volume(), 2), body_volume_mm3=round(vol, 2),
                            valid=v.isValid(), solids=len(sol), discarded_fragments=frags)
        print(name, report[name], f'{time.time()-t0:.0f}s', flush=True)
        if not ok:
            cq.exporters.export(v, str(OUT/f'{name}_INVALID.step'))
            continue
        cq.exporters.export(v, str(OUT/f'BODY_{name}.step'))
        v.exportStl(str(OUT/f'BODY_{name}.stl'), tolerance=0.02, angularTolerance=0.1)
    report['reference_R32_body_volume_mm3'] = round(body.Volume(), 2)
    report['fill_volume_mm3'] = round(fill.Volume(), 2)
    json.dump(report, open(OUT/'variants.json', 'w'), indent=1)
    print('done', f'{time.time()-t0:.0f}s')

if __name__ == '__main__':
    main()
