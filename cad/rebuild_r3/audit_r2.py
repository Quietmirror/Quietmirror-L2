"""Audit unmodelled R2 interfaces before making any R3 correction (mm)."""
from pathlib import Path
import sys,json,math,ctypes
import numpy as np
import trimesh
import manifold3d as md

ROOT=Path(__file__).resolve().parents[2]
RP=ROOT/'reports/rebuild_r3';RP.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'cad/rebuild_r2'))
from mesh_motion import from_mesh,intersection,matrix

def cube(size,center):
    return md.Manifold.cube(size,True).translate(center)

def main():
    ctypes.windll.kernel32.SetPriorityClass(ctypes.c_void_p(-1),0x4000)
    metrics=json.loads((ROOT/'reports/rebuild_r2/cad_metrics.json').read_text())
    design=json.loads((ROOT/'reports/rebuild_r2/design_metadata.json').read_text())
    models={n:from_mesh(trimesh.load_mesh(ROOT/f'exports/rebuild_r2/assembly/{n}.stl')) for n in metrics}
    # Small minimum-clearance gauge is additive to each side, not a mass solid.
    def clashes(m):
        return {n:round(v,5) for n,q in models.items() if (v:=intersection(m,q))>.01}
    strokes=[]
    for m in design['mechanisms']['motions']:
        n=m['part'];q=np.array(m['actuation_point'],float);gap=m['nominal_actuator_gap_mm']
        if m['kind']=='translate':
            normal=-np.array(m['end_vector'])/np.linalg.norm(m['end_vector'])
        else:
            angle=math.radians(m.get('switch_tilt_deg',0))
            normal=np.array([0,-math.sin(angle),math.cos(angle)])
        tip=q-gap*normal;mat=matrix(m,1.)
        qp=mat[:3,:3]@q+mat[:3,3];np_=mat[:3,:3]@normal
        depression=np.dot(np_,tip-qp)/np.dot(np_,normal)
        contact=tip-depression*normal
        offset=np.linalg.norm(contact-qp)
        strokes.append(dict(part=n,axis_projected_stroke_mm=float(depression),
            old_reported_stroke_mm=m.get('calculated_contact_travel_mm',m.get('hard_stop_travel_mm',0)-gap),
            pad_contact_offset_mm=float(offset),PT_max_mm=.5,
            PT_headroom_mm=float(depression-.5),free_position_is_estimate=True))
    # Do not assume the old donor's fictitious wheel cutout exists.
    old_board=cube([36,50,1.2],[0,40,5.4])
    examples={
        'old_ATK_slab_into_R2':dict(size=[36,50,1.2],center=[0,40,5.4],collisions=clashes(old_board)),
        'encoder_pcb_uncut':dict(size=[10,16,1.2],center=[6.4,28,9.8],collisions=clashes(cube([10,16,1.2],[6.4,28,9.8]))),
    }
    # Scan only the explicitly bounded simple translation grid, not all possible
    # rotated PCB placements or arbitrary board outlines. Expanded slab includes
    # .25mm per-side assembly clearance, but no tall components yet.
    scan=[]
    for w,l,angle in [(36,50,0),(50,36,90)]:
        best=None
        for x in (-6.,0.,6.):
            for y in np.arange(28.,64.1,4.):
                for z in np.arange(5.6,18.1,1.):
                    b=cube([w+.5,l+.5,1.7],[x,float(y),float(z)])
                    hits=clashes(b);total=sum(hits.values())
                    row=dict(angle_deg=angle,center=[x,float(y),float(z)],overlap_sum_mm3=total,conflicts=hits)
                    if best is None or total<best['overlap_sum_mm3']:best=row
        scan.append(best)
    report=dict(strokes=strokes,additional_component_examples=examples,donor_bounded_scan=scan,
        donor_scan_scope='780 positions: X=-6/0/6, Y=28..64 step4, Z=5.6..17.6 step1; 0/90deg. This scan alone does not prove impossibility or actual ATK dimensions.',
        original_model='R2 exported meshes, absolute chord .025 mm',threshold_mm3=.01)
    (RP/'R2_missing_interface_audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':main()
