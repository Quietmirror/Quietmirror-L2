"""Conforming Gmsh surface triangulation fallback for OCC STL seam failures."""
from pathlib import Path
import json,subprocess
import trimesh
ROOT=Path(__file__).resolve().parents[2];WORK=ROOT/'_support/work/l2_r3/surface_mesh';WORK.mkdir(exist_ok=True)
OUT=ROOT/'models/L2_r3/parts';GMSH=ROOT/'_support/tools/Gmsh/gmsh-4.15.2-Windows64/gmsh.exe'
rows=[]
for n in ['BODY','SIDE_FRONT_KEY','SIDE_REAR_KEY']:
    geo=WORK/(n+'.geo');stl=WORK/(n+'.stl');source=OUT/(n+'.step')
    geo.write_text(f'''SetFactory("OpenCASCADE");
Merge "{source.as_posix()}";
Mesh.MeshSizeMin=0.10;
Mesh.MeshSizeMax=0.60;
Mesh.MeshSizeFromCurvature=32;
Mesh.Algorithm=6;
Mesh.ElementOrder=1;
Mesh.Binary=1;
''')
    with (WORK/(n+'.log')).open('w') as f:subprocess.run([str(GMSH),str(geo),'-2','-format','stl','-o',str(stl),'-nt','1'],stdout=f,stderr=subprocess.STDOUT,check=True)
    m=trimesh.load_mesh(stl);m.merge_vertices(digits_vertex=6);m.update_faces(m.nondegenerate_faces(height=1e-9));m.update_faces(m.unique_faces());m.remove_unreferenced_vertices()
    row=dict(part=n,watertight=bool(m.is_watertight),winding_consistent=bool(m.is_winding_consistent),components=len(m.split(only_watertight=False)),triangles=len(m.faces),method='Gmsh conforming mesh of the original STEP surfaces; no hole filling or geometric repairs')
    if m.is_watertight and m.is_winding_consistent and row['components']==1:m.export(OUT/(n+'.stl'));row['accepted']=True
    else:row['accepted']=False
    rows.append(row);print(row,flush=True)
    (ROOT/'reports/l2_r3/surface_mesh_checks.json').write_text(json.dumps(rows,indent=2))
