"""Compare a final 3MF re-slice against the independent STL+INI slice."""
from pathlib import Path
import json,zipfile,xml.etree.ElementTree as ET,argparse,re
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--version',choices=['0.1','0.2','0.3','0.4','0.5','0.6'],default='0.2');v=ap.parse_args().version
def footer(path):
    out={}
    for line in path.read_text(encoding='utf8').splitlines():
        if line.startswith('; ') and ' = ' in line:
            k,a=line[2:].split(' = ',1);out[k]=a
    return out
a=footer(ROOT/f'.tools/V{v}_estimate_with_support.gcode');b=footer(ROOT/f'.tools/V{v}_3mf_roundtrip.gcode')
suffix='/v'+v.replace('.','') if v!='0.1' else ''
with zipfile.ZipFile(ROOT/f'exports{suffix}/quietmirror_fingertip_V{v}_PRINT.3mf') as z:
    model=ET.fromstring(z.read('3D/3dmodel.model'))
keys='layer_height first_layer_height perimeters top_solid_layers bottom_solid_layers fill_density nozzle_diameter filament_density filament_diameter support_material support_material_style support_material_buildplate_only support_material_contact_distance brim_width external_perimeter_speed temperature'.split()
compare={k:dict(stl_ini=a[k],embedded_3mf=b[k]) for k in keys}
def seconds(t):return sum(int(n)*{'h':3600,'m':60,'s':1}[u] for n,u in re.findall(r'(\d+)([hms])',t))
one=dict(grams=float(a['filament used [g]']),time=a['estimated printing time (normal mode)']);two=dict(grams=float(b['filament used [g]']),time=b['estimated printing time (normal mode)'])
result=dict(configuration_loaded=all(r['stl_ini']==r['embedded_3mf'] for r in compare.values()),method='Final 3MF re-sliced without --load; actual outputs retained independently',unit=model.get('unit'),mesh_triangles=len(model.findall('.//{*}triangle')),comparison=compare,stl_ini_estimate=one,embedded_3mf_estimate=two,difference=dict(grams=round(two['grams']-one['grams'],2),time_seconds=seconds(two['time'])-seconds(one['time'])),note='Small repeat slicing differences retained, not claimed byte-identical')
(ROOT/f'reports{suffix}/3mf_roundtrip.json').write_text(json.dumps(result,indent=2),encoding='utf8')
assert result['configuration_loaded'] and result['unit']=='millimeter'
print(json.dumps(result,indent=2))
