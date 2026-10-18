"""Validate saved multi-part electronics exports without fusing assemblies."""
from pathlib import Path
import json,zipfile,xml.etree.ElementTree as ET
import cadquery as cq
import trimesh,pymeshlab
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'exports/v06';result=[]
for variant in ('ATK_A1_PLUS','PAW3950_CUSTOM'):
    stem=f'quietmirror_V0.6_{variant}_ESTIMATED'
    s=cq.importers.importStep(str(out/(stem+'.step'))).val()
    with zipfile.ZipFile(out/(stem+'_VIEW_ONLY.3mf')) as z:
        name=next(n for n in z.namelist() if n.endswith('.model'));doc=ET.fromstring(z.read(name))
        unit=doc.get('unit');objects=len(doc.findall('.//{*}object'))
    components=[]
    for path in sorted((out/variant).glob('*.stl')):
        m=trimesh.load_mesh(path);ms=pymeshlab.MeshSet();ms.load_new_mesh(str(path));ms.compute_selection_by_self_intersections_per_face()
        r=dict(file=path.name,watertight=m.is_watertight,winding_consistent=m.is_winding_consistent,components=len(m.split(only_watertight=False)),self_intersecting_faces=ms.current_mesh().selected_face_number())
        assert r['watertight'] and r['winding_consistent'] and r['components']==1 and r['self_intersecting_faces']==0,r
        components.append(r)
    assert s.isValid() and all(a.isValid() for a in s.Solids()) and unit=='millimeter'
    report=json.loads((ROOT/f'reports/v06/{variant}_layout.json').read_text())
    result.append(dict(variant=variant,cad_valid=s.isValid(),cad_solids=len(s.Solids()),view_3mf_unit=unit,view_3mf_objects=objects,component_meshes=components,unintended_physical_overlaps=[a for a in report['component_overlaps'] if not a['intended_interface']],shell_overlap_count=sum(a['shell_overlap_mm3']>.01 or a['caps_overlap_mm3']>.01 for a in report['physical']),note='Assembly is intentionally multiple parts and has interfacing wheel/shaft/slider volumes. No single-solid assertion for electronics scenes.'))
(ROOT/'reports/v06/electronics_validation.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps([{k:v for k,v in a.items() if k!='component_meshes'} for a in result],indent=2))
