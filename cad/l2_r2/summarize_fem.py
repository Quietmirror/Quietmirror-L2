"""Summarize measured baseline convergence and affine mesh volume."""
from pathlib import Path
import importlib.util,json
import numpy as np

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'reports/l2_r2'
spec=importlib.util.spec_from_file_location('own_fem',ROOT/'cad/l2_r1/independent_fem.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)

def main():
    levels=[]
    for s in ('2.4','2','1.6'):
        p=OUT/f'K3_r2_baseline_{s}.json'
        if not p.exists():continue
        d=json.loads(p.read_text());mesh=ROOT/f'_support/work/fem_r2/R32_{s}_straight_midside/mesh.inp'
        if all(r['document_k_N_per_mm'] is None for r in d['results']):
            d['all_eight_within_3_percent']=None
            d['comparison_status']='No document reference for this intermediate grid; convergence only'
            p.write_text(json.dumps(d,indent=2),encoding='utf8')
        nodes,elems=core.readmesh(mesh)
        signed=[];mid_error=0.
        for e in elems:
            q=np.array([nodes[n] for n in e]);signed.append(float(np.linalg.det((q[1:4]-q[0]).T)/6))
            for a,b,m in ((0,1,4),(1,2,5),(2,0,6),(0,3,7),(1,3,8),(2,3,9)):
                mid_error=max(mid_error,float(np.linalg.norm(q[m]-(q[a]+q[b])/2)))
        v=sum(abs(x) for x in signed)
        levels.append(dict(mesh_mm=float(s),nodes=len(nodes),elements=len(elems),
            affine_midside_max_residual_mm=mid_error,mesh_volume_mm3=v,
            mesh_volume_vs_BRep_percent=100*(v/12801.730065878228-1),
            nonpositive_corner_determinants=sum(x<=0 for x in signed),
            min_element_volume_mm3=min(abs(x) for x in signed),
            force_and_moment_balance=d['balance_passed'],
            pass_count=sum(r['within_document_3_percent'] is True for r in d['results']),
            k_values=[r['k_N_per_mm'] for r in d['results']],
            selected_areas=[[p['area_mm2'] for p in r['patches']] for r in d['results']]))
    changes=[]
    for a,b in zip(levels,levels[1:]):
        changes.append(dict(from_mm=a['mesh_mm'],to_mm=b['mesh_mm'],
            k_change_percent=[100*(y/x-1) for x,y in zip(a['k_values'],b['k_values'])],
            note='Two consecutive mesh levels and identical analytic selectors; selected patch edges can move with mesh.'))
    report=dict(levels=levels,changes=changes,author_1p6_nodes=307796,
        author_mesh_inputs_available=False,
        final_L2_vs_R32_certified=False,
        conclusion='Baseline reproduction is not validated unless all required comparisons and convergence gates pass; these runs alone do not establish final L2 stiffness.')
    (OUT/'K3_mesh_summary.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
