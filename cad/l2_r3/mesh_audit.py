"""Inspect numerical tessellation seams; never fill real geometric holes."""
from pathlib import Path
import json
import numpy as np
import trimesh
ROOT=Path(__file__).resolve().parents[2];WORK=ROOT/'_support/work/l2_r3';OUT=ROOT/'models/L2_r3/parts';rows=[]
for n in ['BODY','SIDE_FRONT_KEY','SIDE_REAR_KEY']:
    raw=trimesh.load_mesh(WORK/(n+'_raw.stl'));attempts=[]
    for digits in [7,6,5,4]:
        m=raw.copy();m.merge_vertices(digits_vertex=digits)
        m.update_faces(m.nondegenerate_faces(height=1e-10));m.update_faces(m.unique_faces());m.remove_unreferenced_vertices()
        edges,counts=np.unique(m.edges_sorted,axis=0,return_counts=True);bad=edges[counts!=2]
        points=m.vertices[bad].reshape(-1,3) if len(bad) else np.zeros((0,3))
        row=dict(digits=digits,watertight=bool(m.is_watertight),bad_edges=len(bad),counts={int(c):int(np.sum(counts==c)) for c in np.unique(counts)},bad_bounds=None if not len(points) else [points.min(0).tolist(),points.max(0).tolist()])
        attempts.append(row)
        if m.is_watertight:
            m.export(OUT/(n+'.stl'));row['selected']=True;break
    rows.append(dict(part=n,attempts=attempts));print(n,attempts,flush=True)
(ROOT/'reports/l2_r3/mesh_seam_audit.json').write_text(json.dumps(rows,indent=2))
