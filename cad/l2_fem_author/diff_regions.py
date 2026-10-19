# Where does the released L2 BODY differ from R3.2? Symmetric differences in boxes around the main-key roots / press_B.
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
def vol(s):
    if not s.Solids(): return 0.0
    p = GProp_GProps(); BRepGProp.VolumeProperties_s(s.wrapped, p, 1e-6, True, False); return p.Mass()
def box(x0, x1, y0, y1, z0, z1): return cq.Solid.makeBox(x1-x0, y1-y0, z1-z0, cq.Vector(x0, y0, z0))
r = cq.importers.importBrep(r'D:\Quietmirror_L2\l2_repo_scan\brep\BODY.brep').val()
l = cq.importers.importStep(r'D:\Quietmirror_L2\fem3d\variants\BODY_L2r3.step').val()
for name, b in (('root_-X', box(-30.9, -3.1, 30.1, 46.9, 5.1, 30.9)), ('centre', box(-3, 3, 30, 60, 5, 31)),
                ('pressB_-X_rear', box(-31, -3, 60, 88, 5, 31)), ('rear_+X', box(3, 31, 60, 88, 5, 31)), ('mid_-X', box(-31, -3, 47, 60, 5, 31))):
    try:
        rr = r.intersect(b); ll = l.intersect(b)
    except Exception as e:
        print(name, 'ERR', e); continue
    try:
        rem = rr.cut(ll); add = ll.cut(rr)
    except Exception as e:
        print(name, 'ERR cut', e); continue
    print(f'{name:16s} R32 {vol(rr):8.1f}  L2 {vol(ll):8.1f}  removed {vol(rem):7.2f}  added {vol(add):7.2f}', flush=True)
    for tag, s in (('removed', rem), ('added', add)):
        for q in sorted(s.Solids(), key=lambda q: -vol(q))[:4]:
            if vol(q) > 0.5:
                bb = q.BoundingBox(); print(f'    {tag} {vol(q):7.2f}  X {bb.xmin:.2f}..{bb.xmax:.2f}  Y {bb.ymin:.2f}..{bb.ymax:.2f}  Z {bb.zmin:.2f}..{bb.zmax:.2f}', flush=True)
