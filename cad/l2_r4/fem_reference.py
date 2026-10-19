"""Resolve the written-vs-author root-load interval on one immutable R3.2 mesh.

Both sides, all three mandated mesh sizes, both intervals; serial SPOOLES.
These are additional reference solves, not substitutes for final R4 G8/S7.
"""
import json,os,subprocess,sys
import numpy as np
from fem_stage import FC,L,ROOT,RP,WORK,mesh,solve,REF

def main():
    RP.mkdir(parents=True,exist_ok=True);rows=[];path=RP/'REFERENCE_R32_ROOT_PROTOCOL.json'
    for j,h in enumerate([2.4,2.0,1.6]):
        d=WORK/f'R32_REFERENCE_h{h:g}'
        m=mesh(ROOT/'exports/rebuild_r3_2/assembly/BODY.step',d,h);cons,feet=L.foot_constraints(m)
        for label,interval in [('written',(35.5,42.5)),('author_helper',(35.,42.))]:
            for loads,desc in L.root_cases(m,interval):
                desc.update(root_y_interval_mm=interval,reference_model='R32_BASELINE.FCStd BODY; original f1b1090931d717117287ea2b79c2e14ddc234937')
                r,u=solve(m,d/(label+'_'+desc['name']),cons,loads,desc,feet)
                delta=float(np.sum(loads*u))/5.;k=5./delta
                rows.append(dict(size_mm=h,case=desc['name'],protocol=label,root_y_interval_mm=interval,stiffness_N_per_mm=k,
                    published_reference_N_per_mm=REF[desc['name']][j],difference_from_published_fraction=k/REF[desc['name']][j]-1,
                    equilibrium_pass=r['equilibrium_pass'],solver_runtime=r['solver_runtime']))
                path.write_text(json.dumps(dict(status='RUNNING',rows=rows,scope='Reference protocol discrepancy investigation only; final R4 FEM is separate'),indent=2))
                print(rows[-1],flush=True)
                if os.getenv('GITHUB_ACTIONS')=='true':subprocess.run([sys.executable,str(ROOT/'cad/l2_r4/ci_checkpoint.py')],cwd=ROOT,check=True)
        del m
    path.write_text(json.dumps(dict(status='COMPLETED' if len(rows)==12 and all(r['equilibrium_pass'] for r in rows) else 'FAILED',rows=rows),indent=2))

if __name__=='__main__':main()
