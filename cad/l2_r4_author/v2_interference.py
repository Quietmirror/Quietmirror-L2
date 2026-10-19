# Interference of the r4 (V2) BODY additions with every component of the released L2-r3 assembly.
# Additions: side frame fused into BODY, lower cross tie Y56/Z8.6 d2.0, bearing struts (+-9.9, 40.8), Y67.5 tie r1.5.
# Moving groups swept: main keys (axis X @ Y38.5 Z14.32, -0.5..3.1 deg), wheel carrier group (axis X @ Y50 Z19, +-4.4 deg),
# side keys (vertical axes (29,45)/(29,70), 0..7.1 deg).
import json, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
H = Path(__file__).resolve().parent; V = cq.Vector
REPO = next(Path(r'D:\Quietmirror_L2\_support\repo_L2_1ac9de77\x').iterdir())
REF = Path(r'D:\Quietmirror_L2\_support\repo_L2_ab2240f3\x\Quietmirror-L2-ab2240f3\exports\l2_r2_diagnostic\support_reference')
def vol(s):
    if not s.Solids(): return 0.0
    p = GProp_GProps(); BRepGProp.VolumeProperties_s(s.wrapped, p, 1e-6, True, False); return p.Mass()
outer = cq.importers.importStep(str(REF/'MOTHER_OUTER_FROM_R32_SURFACE.step')).val()
def rodx(y, z, r): return cq.Solid.makeCylinder(r, 80, V(-40, y, z), V(1, 0, 0)).intersect(outer)
adds = {'side_frame': cq.importers.importStep(r'D:\Quietmirror_L2\fem3d\variants\R4_SIDE_FRAME_ONLY.step').val(),
        'lower_tie_Y56': rodx(56, 8.6, 1.0),
        'strut_+X': cq.Solid.makeCylinder(1.2, 4.6, V(9.9, 40.8, 7.4)), 'strut_-X': cq.Solid.makeCylinder(1.2, 4.6, V(-9.9, 40.8, 7.4)),
        'Y67.5_tie_r1.5': rodx(67.5, 23.0, 1.5)}
z = zipfile.ZipFile(REPO/'models'/'L2_r3'/'FULL_ASSEMBLY_H.FCStd'); doc = ET.fromstring(z.read('Document.xml'))
work = H/'asm_brep'; work.mkdir(exist_ok=True); comp = {}
for obj in doc.findall('./ObjectData/Object'):
    p = obj.find('./Properties/Property[@name="Shape"]')
    if p is None: continue
    fn = next(iter(p)).attrib.get('file')
    if not fn: continue
    n = obj.attrib['name']; f = work/f'{n}.brep'; f.write_bytes(z.read(fn)); comp[n] = cq.importers.importBrep(str(f)).val()
skip = {'BODY', 'SIDE_SWITCH_CARRIER', 'CARRIER_M2x5_1', 'CARRIER_M2x5_2', 'SIDE_IO_PCB'}   # replaced / removed in r4
main_keys = ['LEFT_KEY', 'RIGHT_KEY']
wheel_grp = ['WHEEL_CARRIER', 'WHEEL', 'ENCODER_ADAPTER_PCB_EST', 'ENCODER_EC10E_HOUSING', 'ENCODER_EC10E_ROTOR', 'ENCODER_M2x3_FRONT', 'ENCODER_M2x3_REAR', 'ENCODER_WASHER_FRONT', 'ENCODER_WASHER_REAR']
side = {'SIDE_FRONT_KEY': ((29, 45), 1), 'SIDE_REAR_KEY': ((29, 70), -1), 'SF_TUNING_SHIM_0p33': ((29, 45), 1), 'SR_TUNING_SHIM_0p33': ((29, 70), -1)}
def swept(n):
    s = comp[n]
    if n in main_keys: return [s.rotate(V(0, 38.5, 14.32), V(1, 38.5, 14.32), a) for a in (-0.5, 0.0, 1.0, 2.0, 2.8, 3.1)], 0.3
    if n in wheel_grp: return [s.rotate(V(0, 50, 19), V(1, 50, 19), a) for a in (-4.4, -2.0, 0.0, 2.0, 4.4)], 0.3
    if n in side: (x, y), sg = side[n]; return [s.rotate(V(x, y, 0), V(x, y, 1), sg*a) for a in (0.0, 2.4, 4.8, 7.1)], 0.3
    return [s], (0.2 if n.endswith('ROUTE_EST') else 0.5)
rows = []
for an, a in adds.items():
    ab = a.BoundingBox()
    for n in comp:
        if n in skip: continue
        poses, need = swept(n)
        for i, s in enumerate(poses):
            b = s.BoundingBox()
            if b.xmin > ab.xmax+2 or b.xmax < ab.xmin-2 or b.ymin > ab.ymax+2 or b.ymax < ab.ymin-2 or b.zmin > ab.zmax+2 or b.zmax < ab.zmin-2: continue
            d = a.distance(s); ov = vol(a.intersect(s)) if d < 1e-6 else 0.0
            intended = (an == 'side_frame' and n in ('SF_D2F_01F', 'SR_D2F_01F'))
            ok = (ov <= 0.001) if intended else (ov <= 0.001 and d >= need - 1e-6)
            rows.append(dict(addition=an, part=n, pose=i, gap_mm=round(d, 4), overlap_mm3=round(ov, 4), need_mm=0 if intended else need, intended_contact=intended, pass_=ok))
worst = {}
for r in rows:
    k = (r['addition'], r['part'])
    if k not in worst or r['gap_mm'] < worst[k]['gap_mm'] or r['overlap_mm3'] > worst[k]['overlap_mm3']: worst[k] = r
fails = [r for r in worst.values() if not r['pass_']]
json.dump(dict(pairs=list(worst.values()), fails=fails), open(H/'v2_interference.json', 'w'), indent=1)
for r in sorted(worst.values(), key=lambda r: r['gap_mm'])[:25]: print(r)
print('FAILS', len(fails)); [print('  FAIL', f) for f in fails]
