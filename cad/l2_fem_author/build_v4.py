# Variant builder v4: clean roof patch without old window seams.
#   sR    = mother skin ∩ region prism (region = windows ∪ P7 area, +1.5 mm; Z >= 11.34; minus keep masks)
#   base  = R32 − sR
#   win0  = R3.2 window prisms (exact outlines) − keep masks
#   voids = sR − R32 − win0          (R3.2 roof openings that are NOT the windows: side-key pin holes etc.)
#   supp  = R32 ∩ sR ∩ win0          (R3.2 internal support material standing inside the window skin volume)
#   BODY_V = base ∪ (sR − voids − holes_V) ∪ supp
# The old window outlines no longer exist as seam edges on the new skin (they crossed the new hole arcs at
# the ROOT front corners and broke the mesh). P0d (holes = win0) must reproduce R3.2.
import sys, json, time
import cadquery as cq
from shapely.geometry import Point
from shapely.ops import unary_union
import build_variants as B

def V(s): return round(s.Volume(), 2)

def main(names):
    t0 = time.time()
    outer, inner, _ = B.make_surfaces(B.p)
    skin = outer.cut(inner).clean()
    R = cq.importers.importStep(str(B.BODY_STEP)).val()
    M = B.masks()
    p7 = B.isogrid_p7()
    region_poly = unary_union(B.P0 + [unary_union(p7).convex_hull.intersection(unary_union([q.buffer(3.0) for q in p7]))]).buffer(1.5)
    regs = list(region_poly.geoms) if hasattr(region_poly, 'geoms') else [region_poly]
    # leave R3.2 untouched within r = 2.0 mm of the side-key pin holes: there the R3.2 pin hole runs ~0.08 mm
    # past the old SHOULDER window wall (a near-tangent detail that broke every rebuilt variant's mesh)
    PINS = ((26.96, 50.0), (27.76, 65.0))
    pin_excl = B.union([cq.Workplane('XY').center(px, py).circle(2.0).extrude(45.0).val() for px, py in PINS])
    sR = skin.intersect(B.union([B.prism(r) for r in regs]).cut(M).cut(pin_excl)).clean()
    base = R.cut(sR).clean()
    win0 = B.union([B.prism(q) for q in B.P0]).cut(M)
    voids = sR.cut(R).cut(win0).clean()
    supp = R.intersect(sR).intersect(win0).clean()
    vs = sorted(voids.Solids(), key=lambda s: -s.Volume()); ss = sorted(supp.Solids(), key=lambda s: -s.Volume())
    print('sR', V(sR), 'base', V(base), 'voids', V(voids), len(vs), 'supp', V(supp), len(ss), f'{time.time()-t0:.0f}s', flush=True)
    for s in vs[:8]:
        bb = s.BoundingBox(); print('   void', round(s.Volume(), 2), [round(c, 2) for c in (bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax)], flush=True)
    for s in ss[:8]:
        bb = s.BoundingBox(); print('   supp', round(s.Volume(), 2), [round(c, 2) for c in (bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax)], flush=True)
    pins = unary_union([Point(26.96, 50.0).buffer(2.3), Point(27.76, 65.0).buffer(2.3)])
    def off_pins(polys):
        out = []
        for q in polys:
            d = q.difference(pins)
            out += [g for g in (d.geoms if hasattr(d, 'geoms') else [d]) if g.area > 1.0]
        return out
    sets = {'P0d': None, 'P1d': off_pins([B.fillet_equal_area(q, 1.3) for q in B.P0]), 'P7d': off_pins(p7)}
    # R3.2's rear pin hole crosses the old SHOULDER window wall by ~0.08 mm, so the extracted voids near the
    # pins are slivers (0.1 / 1.31 mm3) that leave near-tangent faces once the window moves away. Replace
    # every void fragment near a pin by the complete pin-hole cylinder (d1.72), keep all other voids as found.
    voids2 = B.union(vs) if vs else None
    print('voids kept', [round(s.Volume(), 2) for s in vs], '(pin-hole areas excluded from the region)', flush=True)
    clean_skin = sR.cut(voids2).clean() if voids2 is not None else sR
    rep = json.load(open(B.OUT/'variants.json'))
    for name in names:
        holes = win0 if sets[name] is None else B.union([B.prism(q) for q in sets[name]]).cut(M)
        patch = clean_skin.cut(holes).clean()
        v = base.fuse(patch).fuse(supp).clean()
        sol = sorted(v.Solids(), key=lambda s: -s.Volume())
        frag = [round(s.Volume(), 3) for s in sol[1:]]
        if sol and all(f < 5 for f in frag): v = sol[0]
        info = dict(method='v4 clean patch', holes=6 if sets[name] is None else len(sets[name]),
                    projected_area_mm2=round(float(unary_union(B.P0 if sets[name] is None else sets[name]).area), 2),
                    roof_removed_mm3=round(clean_skin.Volume()-patch.Volume(), 2), body_volume_occ_mm3=V(v),
                    valid=v.isValid(), solids=len(v.Solids()), fragments=frag)
        print(name, info, f'{time.time()-t0:.0f}s', flush=True)
        rep[name] = info
        if v.isValid() and len(v.Solids()) == 1:
            cq.exporters.export(v, str(B.OUT/f'BODY_{name}.step'))
    json.dump(rep, open(B.OUT/'variants.json', 'w'), indent=1)

if __name__ == '__main__':
    main(sys.argv[1].split(',') if len(sys.argv) > 1 else ['P0d', 'P1d', 'P7d'])
