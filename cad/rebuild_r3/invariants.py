"""Check unchanged R2 interfaces and record the deliberately blocked donor scene."""
from pathlib import Path
import sys,json,ctypes
import cadquery as cq
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'exports/rebuild_r3';RP=ROOT/'reports/rebuild_r3'
sys.path.insert(0,str(ROOT/'cad/rebuild_r2'))
from mechanics import box
from mesh_motion import from_mesh,intersection
import trimesh

def main():
    ctypes.windll.kernel32.SetPriorityClass(ctypes.c_void_p(-1),0x4000)
    old=cq.importers.importStep(str(ROOT/'exports/rebuild_r2/assembly/BODY.step')).val()
    new=cq.importers.importStep(str(OUT/'assembly/BODY.step')).val()
    band=box(120,120,5,(0,44,2.5));a=old.intersect(band);b=new.intersect(band)
    difference=a.cut(b).Volume()+b.cut(a).Volume()
    names=['LEFT_KEY','RIGHT_KEY','SIDE_FRONT_KEY','SIDE_REAR_KEY','WHEEL','LEFT_KEY_STEEL_PIN','RIGHT_KEY_STEEL_PIN','WHEEL_CARRIER_STEEL_PIN','SWITCH_LEFT','SWITCH_RIGHT','SWITCH_MIDDLE','SWITCH_SIDE_FRONT','SWITCH_SIDE_REAR','USB_C_REFERENCE']
    same={n:(ROOT/f'exports/rebuild_r2/assembly/{n}.step').read_bytes()==(OUT/f'assembly/{n}.step').read_bytes() for n in names}
    report=dict(exact_bottom_band_symmetric_difference_mm3=difference,byte_identical_STEP_parts=same,
        pass_check=difference<1e-6 and all(same.values()),scope='BODY Z0..5 exact Boolean comparison plus unchanged functional references. R2 FEM is not re-certified for the modified BODY.')
    (RP/'preserved_interfaces.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    assert report['pass_check']
    d=from_mesh(trimesh.load_mesh(OUT/'electronics/donor_blocked/UNMEASURED_DONOR_SLAB.stl'))
    metrics=json.loads((RP/'cad_metrics.json').read_text());hits=[]
    for n in metrics:
        q=from_mesh(trimesh.load_mesh(OUT/f'assembly/{n}.stl'));v=intersection(d,q)
        if v>.01:hits.append(dict(part=n,overlap_mm3=v))
    donor=dict(assumed_size_mm=[36,50,1.2],assumed_center_mm=[0,40,5.4],actual_ATK_board_measured=False,
        conflicts=hits,fit_pass=False,diagnostic_expected_failure=bool(hits),
        interpretation='The historical guessed slab does not fit this placement. 780-position R2 scan also had no clear result, but neither proves every real donor outline or orientation impossible. Do not cut a populated donor PCB.')
    (RP/'blocked_donor_check.json').write_text(json.dumps(donor,indent=2),encoding='utf8')
    print('Invariants',report['pass_check'],'low-band difference',difference,'donor conflicts',hits,flush=True)
if __name__=='__main__':main()
