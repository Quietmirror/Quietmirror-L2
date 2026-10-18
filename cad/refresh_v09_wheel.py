"""Refresh wheel parts and canonical assemblies after a local wheel edit.

Use build_v09.py for a complete clean build. Always re-run validation afterwards.
"""
from pathlib import Path
from package_steps_v09 import ensure_body_step
ensure_body_step()
import json,time
import cadquery as cq
import trimesh
from build_v09 import print_pose
from mechanisms_v09 import wheel_parts
from export_v09 import save_model

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'exports/v09';RP=ROOT/'reports/v09'
p=json.loads((ROOT/'cad/parameters_v09.json').read_text(encoding='utf8'))
report=json.loads((RP/'cad_metrics.json').read_text(encoding='utf8'))
by_name={a['name']:a for a in report['parts']}
for n,s in wheel_parts(p).items():
    name=n.upper();old=by_name[name]
    a=save_model(s,name,OUT/'placed');flat=save_model(print_pose(s,name,p),name,OUT/'print')
    for key in ('kind','module','color','print_quantity','file','print_file'):a[key]=old[key]
    a['print_bounds']=flat['bounds'];by_name[name]=a
    print('Refreshed',name,flush=True)
report['parts']=[by_name[a['name']] for a in report['parts']]
report['parameters']=p
report['wheel_refresh']='Lowered axis Z13.0; lower crossbar D26.9, length 4.2, to clear the wheel and the insertion guide.'
assy=cq.Assembly(name='QUIETMIRROR_V09_MECHANICAL_TEST');scene=trimesh.Scene()
objects=[(a['name'],a['color']) for a in report['parts']]+[(n+'_SWITCH_EXAMPLE',[.76,.31,.21]) for n in p['modules']]
for name,color in objects:
    shape=cq.importers.importStep(str(OUT/'placed'/(name+'.step'))).val()
    assy.add(shape,name=name,color=cq.Color(*color))
    mesh=trimesh.load_mesh(OUT/'placed'/(name+'.stl'));mesh.visual.face_colors=[int(c*255) for c in color]+[255];scene.add_geometry(mesh,node_name=name)
assy.save(str(OUT/'quietmirror_V0.9_MECHANICAL_ASSEMBLY.step'),write_pcurves=False)
scene.units='mm';(OUT/'quietmirror_V0.9_MECHANICAL_VIEW_ONLY.3mf').write_bytes(trimesh.exchange.threemf.export_3MF(scene))
(RP/'cad_metrics.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
print('Wheel and mechanical assembly refreshed.',flush=True)
