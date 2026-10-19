"""Full three-grid SPOOLES checks. Serial, with a 10 GB available-RAM guard."""
import importlib.util,json,os,shutil,sys,time,subprocess
from pathlib import Path
import numpy as np
import gmsh,psutil
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
WORK=ROOT/'_support/work/l2_r4/fem';RP=ROOT/'reports/l2_r4/fem'
spec=importlib.util.spec_from_file_location('r4_fem_core',ROOT/'cad/rebuild_r2/fem_check.py')
FC=importlib.util.module_from_spec(spec);sys.modules[spec.name]=FC;spec.loader.exec_module(FC)
FC.CCX=Path(shutil.which('ccx') or os.environ['QM_CCX'])
os.environ['QM_FEM_LINEAR_SOLVER']='DEFAULT'
import fem_loads as L
L.FC=FC

def monitored_command(args,cwd,log,timeout=600):
    """Serial actual solver execution with resident-memory and completion data."""
    start=time.monotonic();peak=0;deadline=max(timeout,1800);env=os.environ.copy()
    env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',CCX_NPROC_RESULTS='1',NUMBER_OF_CPUS='1')
    with Path(log).open('w',encoding='utf8') as stream:
        process=subprocess.Popen([str(a) for a in args],cwd=cwd,env=env,stdout=stream,stderr=subprocess.STDOUT)
        observed=psutil.Process(process.pid)
        while process.poll() is None:
            try:peak=max(peak,observed.memory_info().rss)
            except psutil.NoSuchProcess:pass
            if time.monotonic()-start>deadline:
                process.kill();process.wait();raise RuntimeError(f'Same-case solver timeout after {deadline}s; no case skipped')
            time.sleep(.25)
    seconds=time.monotonic()-start
    measured=dict(returncode=process.returncode,elapsed_seconds=seconds,peak_resident_GB=peak/1e9,measurement='psutil process RSS sampled every 0.25 s',solver_command=[str(a) for a in args])
    (Path(cwd)/'solver_runtime.json').write_text(json.dumps(measured,indent=2))
    if process.returncode:raise RuntimeError('CalculiX failed '+json.dumps(measured)+'\n'+Path(log).read_text(errors='replace')[-5000:])
    return seconds
FC.command=monitored_command
REF={
 'palm_down_20N':[105.64,105.97,105.04],
 'left_main_root_down_5N':[24.95,24.63,24.47],
 'right_main_root_down_5N':[24.28,23.97,23.93],
 'LC3_squeeze_2x2N':[496.43,502.,497.99],
 'press_A_d16_x14_y60':[62.21,62.15,61.77],
 'press_B_d16_x-14_y72':[56.21,53.9,55.31]}
AUTHOR={
 'palm_down_20N':[143.35,144.45,142.41],
 'left_main_root_down_5N':[31.70,31.28,31.54],
 'right_main_root_down_5N':[27.98,27.59,27.53],
 'LC3_squeeze_2x2N':[922.03,923.32,931.07],
 'press_A_d16_x14_y60':[74.24,74.70,73.86],
 'press_B_d16_x-14_y72':[60.53,57.72,59.10]}

def mesh(step,d,h):
    d.mkdir(parents=True,exist_ok=True);gmsh.initialize()
    try:
        gmsh.option.setNumber('General.Terminal',0)
        gmsh.model.occ.importShapes(str(step));gmsh.model.occ.synchronize()
        vs=gmsh.model.getEntities(3)
        assert len(vs)==1,vs
        gmsh.model.addPhysicalGroup(3,[vs[0][1]],name='BODY')
        opts={'Mesh.MeshSizeMin':max(.35,.38*h),'Mesh.MeshSizeMax':h,
              'Mesh.MeshSizeFromPoints':1,'Mesh.MeshSizeFromCurvature':24,
              'Mesh.MeshSizeExtendFromBoundary':1,'Mesh.Algorithm':6,
              'Mesh.Algorithm3D':1,'Mesh.ElementOrder':2,
              'Mesh.SecondOrderLinear':1,'Mesh.HighOrderOptimize':0,
              'Mesh.Optimize':1,'Mesh.SaveAll':0,'General.NumThreads':1}
        for k,v in opts.items():gmsh.option.setNumber(k,v)
        gmsh.model.mesh.generate(3);gmsh.write(str(d/'mesh.inp'))
        (d/'mesh_settings.json').write_text(json.dumps(opts,indent=2))
    finally:gmsh.finalize()
    m=FC.parse_mesh(d/'mesh.inp');m.stats.update(target_max_size_mm=h,settings=opts,gmsh_version=gmsh.__version__)
    return m

def solve(m,d,cons,loads,description,feet):
    mem=psutil.virtual_memory().available
    if mem<10_000_000_000:raise RuntimeError(f'Available RAM {mem/1e9:.3f} GB < required 10 GB; solve was not started')
    print('SPOOLES',description['name'],'free_GB',mem/1e9,flush=True)
    r,u=FC.solve(m,d,1500.,.35,cons,loads,description,feet)
    solver_log=(d/'ccx.log').read_text(errors='replace')
    assert 'SPOOLES' in solver_log.upper(),'Requested default SPOOLES was not identified in actual solver log'
    r['solver_backend_verified']='SPOOLES in actual CalculiX log'
    r['solver_runtime']=json.loads((d/'solver_runtime.json').read_text())
    r['available_memory_before_solve_GB']=mem/1e9
    # Keep exact deck + compact actual results under versioned reports; raw
    # meshes and DAT files remain in work, with their recorded digests.
    target=RP/d.parent.name/d.name;target.mkdir(parents=True,exist_ok=True)
    (target/'result.json').write_text(json.dumps(r,indent=2))
    return r,u

def main():
    RP.mkdir(parents=True,exist_ok=True);rows=[]
    for j,h in enumerate([2.4,2.0,1.6]):
        d=WORK/f'BODY_h{h:g}';m=mesh(ROOT/'models/L2_r4/parts/BODY.step',d,h)
        cons,feet=L.foot_constraints(m)
        for loads,desc in L.cases(m):
            r,u=solve(m,d/desc['name'],cons,loads,desc,feet)
            F=desc['magnitude_N'];delta=float(np.sum(loads*u))/F;k=F/delta
            row=dict(size_mm=h,case=desc['name'],stiffness_N_per_mm=k,
                baseline_N_per_mm=REF[desc['name']][j],ratio=k/REF[desc['name']][j],
                author_N_per_mm=AUTHOR[desc['name']][j],author_difference_fraction=k/AUTHOR[desc['name']][j]-1,
                equilibrium_pass=r['equilibrium_pass'],vm_p95_MPa=r['p95_integration_point_vm_MPa'],
                passed=k>=REF[desc['name']][j] and r['equilibrium_pass'],
                author_difference_requires_investigation=abs(k/AUTHOR[desc['name']][j]-1)>.03)
            rows.append(row);(RP/'stiffness.json').write_text(json.dumps(rows,indent=2));print(row,flush=True)
        del m
    (RP/'G8.json').write_text(json.dumps(dict(status='COMPLETED' if len(rows)==18 and all(r['passed'] and not r['author_difference_requires_investigation'] for r in rows) else 'REVIEW_REQUIRED',rows=rows),indent=2))

if __name__=='__main__':main()
