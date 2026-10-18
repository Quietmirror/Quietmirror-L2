"""Restore complete original foot primitives after lower-skin reconstruction.

Incremental release helper; clean builds include this in build_v09.py.
"""
from pathlib import Path
import json,shutil
import cadquery as cq
import trimesh,pymeshlab
from build_v09 import preserve_lower_interfaces
from build_v03 import bounds
from export_v09 import save_model
from validate_v09 import overlap

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'exports/v09';RP=ROOT/'reports/v09'
p=json.loads((ROOT/'cad/parameters_v09.json').read_text(encoding='utf8'))
info=json.loads((RP/'cad_metrics.json').read_text(encoding='utf8'))
old=cq.Shape.importBrep(str(ROOT/'.tools/v09_final_BODY.brep'))
body=preserve_lower_interfaces(p,old,None)
added=[];feet=[]
positions=[(-21,-8),(21,-8),(-21.5,-61.5),(21.5,-61.5),(0,-81.5)]
for x,y in positions:
    foot=cq.Workplane('XY').center(x,y).circle(4.4).extrude(2.4).edges('>Z').fillet(.35).val()
    delta=foot.cut(old,tol=1e-5)
    if delta.Solids():added.append(delta)
    missing=foot.cut(body,tol=1e-5).Volume(tol=1e-6)
    feet.append(dict(x=x,y=y,diameter_mm=8.8,height_mm=2.4,upper_fillet_mm=.35,missing_mm3=missing))
assert all(a['missing_mm3']<.001 for a in feet),feet
addition=cq.Compound.makeCompound(added)
minima=[]
for row in info['parts']:
    if row['name']=='BODY':continue
    s=cq.importers.importStep(str(OUT/'placed'/(row['name']+'.step'))).val()
    low=bounds(s)[2]-p['mechanism']['travel']
    minima.append(dict(part=row['name'],conservative_lowest_z_mm=low))
assert min(x['conservative_lowest_z_mm'] for x in minima)>2.4
electronics=[]
for variant in ('ATK_A1_PLUS','PAW3950_CUSTOM'):
    layout=json.loads((RP/(variant+'_layout.json')).read_text(encoding='utf8'))
    for item in layout['physical']:
        s=cq.importers.importStep(str((ROOT/item['file']).with_suffix('.step'))).val()
        vol=overlap(addition,s)
        electronics.append(dict(variant=variant,part=item['name'],overlap_mm3=vol))
assert all(x['overlap_mm3']<.01 for x in electronics)
record=save_model(body,'BODY',OUT/'placed')
for suffix in ('.stl','.step'):shutil.copyfile(OUT/'placed'/('BODY'+suffix),OUT/'print'/('BODY'+suffix))
ms=pymeshlab.MeshSet();ms.load_new_mesh(str(OUT/'placed/BODY.stl'));ms.compute_selection_by_self_intersections_per_face()
assert ms.current_mesh().selected_face_number()==0
oldrow=next(x for x in info['parts'] if x['name']=='BODY')
for key in ('kind','color','print_quantity','file','print_file'):record[key]=oldrow[key]
record['print_bounds']=record['bounds']
info['parts']=[record if x['name']=='BODY' else x for x in info['parts']];info['parameters']=p
(RP/'cad_metrics.json').write_text(json.dumps(info,indent=2,ensure_ascii=False),encoding='utf8')
reference=cq.importers.importStep(str(ROOT/'exports/v08/placed/BODY.step')).val()
regions=[]
for x,y in positions:
    region=cq.Solid.makeCylinder(4.4,2.4,cq.Vector(x,y,0));a=reference.intersect(region);b=body.intersect(region)
    regions.append(dict(name=f'foot_{x}_{y}',difference_mm3=a.cut(b,tol=1e-5).Volume(tol=1e-6)+b.cut(a,tol=1e-5).Volume(tol=1e-6),note='Bounding cylinder also contains the rebuilt adjacent skin; exact filleted-foot containment is tested separately.'))
for name,w,l,y in [('sensor',22,26,-48),('power_switch',12,8,-72)]:
    region=cq.Workplane('XY').box(w,l,5.4).val().translate((0,y,2.7));a=reference.intersect(region);b=body.intersect(region)
    regions.append(dict(name=name,difference_mm3=a.cut(b,tol=1e-5).Volume(tol=1e-6)+b.cut(a,tol=1e-5).Volume(tol=1e-6)))
r=dict(exact_platforms=feet,added_volume_mm3=addition.Volume(tol=1e-6),added_material_maximum_z_mm=2.4,conservative_mechanical_minima=minima,electronic_checks=electronics,protected_regions=regions,method='Restore the original R4.4 x 2.4 mm platforms with R0.35 top fillets. Added material is below all mechanical parts and their conservative downward stroke; it cannot affect the tested upward/side insertion paths. Electronic envelopes are checked against the additions explicitly. No material was removed.')
(RP/'platform_restoration.json').write_text(json.dumps(r,indent=2),encoding='utf8')
print('Platforms restored and checked',r['added_volume_mm3'],flush=True)
