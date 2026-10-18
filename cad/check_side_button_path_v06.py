"""Sample a proposed bottom-entry path; not a continuous collision proof."""
from pathlib import Path
import json
import numpy as np
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1]
p=json.loads((ROOT/'cad/parameters_v06.json').read_text())
shell=cq.importers.importStep(str(ROOT/'exports/v06/quietmirror_fingertip_V0.6_SHELL.step')).val()
caps=[cq.importers.importStep(str(ROOT/f'.tools/v06_cap_{i}_placed.step')).val() for i in (1,2)]
results=[]
for i,(cap,b) in enumerate(zip(caps,p['side_buttons'])):
    # Keep absolute entry center at Z=9.2, above the reference sensor frame.
    low_z=9.2-b['z']
    waypoints=np.array([(25,b['y']-28,-30),(25,b['y']-28,low_z),(25,0,low_z),(10,0,low_z),(10,0,0),(0,0,0)],float)
    samples=[]
    for j,(a,z) in enumerate(zip(waypoints,waypoints[1:])):
        for f in np.linspace(0,1,int(np.linalg.norm(z-a)/1.5)+2):
            t=a+(z-a)*f;q=cap.translate(tuple(t));v=shell.copy().intersect(q).Volume()
            # The other cap may already be seated when the second is inserted.
            other=caps[1-i].copy().intersect(q.copy()).Volume()
            samples.append(dict(segment=j,translation_xyz_mm=t.tolist(),shell_overlap_mm3=v,other_cap_overlap_mm3=other))
    result=dict(cap=i+1,method='Discrete CAD intersections at <=1.5 mm path intervals; not swept-volume certification',waypoints_xyz_translation_mm=waypoints.tolist(),sample_count=len(samples),max_shell_overlap_mm3=max(s['shell_overlap_mm3'] for s in samples),max_other_cap_overlap_mm3=max(s['other_cap_overlap_mm3'] for s in samples),samples=samples)
    result['sampled_path_clear']=result['max_shell_overlap_mm3']<1e-4 and result['max_other_cap_overlap_mm3']<1e-4
    results.append(result);print({k:v for k,v in result.items() if k!='samples'},flush=True)
(ROOT/'reports/v06/side_button_insertion.json').write_text(json.dumps(results,indent=2),encoding='utf8')
