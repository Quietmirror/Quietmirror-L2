"""Compare saved V0.5 vs released V0.3 geometry, not build-time assertions."""
from pathlib import Path
import json
import cadquery as cq
import numpy as np
import trimesh
from build_v03 import bounds
from validate_mouse import ray_distances

ROOT=Path(__file__).resolve().parents[1]
p=json.loads((ROOT/'cad/parameters_v05.json').read_text())
z=p['frozen_bottom']['through_z_mm']
clip=cq.Workplane('XY').box(240,300,60).val().translate((0,-50,z-30))
results=[]
for variant in ('FIT','SHELL'):
    paths=[ROOT/f'exports/v0{v}/quietmirror_fingertip_V0.{v}_{variant}.step' for v in (3,5)]
    shapes=[cq.importers.importStep(str(path)).val().intersect(clip.copy()) for path in paths]
    a,b=shapes
    vols=[s.Volume(tol=1e-7) for s in shapes]
    removed=a.copy().cut(b.copy()).Volume(tol=1e-7)
    added=b.copy().cut(a.copy()).Volume(tol=1e-7)
    common=a.copy().intersect(b.copy()).Volume(tol=1e-7)
    item=dict(variant=variant,source=str(paths[0].relative_to(ROOT)),new=str(paths[1].relative_to(ROOT)),through_z_mm=z,volumes_mm3=vols,old_minus_new_mm3=removed,new_minus_old_mm3=added,common_mm3=common,bounds_xyz_mm=[bounds(s) for s in shapes],valid=[s.isValid() for s in shapes])
    assert min(vols)>6000 and abs(common-vols[0])<.002,item
    assert removed<1e-5 and added<1e-5 and all(item['valid']),item
    results.append(item)
    if variant=='FIT':
        for i,shape in enumerate(shapes):shape.exportStl(str(ROOT/f'.tools/v05_bottom_check_{i}.stl'),tolerance=.02,angularTolerance=.15,relative=False)

# Record the small freeform-skirt transition at the exact freeze plane.
m=trimesh.load_mesh(ROOT/'exports/v05/quietmirror_fingertip_V0.5_FIT.stl')
seams=[]
for d in np.linspace(3,79,39):
    r=ray_distances(m,[[-40,-d,z-.01],[-40,-d,z+.01]],[[1,0,0],[1,0,0]])
    if all(len(a)>1 for a in r):
        old=[r[0][0],r[0][-1]];new=[r[1][0],r[1][-1]]
        seams.append(dict(from_front_mm=float(d),outer_edge_change_mm=max(abs(a-b) for a,b in zip(old,new))))
max_seam=max(s['outer_edge_change_mm'] for s in seams)
report=dict(version='0.5',method='Saved STEP Boolean differences in complete Z<=6 mm slab; independent mesh ray skirt sampling above/below joint',tolerance_volume_mm3=1e-5,comparisons=results,skirt_joint=dict(z_mm=z,sampling_delta_z_mm=.01,sample_count=len(seams),max_sampled_outer_edge_change_mm=max_seam,samples=seams),note='Bottom lock includes the five pads, full rib network, sensor frame, right lip and wheel roots. Mesh triangulation may differ. Only manufacturing and adhesion can establish physical coplanarity.')
(ROOT/'reports/v05/bottom_preservation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k!='skirt_joint'},indent=2))
print('Maximum sampled skirt edge change:',max_seam)
assert max_seam<.2,'Inspect the skirt joint: exceeds 0.2 mm'
