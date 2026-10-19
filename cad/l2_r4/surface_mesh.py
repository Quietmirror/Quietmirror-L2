import numpy as np
"""Conforming surface mesh from final STEP, without hole filling."""
import json
from pathlib import Path
import gmsh,trimesh
ROOT=Path(__file__).resolve().parents[2];WORK=ROOT/'_support/work/l2_r4/surface_mesh';OUT=ROOT/'models/L2_r4/parts';RP=ROOT/'reports/l2_r4'
def main(selected_parts=None):
    WORK.mkdir(parents=True,exist_ok=True);rows=[]
    for n in selected_parts or ['BODY','LEFT_KEY','RIGHT_KEY','SIDE_FRONT_KEY','SIDE_REAR_KEY','SF_RETAINER','SR_RETAINER','WHEEL_CARRIER']:
        gmsh.initialize();gmsh.option.setNumber('General.Terminal',0)
        try:
            gmsh.model.occ.importShapes(str(OUT/(n+'.step')));gmsh.model.occ.synchronize()
            for k,v in {'Mesh.MeshSizeMin':.10,'Mesh.MeshSizeMax':.60,'Mesh.MeshSizeFromCurvature':32,'Mesh.Algorithm':6,'Mesh.ElementOrder':1,'Mesh.Binary':1,'General.NumThreads':1}.items():gmsh.option.setNumber(k,v)
            gmsh.model.mesh.generate(2);gmsh.write(str(WORK/(n+'.stl')))
        finally:gmsh.finalize()
        m=trimesh.load_mesh(WORK/(n+'.stl'));m.merge_vertices(digits_vertex=6);m.update_faces(m.nondegenerate_faces(height=1e-9));m.update_faces(m.unique_faces());m.remove_unreferenced_vertices()
        row=dict(part=n,watertight=bool(m.is_watertight),winding_consistent=bool(m.is_winding_consistent),components=len(trimesh.graph.connected_components(m.face_adjacency,nodes=np.arange(len(m.faces)),engine='scipy',min_len=1)),triangles=len(m.faces),method='Conforming final STEP surface triangulation; no hole filling')
        row['passed']=row['watertight'] and row['winding_consistent'] and row['components']==1
        rows.append(row);(RP/'surface_mesh_checks.json').write_text(json.dumps(rows,indent=2));print(row,flush=True)
        if not row['passed']:raise RuntimeError('Final surface mesh failed '+n)
        m.export(OUT/(n+'.stl'))
if __name__=='__main__':main()
