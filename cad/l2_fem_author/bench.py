# Re-run fem_check.py's analytic cantilever benchmark through this toolchain (gmsh API + CalculiX 2.22)
import os, sys, json
from pathlib import Path
import numpy as np
TMP = Path(os.environ.get('QM_SUPPORT', r'D:\Quietmirror_L2\_support'))
sys.path.insert(0, str(TMP/'src'/'R3_2_SOURCE'/'cad'/'rebuild_r2'))
import fem_check as FC
import gmsh
FC.CCX = Path(os.environ['QM_CCX'])
W = TMP/'fem3d_work'/'bench'
def beam_mesh(size):
    d = W/f'h{size:g}'; d.mkdir(parents=True, exist_ok=True); inp = d/'mesh.inp'
    if not inp.is_file():
        gmsh.initialize(); gmsh.option.setNumber('General.Terminal', 0); gmsh.model.add('b')
        gmsh.model.occ.addBox(0, -2, -2, 40, 4, 4); gmsh.model.occ.synchronize()
        gmsh.model.addPhysicalGroup(3, [1], name='BODY')
        for k, v in {'Mesh.MeshSizeMin': size, 'Mesh.MeshSizeMax': size, 'Mesh.Algorithm': 6, 'Mesh.Algorithm3D': 1,
                     'Mesh.ElementOrder': 2, 'Mesh.SecondOrderLinear': 1, 'Mesh.Optimize': 1, 'Mesh.SaveAll': 0}.items():
            gmsh.option.setNumber(k, v)
        gmsh.model.mesh.generate(3); gmsh.write(str(inp)); gmsh.finalize()
    return d, FC.parse_mesh(inp)
L, b, h, E, nu = 40., 4., 4., 1500., .35
euler = L**3/(3*E*(b*h**3/12)); shear = L/((5/6)*(E/(2*(1+nu)))*b*h); axial = 10*L/(E*b*h)
for size in (2.0, 1.25):
    d, m = beam_mesh(size)
    fixed = np.flatnonzero(m.xyz[:, 0] < 1e-7); cons = [(int(i), k) for i in fixed for k in (1, 2, 3)]
    mask = (m.centers[:, 0] > L-1e-6) & (m.normals[:, 0] > .99)
    for name, dirn, F, exp, c in (('bend', [0, 0, -1], 1., euler+shear, 2), ('axial', [1, 0, 0], 10., axial, 0)):
        loads, desc = FC.selected_load(m, mask, dirn, F, name)
        r, u = FC.solve(m, d/name, E, nu, cons, loads, desc)
        meas = abs(float((np.abs(loads[:, c])/F) @ u[:, c]))
        print(f'h{size} {name}: FEM {meas:.6f} analytic {exp:.6f} err {abs(meas/exp-1)*100:.2f}% eq {r["equilibrium_pass"]} nodes {m.stats["nodes"]}')
