"""Shorten only the five R3 pad supports to the reserved lower lens datum."""
from pathlib import Path
import sys,json,shutil,ctypes,importlib.util
import cadquery as cq
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
BASE=ROOT/'exports/rebuild_r3';OUT=ROOT/'exports/rebuild_r3_1';RP=ROOT/'reports/rebuild_r3_1'
sys.path.insert(0,str(ROOT/'cad/rebuild_r2'))
from mechanics import cylinder,box,join,check
spec=importlib.util.spec_from_file_location('r2_exporter',ROOT/'cad/rebuild_r2/build.py')
exporter=importlib.util.module_from_spec(spec);spec.loader.exec_module(exporter)

def dump(n,d):
    (RP/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
    ctypes.windll.kernel32.SetPriorityClass(ctypes.c_void_p(-1),0x4000)
    OUT.mkdir(parents=True,exist_ok=True);RP.mkdir(parents=True,exist_ok=True)
    p=json.loads((HERE/'parameters.json').read_text())
    for folder in ('assembly','print','gauges','electronics'):
        shutil.copytree(BASE/folder,OUT/folder,dirs_exist_ok=True)
    met=json.loads((ROOT/'reports/rebuild_r3/cad_metrics.json').read_text())
    d=json.loads((ROOT/'reports/rebuild_r3/design_metadata.json').read_text())
    old=cq.importers.importStep(str(BASE/'assembly/BODY.step')).val()
    reservation=cq.importers.importStep(str(BASE/'gauges/SENSOR_RESERVED_VOLUME.step')).val()
    z=p['foot_contact_z_mm'];r=p['foot_diameter_mm']/2;h=p['foot_land_thickness_mm']
    assert abs(z-reservation.BoundingBox().zmin)<1e-6,'Datum must match actual exported reservation'
    feet=d['mechanisms']['feet']
    local=join(*[cylinder(p['edit_radius_mm'],z+6,(*f['center'],-5)) for f in feet])
    lower=box(150,150,z+5,(0,44,(z-5)/2))
    new=old.cut(lower.intersect(local))
    for f in feet:new=new.fuse(cylinder(r,h,(*f['center'],z)))
    # Retain exact Boolean split faces. UnifySameDomain (.clean()) merges a
    # rear disk/brace cylinder into a face that fails STEP roundtrip orientation.
    # No geometry approximation or mesh patching is used to avoid that issue.
    new=check(new,'R3_1_BODY')
    exporter.OUT=OUT;exporter.REPORT=RP
    exporter.CACHE=ROOT.parent/'_support/work/fenrir_rebuild_r3_1/build';exporter.CACHE.mkdir(parents=True,exist_ok=True)
    exporter.export('BODY',new,True,met)
    back=cq.importers.importStep(str(OUT/'assembly/BODY.step')).val()
    assert back.isValid() and len(back.Solids())==1,'BODY STEP roundtrip must remain a valid solid'
    d['parameters']['version']='R3.1'
    d['parameters']['coordinates']=p['coordinates']
    d['parameters']['feet'].update(height=h,contact_z=z)
    for f in feet:
        f.update(contact_z=z,pad_top_z=z+h,load_path='Shortened disk and retained upper stem/brace, joined to BODY')
    d['mechanisms']['open_bottom']='Five shortened pad lands at the reserved lower datum; R3 frame outside local pad prisms is unchanged. Apply measured skates for ground clearance.'
    d['r3_1_scope']=p
    dump('cad_metrics.json',met);dump('design_metadata.json',d)
    dump('change_scope.json',dict(base='R3',modified=['BODY'],unchanged=[n for n in met if n!='BODY'],
        old_contact_z_mm=0,new_contact_z_mm=z,shortened_mm=z,diameter_mm=2*r,land_thickness_mm=h,
        reference_gauge='SENSOR_RESERVED_VOLUME',reference_bottom_z_mm=reservation.BoundingBox().zmin,
        volume_method='Adaptive volume is reported by thickness_check.py. Global coincident-face difference is not used as an acceptance check.',
        upper_shell_and_keys_preserved=True,optical_working_distance_verified=False))
    electronic=json.loads((ROOT/'cad/rebuild_r3/electronics.json').read_text())
    electronic['optics'].update(foot_contact_z_mm=z,equation='lens_bottom_to_pad = lens_lowest_z - foot_contact_z + actual_skate_thickness; solve from measured lens and board stack.')
    (HERE/'electronics.json').write_text(json.dumps(electronic,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('R3.1 BODY exported; five lands Z=',z,'height=',h,'volume=',new.Volume(),flush=True)

if __name__=='__main__':main()
