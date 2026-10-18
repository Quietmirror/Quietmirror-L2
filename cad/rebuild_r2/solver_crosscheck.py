"""Validate the iterative solver on the same analytical beam before fine BODY jobs."""
import json,os
import fem_check as f

def main():
    f.low_priority()
    original_work,original_report=f.WORK,f.REPORT
    reference=json.loads((original_report/'fem_beam_benchmark.json').read_text(encoding='utf8'))
    f.WORK=original_work/'iterative_validation'
    f.REPORT=f.WORK/'report'
    os.environ['QM_FEM_LINEAR_SOLVER']='ITERATIVE CHOLESKY'
    result=f.beam_benchmark()
    rows=[]
    for a,b in zip(reference['results'],result['results']):
        rows.append(dict(case=b['case']['name'],size_mm=b['mesh']['target_max_size_mm'],
            direct_displacement_mm=a['measured_end_displacement_mm'],
            iterative_displacement_mm=b['measured_end_displacement_mm'],
            relative_difference=abs(b['measured_end_displacement_mm']/a['measured_end_displacement_mm']-1),
            analytic_error=b['relative_analytic_error'],equilibrium_pass=b['equilibrium_pass'],
            deck_sha256=b['deck_sha256'],dat_sha256=b['dat_sha256']))
    checked=dict(solver='CalculiX 2.22 ITERATIVE CHOLESKY',
        reference='fem_beam_benchmark.json',comparisons=rows,
        pass_check=result['pass_check'] and all(x['relative_difference']<1e-4 for x in rows),
        scope='Analytical beam crosscheck; fine BODY jobs also require force/moment balance and completed solver output.',
        source='https://www.dhondt.de/ccx_2.22.pdf')
    f.write_json(original_report/'solver_crosscheck.json',checked)
    assert checked['pass_check'],checked
    print('ITERATIVE_SOLVER_CROSSCHECK',checked['pass_check'],flush=True)

if __name__=='__main__':main()
