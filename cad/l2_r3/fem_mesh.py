"""Independent r3 Appendix A meshing, shared by baseline and final geometry."""
from pathlib import Path
import importlib.util
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('r3_independent_core',ROOT/'cad/l2_r1/independent_fem.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
core.OUT=ROOT/'reports/l2_r3';core.WORK=ROOT/'_support/work/fem_r3'
def mesh(name,size,source):
    work=core.WORK/f'{name}_{size:g}_curvature24';work.mkdir(parents=True,exist_ok=True)
    geo=work/'mesh.geo';inp=work/'mesh.inp'
    content=f'''SetFactory("OpenCASCADE");
Merge "{source.as_posix()}";
Mesh.MeshSizeMin={max(.35,.38*size)};
Mesh.MeshSizeMax={size};
Mesh.MeshSizeFromCurvature=24;
Mesh.MeshSizeExtendFromBoundary=1;
Mesh.Algorithm=6;
Mesh.Algorithm3D=1;
Mesh.ElementOrder=2;
Mesh.SecondOrderLinear=1;
Mesh.Optimize=1;
Physical Volume("SOLID")={{Volume{{:}}}};
Mesh.SaveGroupsOfElements=0;
'''
    if geo.exists() and geo.read_text()!=content and inp.exists():
        raise RuntimeError('Different existing mesh definition; preserve it and use a new work directory')
    geo.write_text(content)
    if not inp.exists():core.run([core.GMSH,geo,'-3','-order','2','-format','inp','-o',inp,'-nt','1'],work,work/'gmsh.log')
    nodes,elements=core.readmesh(inp);faces=core.boundary(nodes,elements)
    print('Mesh',name,size,len(nodes),len(elements),len(faces),flush=True)
    return work,nodes,elements,faces
core.mesh=mesh
