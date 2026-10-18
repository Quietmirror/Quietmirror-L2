"""Check packaged 3MF units/counts, calibration meshes and parameter defaults."""
from pathlib import Path
import json
import zipfile
import xml.etree.ElementTree as ET
import cadquery as cq
import trimesh
import pymeshlab
from mechanisms_v07 import wheel_parts, cartridge, pose
from build_v03 import bounds

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'exports/v07'
p = json.loads((ROOT / 'cad/parameters_v07.json').read_text(encoding='utf8'))
report = {'version': '0.7', 'packages': [], 'calibration': [], 'default_parameter_equivalence': []}
ns = {'m': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
counts = {'PRINT_PLATE': 20, 'MECHANICAL_VIEW_ONLY': 25}
for v in ('ATK_A1_PLUS', 'PAW3950_CUSTOM'):
    data = json.loads((ROOT / 'reports/v07' / (v + '_layout.json')).read_text())
    counts[v + '_VIEW_ONLY'] = 25 + len(data['physical'])
for name, expected in counts.items():
    f = OUT / ('quietmirror_V0.7_' + name + '.3mf')
    with zipfile.ZipFile(f) as z:
        root = ET.fromstring(z.read('3D/3dmodel.model'))
        objects = root.findall('m:resources/m:object', ns)
        items = root.findall('m:build/m:item', ns)
        unit = root.get('unit', 'millimeter')
        assert unit == 'millimeter', (f.name, unit)
        assert len(items) == expected, (f.name, len(items), expected)
        assert len(objects) == expected, (f.name, len(objects), expected)
        report['packages'].append({'file': f.name, 'units': unit, 'objects': len(objects), 'build_items': len(items), 'pass': True})
    print('Package', name, expected, flush=True)

for f in sorted((OUT / 'calibration').glob('*.stl')):
    m = trimesh.load_mesh(f)
    ms = pymeshlab.MeshSet()
    ms.load_new_mesh(str(f))
    ms.compute_selection_by_self_intersections_per_face()
    s = cq.importers.importStep(str(f.with_suffix('.step'))).val()
    r = {'file': f.name, 'cad_valid': s.isValid(), 'solids': len(s.Solids()), 'watertight': m.is_watertight, 'components': len(m.split(only_watertight=False)), 'self_intersecting_faces': ms.current_mesh().selected_face_number()}
    assert r['cad_valid'] and r['solids'] == 1 and r['watertight'] and r['components'] == 1 and r['self_intersecting_faces'] == 0, r
    report['calibration'].append(r)

# Moving the numeric defaults into JSON must not change the shipped shapes.
generated = {k.upper(): v for k, v in wheel_parts(p).items()}
generated['left_TRAY'] = pose(cartridge(p['mechanism'])['tray'], p['modules']['left'])
for name, a in generated.items():
    b = cq.importers.importStep(str(OUT / 'placed' / (name + '.step'))).val()
    delta = abs(a.Volume(tol=1e-9) - b.Volume(tol=1e-9))
    bbox_delta = max(abs(x - y) for x, y in zip(bounds(a), bounds(b)))
    assert delta < 0.001 and bbox_delta < 0.001, (name, delta, bbox_delta)
    report['default_parameter_equivalence'].append({'part': name, 'volume_difference_mm3': delta, 'bounds_max_difference_mm': bbox_delta})
    print('Default parameter equivalence', name, delta, bbox_delta, flush=True)

s = cq.importers.importStep(str(OUT / 'quietmirror_V0.7_MECHANICAL_ASSEMBLY.step')).val()
assert len(s.Solids()) == 25
report['mechanical_step_solids'] = 25
(ROOT / 'reports/v07/package_checks.json').write_text(json.dumps(report, indent=2), encoding='utf8')
print('Package checks passed.', flush=True)
