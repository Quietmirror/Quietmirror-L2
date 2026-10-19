"""Native MeshLab face self-intersection selection on actual final STL meshes."""
from pathlib import Path
import json,importlib.metadata
import numpy as np
import pymeshlab
ROOT=Path(__file__).resolve().parents[2];RP=ROOT/'reports/l2_r4';rows=[]
for name in json.loads((RP/'assembly_inventory.json').read_text())['printable']:
    ms=pymeshlab.MeshSet();ms.load_new_mesh(str(ROOT/'models/L2_r4/parts'/(name+'.stl')))
    ms.compute_selection_by_self_intersections_per_face()
    m=ms.current_mesh();ids=np.flatnonzero(m.face_selection_array())
    rows.append(dict(part=name,faces=m.face_number(),self_intersecting_faces=len(ids),selected_face_ids=ids.tolist(),passed=len(ids)==0))
    (RP/'mesh_self_intersections.json').write_text(json.dumps(dict(library='PyMeshLab '+importlib.metadata.version('pymeshlab'),filter='compute_selection_by_self_intersections_per_face',source='https://pymeshlab.readthedocs.io/en/latest/filter_list.html#compute-selection-by-self-intersections-per-face',parts=rows,passed=len(rows)==9 and all(r['passed'] for r in rows)),indent=2))
    print('MESH_SELF_INTERSECTION',name,len(ids),flush=True)
