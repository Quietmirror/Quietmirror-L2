# 3D solid FEM comparison of the R3.2 roof-cutout variants P0 / P1 / P7 with Gmsh + CalculiX.
# Reuses the R2 fem_check.py mesh parser, load distribution, deck writer, solver wrapper and
# post-processing unchanged; only mesh generation (gmsh Python API on the variant STEP), the
# foot datum (R3.1 short feet at Z 5.2) and the extra load cases are new here.
import json, math, os, sys, time
from pathlib import Path
import numpy as np

TMP = Path(os.environ.get('QM_SUPPORT', r'D:\Quietmirror_L2\_support'))
sys.path.insert(0, str(TMP/'src'/'R3_2_SOURCE'/'cad'/'rebuild_r2'))
import fem_check as FC                                         # noqa: E402
import gmsh                                                    # noqa: E402

HERE = Path(__file__).resolve().parent
WORK = TMP/'fem3d_work'; WORK.mkdir(exist_ok=True)
FC.CCX = Path(os.environ.get('QM_CCX', str(TMP/'tools'/'_x'/'FreeCAD_1.1.4-Windows-x86_64-py311'/'bin'/'ccx.exe')))
META = json.load(open(TMP/'qm'/'reports__rebuild_r3_2__design_metadata.json', encoding='utf-8-sig'))
P2 = json.load(open(TMP/'src'/'R3_2_SOURCE'/'cad'/'rebuild_r2'/'parameters.json', encoding='utf-8-sig'))
FOOT_Z = 5.2

MESH_MODE = os.environ.get('QM_MESH_MODE', 'direct')   # 'direct' (fem_check-style) or 'twostep' (mesh2.py)

def make_mesh(step, directory, size):
    if MESH_MODE == 'twostep':
        import mesh2
        info = mesh2.two_step(step, directory, size)
        m = FC.parse_mesh(directory/'mesh.inp'); m.stats.update(target_max_size_mm=size, mesh_method=info)
        print(f'  two-step mesh {directory.name}: {info}', flush=True)
        return m
    directory.mkdir(parents=True, exist_ok=True)
    inp = directory/'mesh.inp'
    # healing broke a periodic surface on P1c; P1c has a coincident face pair (surfaces 823/825) that
    # the Delaunay 3D boundary check rejects, Frontal 3D (alg 4) accepts it (mesh then validated by parse_mesh)
    attempts = [dict(heal=False, alg2d=6, alg3d=1, overlap_tol=None), dict(heal=False, alg2d=6, alg3d=1, overlap_tol=0.0),
                dict(heal=False, alg2d=6, alg3d=4, overlap_tol=None)]
    used = None
    if not inp.is_file():
        last = None
        for a in attempts:
            gmsh.initialize(); gmsh.option.setNumber('General.Terminal', 0)
            try:
                gmsh.model.add('m'); gmsh.model.occ.importShapes(str(step))
                if a['heal']:
                    gmsh.model.occ.healShapes(tolerance=1e-4, fixDegenerated=True, fixSmallEdges=True, fixSmallFaces=True, sewFaces=True, makeSolids=True)
                gmsh.model.occ.synchronize()
                vols = gmsh.model.getEntities(3)
                gmsh.model.addPhysicalGroup(3, [v[1] for v in vols], name='BODY')
                for k, v in dict(**{'Mesh.MeshSizeMin': max(.35, size*.38), 'Mesh.MeshSizeMax': size, 'Mesh.MeshSizeFromPoints': 1,
                                   'Mesh.MeshSizeFromCurvature': 24, 'Mesh.MeshSizeExtendFromBoundary': 1, 'Mesh.Algorithm': a['alg2d'],
                                   'Mesh.Algorithm3D': a['alg3d'], 'Mesh.ElementOrder': 2, 'Mesh.SecondOrderLinear': 1,
                                   'Mesh.HighOrderOptimize': 0, 'Mesh.Optimize': 1, 'Mesh.SaveAll': 0,
                                   'General.NumThreads': 4}).items():
                    gmsh.option.setNumber(k, v)
                if a['overlap_tol'] is not None: gmsh.option.setNumber('Mesh.AngleToleranceFacetOverlap', a['overlap_tol'])
                t = time.time(); gmsh.model.mesh.generate(3); gmsh.write(str(inp))
                used = a; print(f'  meshed {directory.name} in {time.time()-t:.0f}s with {a}', flush=True)
                break
            except Exception as ex:
                last = ex; print(f'  mesh attempt {a} failed: {ex}', flush=True)
            finally:
                gmsh.finalize()
        if used is None: raise RuntimeError(f'all mesh attempts failed: {last}')
        (directory/'mesh_method.json').write_text(json.dumps(used))
    m = FC.parse_mesh(inp)
    m.stats.update(target_max_size_mm=size)
    mm = directory/'mesh_method.json'
    m.stats['mesh_method'] = json.loads(mm.read_text()) if mm.is_file() else attempts[0]
    return m

def foot_constraints(mesh):
    centers = np.asarray(P2['feet']['centers']); r = P2['feet']['diameter']/2
    feet = []
    for c in centers:
        idx = np.flatnonzero((np.abs(mesh.xyz[:, 2]-FOOT_Z) < .025) & (np.linalg.norm(mesh.xyz[:, :2]-c, axis=1) < r+.03))
        if len(idx) < 6: raise ValueError(f'Too few foot nodes at {c}: {len(idx)}')
        feet.append(idx)
    a = int(feet[0][np.argmin(np.linalg.norm(mesh.xyz[feet[0], :2]-centers[0], axis=1))])
    b = int(feet[1][np.argmin(np.linalg.norm(mesh.xyz[feet[1], :2]-centers[1], axis=1))])
    return [(int(i), 3) for g in feet for i in g]+[(a, 1), (a, 2), (b, 2)], feet

from surfaces import roof_z, half_width, roof_height   # noqa: E402

def outer_masks(mesh):
    """Faces lying on the mother OUTER surface (roof: |z - roof_z| < .35; side: ||x| - wall_x| < .35).
    The R2 masks also caught interior faces seen through the windows (e.g. the top of the severed
    Y54 cross tie), which loaded a floating beam (umax 280 mm). Only the shell exterior is loaded here."""
    x, y, z = mesh.centers.T
    rz = np.array([roof_z(a, b, P2) for a, b in zip(x, y)])
    w = np.array([half_width(b, P2) for b in y]); h = np.array([roof_height(b, P2) for b in y])
    frac = np.clip((z-5)/np.maximum(h-5, 1e-6), 0, 1)
    wx = w*np.maximum(0, 1-frac**3.4)**(1/3.4)
    return np.abs(z-rz) < .35, np.abs(np.abs(x)-wx) < .35

def cases(mesh):
    x, y, z = mesh.centers.T; nx, ny, nz = mesh.normals.T
    roof_out, side_out = outer_masks(mesh)
    root = P2['main']['root_y']; out = []
    # fem_check.py body_cases; palm restricted to the outer roof surface (see outer_masks)
    out.append(FC.selected_load(mesh, (y >= 44) & (y <= 71) & (np.abs(x) <= 24) & (z >= 23) & (nz > .3) & roof_out, [0, 0, -1], 20, 'palm_down_20N'))
    out.append(FC.selected_load(mesh, (y >= root-3) & (y <= root+4) & (x >= 6) & (x <= 24) & (z >= 11) & (nz > .2), [0, 0, -1], 5, 'left_main_root_down_5N'))
    out.append(FC.selected_load(mesh, (y >= root-3) & (y <= root+4) & (x <= -6) & (x >= -24) & (z >= 11) & (nz > .2), [0, 0, -1], 5, 'right_main_root_down_5N'))
    for i, m in enumerate(META['mechanisms']['side_motions']):
        tip = np.asarray(m['plunger_tip'], float); fx = tip[0]-7.5; cy, cz = tip[1:]
        out.append(FC.selected_load(mesh, (np.abs(x-fx) < .04) & (np.abs(y-cy) <= 7.25) & (z >= cz-2.9) & (z <= cz+2.9) & (nx > .95),
                                    [-1, 0, 0], 5, f'side_{i+1}_switch_fence_inward_5N'))
    # new: LC3 two-sided squeeze (4 N total, 2 N each side, opposing) on the grip bands
    lp, _ = FC.selected_load(mesh, (x > 20) & (y >= 45) & (y <= 70) & (z >= 8) & (z <= 14) & (nx > .5) & side_out, [-1, 0, 0], 2, 'squeeze_+X')
    lm, _ = FC.selected_load(mesh, (x < -20) & (y >= 45) & (y <= 70) & (z >= 8) & (z <= 14) & (nx < -.5) & side_out, [1, 0, 0], 2, 'squeeze_-X')
    out.append((lp+lm, dict(name='LC3_squeeze_2x2N', magnitude_N=4.0, components=['+X side 2 N toward -X', '-X side 2 N toward +X'])))
    # new: local 5 N finger-pad press, d16 patch on the outer roof at two cut-out areas. A d10 patch at
    # (-14, 72) lies entirely inside the R3.2 rear window (no surface), so d16 is used: in every variant
    # the pad then bears on the hole edges / ribs that a real finger pad would touch.
    for nm, (px, py) in (('press_A_d16_x14_y60', (14.0, 60.0)), ('press_B_d16_x-14_y72', (-14.0, 72.0))):
        out.append(FC.selected_load(mesh, (np.hypot(x-px, y-py) <= 8.0) & (z >= 18) & (nz > .3) & roof_out, [0, 0, -1], 5, nm))
    return out

def conjugate_disp(loads, u):
    F = loads.reshape(-1); return float(F @ u.reshape(-1))/max(1e-12, float(np.linalg.norm(loads.sum(axis=0))) if np.linalg.norm(loads.sum(axis=0)) > 1e-9 else float(np.abs(loads).sum()/2))

def main(sizes, variants, young=1500.0, nu=0.35):
    summary = []
    for size in sizes:
        for v in variants:
            step = HERE/'variants'/f'BODY_{v}.step'
            d = WORK/(f'{v}_h{size:g}' + ('_ts' if MESH_MODE == 'twostep' else ''))
            t = time.time()
            mesh = make_mesh(step, d, size)
            cons, feet = foot_constraints(mesh)
            print(f'{v} h{size}: nodes {mesh.stats["nodes"]} elems {mesh.stats["elements"]} vol {mesh.stats["quadratic_tet_integrated_volume_mm3"]:.1f}', flush=True)
            for loads, desc in cases(mesh):
                r, u = FC.solve(mesh, d/desc['name'], young, nu, cons, loads, desc, feet)
                # work-conjugate displacement: sum(f.u)/|F| (self-equilibrated squeeze: divide by the 4 N total pair magnitude/2 per side)
                fu = float(np.sum(loads*u))
                Fmag = desc.get('magnitude_N', float(np.linalg.norm(loads.sum(axis=0))))
                delta = fu/Fmag
                row = dict(variant=v, size=size, case=desc['name'], F_N=Fmag, work_conj_disp_mm=delta, stiffness_N_per_mm=Fmag/delta,
                           umax_mm=r['maximum_displacement_mm'], vm_max_MPa=r['maximum_vm_stress_MPa'], vm_p95_MPa=r['p95_integration_point_vm_MPa'],
                           equilibrium_pass=r['equilibrium_pass'], nodes=mesh.stats['nodes'], elements=mesh.stats['elements'],
                           solve_s=r['solving_seconds'], negative_feet=r['negative_foot_reactions'])
                summary.append(row)
                print(f'   {desc["name"]:30s} delta {delta:.5f} mm  k {Fmag/delta:9.2f} N/mm  umax {r["maximum_displacement_mm"]:.4f}  p95 {r["p95_integration_point_vm_MPa"]:.3f}  eq {r["equilibrium_pass"]}  [{r["solving_seconds"] or 0:.0f}s]', flush=True)
                json.dump(summary, open(HERE/('fem_summary_ts.json' if MESH_MODE == 'twostep' else 'fem_summary.json'), 'w'), indent=1)
            print(f'  {v} h{size} total {time.time()-t:.0f}s', flush=True)
    return summary

if __name__ == '__main__':
    sizes = [float(s) for s in (sys.argv[1] if len(sys.argv) > 1 else '2.4').split(',')]
    variants = (sys.argv[2] if len(sys.argv) > 2 else 'P0,P1,P7').split(',')
    main(sizes, variants)
