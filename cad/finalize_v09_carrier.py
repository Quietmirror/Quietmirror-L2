"""Incremental V0.9 carrier check after the complete pre-shortening check.

Fresh reproduction should run validate_v09.py instead. This records why the
four already-passing key insertion paths remain valid after material removal.
"""
from pathlib import Path
import copy,json
import numpy as np
import cadquery as cq
import trimesh,pymeshlab
from package_steps_v09 import ensure_body_step
from mechanisms_v09 import wheel_parts
from validate_v09 import overlap,insertion_check

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'exports/v09';RP=ROOT/'reports/v09'

def main():
    ensure_body_step()
    p=json.loads((ROOT/'cad/parameters_v09.json').read_text(encoding='utf8'))
    report=json.loads((RP/'validation.json').read_text(encoding='utf8'))
    assert report['topology_pass'] and report['rigid_motion_pass'] and not report['static_intersections']
    assert all(x['pass_check'] for x in report['insertion_paths'] if x['part']!='WHEEL_CARRIER')
    before=copy.deepcopy(p);before['wheel'].update(carrier_lower_crossbar_length=5.0,carrier_lower_crossbar_d=27.3)
    old=wheel_parts(before)['wheel_carrier']
    new=cq.importers.importStep(str(OUT/'placed/WHEEL_CARRIER.step')).val()
    added=new.cut(old).Volume(tol=1e-7)
    removed=old.cut(new).Volume(tol=1e-7)
    assert added<.001 and removed>0,(added,removed)
    print('Carrier material added/removed',added,removed,flush=True)
    info=json.loads((RP/'cad_metrics.json').read_text(encoding='utf8'))
    shapes={a['name']:cq.importers.importStep(str(OUT/'placed'/(a['name']+'.step'))).val() for a in info['parts']}
    clip=cq.Workplane('XY').box(22,40,60).val().translate((0,-25,30))
    local=shapes['BODY'].intersect(clip)
    poses=[]
    for d in np.linspace(0,p['mechanism']['travel'],9):
        moved=new.translate((0,0,-float(d)));hits=[]
        for n,s in shapes.items():
            if n in ('WHEEL_CARRIER','WHEEL','AXLE','AXLE_WASHER','DETENT_LEAF','middle_RETAINER'):continue
            vol=overlap(moved,local if n=='BODY' else s)
            if vol>.01:hits.append(dict(part=n,overlap_mm3=vol))
        poses.append(dict(travel_mm=float(d),hits=hits))
    # The other members of the middle moving group have not changed.
    assert all(not x['hits'] for x in poses)
    contacts=[]
    for n,s in shapes.items():
        if n=='WHEEL_CARRIER':continue
        vol=overlap(new,local if n=='BODY' else s)
        if vol>.01:contacts.append(dict(part=n,overlap_mm3=vol))
    assert not contacts,contacts
    insert=insertion_check(('WHEEL_CARRIER',()))
    print('New wheel insertion',insert['pass_check'],flush=True)
    assert insert['pass_check'],insert
    report['insertion_paths']=[insert if x['part']=='WHEEL_CARRIER' else x for x in report['insertion_paths']]
    mesh=trimesh.load_mesh(OUT/'placed/WHEEL_CARRIER.stl')
    ms=pymeshlab.MeshSet();ms.load_new_mesh(str(OUT/'placed/WHEEL_CARRIER.stl'));ms.compute_selection_by_self_intersections_per_face()
    row=dict(name='WHEEL_CARRIER',cad_valid=new.isValid(),solids=len(new.Solids()),watertight=mesh.is_watertight,winding_consistent=mesh.is_winding_consistent,components=len(mesh.split(only_watertight=False)),self_intersecting_faces=ms.current_mesh().selected_face_number(),dimensions_xyz_mm=mesh.extents.tolist(),volume_mm3=mesh.volume)
    assert row['cad_valid'] and row['solids']==1 and row['watertight'] and row['winding_consistent'] and row['components']==1 and row['self_intersecting_faces']==0,row
    report['topology']=[row if x['name']=='WHEEL_CARRIER' else x for x in report['topology']]
    core=cq.importers.importStep(str(ROOT/'.tools/v09_core_only.step')).val()
    missing=core.cut(shapes['BODY']).Volume(tol=1e-7)
    assert missing<.001,missing
    assert all(x['difference_mm3']<.001 for x in report['protected_lower_interfaces'] if not x['name'].startswith('foot_'))
    platform=json.loads((RP/'platform_restoration.json').read_text(encoding='utf8'))
    assert all(x['missing_mm3']<.001 for x in platform['exact_platforms'])
    report['exact_foot_platforms']=platform['exact_platforms']
    report['platform_restoration']=platform
    report['base_symmetric_difference_mm3']=None
    report['base_comparison_method']='Local sensor/switch interface differences, framework containment and exact original filleted foot containment. Full coincident-shell symmetric difference is not used.'
    report['protected_lower_interfaces']=platform['protected_regions']
    assert all(x['full_press_tip_to_body_mm']>.25 for x in report['front_key_clearance'])
    assert report['main_to_front_side_longitudinal_gap_mm']>2*p['mechanism']['radial_clearance']
    assert all(x['samples']==9 and abs(x['min_z'])<.001 and abs(x['max_z'])<.001 for x in report['feet'])
    assert all(not x['rest_intersections'] for x in report['switch_example_rest_fit'])
    proof=dict(previous_crossbar=dict(length_mm=5,center_d_mm=27.3),final_crossbar=dict(length_mm=4.2,center_d_mm=26.9),added_material_mm3=added,removed_material_mm3=removed,static_contacts=contacts,rechecked_middle_carrier_poses=poses,new_wheel_insertion_pass=True,method='Only the lower crossbar was shortened. New carrier is a Boolean-proven subset of the tested carrier. The four unchanged key insertion paths were tested against the larger carrier; their zero-intersection result therefore remains conservative. Wheel group insertion was rerun at all 31 positions. Other parts, wheel annulus, hardware and body are unchanged.')
    report['carrier_revision']=proof
    report['preserved_framework_missing_mm3']=missing
    report['base_change_note']='Lower side skin rebuilt with 1.6 mm parent loft; internal frame, feet, sensor and switch structures retained.'
    (RP/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    (RP/'carrier_revision.json').write_text(json.dumps(proof,indent=2),encoding='utf8')
    bodymesh=trimesh.load_mesh(OUT/'placed/BODY.stl');bm=pymeshlab.MeshSet();bm.load_new_mesh(str(OUT/'placed/BODY.stl'));bm.compute_selection_by_self_intersections_per_face()
    assert bodymesh.is_watertight and len(bodymesh.split(only_watertight=False))==1 and bm.current_mesh().selected_face_number()==0
    for a in report['topology']:
        if a['name']=='BODY':a.update(volume_mm3=bodymesh.volume,dimensions_xyz_mm=bodymesh.extents.tolist())
    (RP/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    info['parameters']=p
    (RP/'cad_metrics.json').write_text(json.dumps(info,indent=2,ensure_ascii=False),encoding='utf8')
    for variant in ('ATK_A1_PLUS','PAW3950_CUSTOM'):
        layout=json.loads((RP/(variant+'_layout.json')).read_text(encoding='utf8'))
        assert layout['static_and_sampled_motion_pass']
        checks=[]
        for part in layout['physical']:
            s=cq.importers.importStep(str((ROOT/part['file']).with_suffix('.step'))).val()
            hits=[]
            for d in np.linspace(0,p['mechanism']['travel'],9):
                vol=overlap(new.translate((0,0,-float(d))),s)
                if vol>.01:hits.append(dict(travel_mm=float(d),overlap_mm3=vol))
            checks.append(dict(part=part['name'],hits=hits))
        assert all(not x['hits'] for x in checks)
        layout['carrier_revision_recheck']=dict(subset_added_material_mm3=added,checks=checks,unchanged_components='All other saved shapes and envelopes unchanged.')
        assembly=cq.Assembly(name=variant+'_ESTIMATED_SPACE_STUDY');scene=trimesh.Scene()
        objects=[(a['name'],OUT/'placed'/(a['name']+'.step'),a['color']) for a in info['parts'] if a['name'] in layout['mechanical_parts']]
        objects += [(m+'_SWITCH_EXAMPLE',OUT/'placed'/(m+'_SWITCH_EXAMPLE.step'),[.76,.31,.21]) for m in p['modules']]
        objects += [(a['name'],(ROOT/a['file']).with_suffix('.step'),a['color']) for a in layout['physical']]
        for name,path,color in objects:
            s=shapes[name] if name in shapes else cq.importers.importStep(str(path)).val()
            assembly.add(s,name=name,color=cq.Color(*color))
            m=trimesh.load_mesh(path.with_suffix('.stl'));m.visual.face_colors=[int(c*255) for c in color]+[255];scene.add_geometry(m,node_name=name)
        assembly.save(str(OUT/f'quietmirror_V0.9_{variant}_ESTIMATED.step'),write_pcurves=False)
        scene.units='mm';(OUT/f'quietmirror_V0.9_{variant}_VIEW_ONLY.3mf').write_bytes(trimesh.exchange.threemf.export_3MF(scene))
        (RP/(variant+'_layout.json')).write_text(json.dumps(layout,indent=2),encoding='utf8')
        print('Electronic scene refreshed',variant,flush=True)
    assembly=cq.Assembly(name='QUIETMIRROR_V09_MECHANICAL_TEST');scene=trimesh.Scene()
    objects=[(a['name'],a['color']) for a in info['parts']]+[(m+'_SWITCH_EXAMPLE',[.76,.31,.21]) for m in p['modules']]
    for name,color in objects:
        path=OUT/'placed'/(name+'.step');s=shapes[name] if name in shapes else cq.importers.importStep(str(path)).val()
        assembly.add(s,name=name,color=cq.Color(*color));m=trimesh.load_mesh(path.with_suffix('.stl'));m.visual.face_colors=[int(c*255) for c in color]+[255];scene.add_geometry(m,node_name=name)
    assembly.save(str(OUT/'quietmirror_V0.9_MECHANICAL_ASSEMBLY.step'),write_pcurves=False)
    scene.units='mm';(OUT/'quietmirror_V0.9_MECHANICAL_VIEW_ONLY.3mf').write_bytes(trimesh.exchange.threemf.export_3MF(scene))
    print('Final carrier and all report assertions passed.',flush=True)

if __name__=='__main__':main()
