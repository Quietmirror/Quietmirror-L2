"""Serial, bounded low-memory FEM attempts; fail closed on missing evidence."""
from pathlib import Path
import sys,subprocess,json
ROOT=Path(__file__).resolve().parents[2];RP=ROOT/'reports/l2_r3';WORK=ROOT/'_support/work/fem_r3'
GUARD=ROOT/'cad/l2_r3/guard.py';CCX=ROOT/'_support/tools/FreeCAD/FreeCAD_1.1.4-Windows-x86_64-py311/bin/ccx.exe'
status=dict(G8_status='INCOMPLETE',summary='Staged solver attempts running; no certification',attempts=[],three_mesh_comparison_complete=False)

def save():(RP/'fem_status.json').write_text(json.dumps(status,indent=2,ensure_ascii=False))
def run(cmd,cwd,log,timeout=900):
    code=subprocess.run([sys.executable,str(GUARD),'--memory-gib','4','--timeout',str(timeout),'--log',str(log),'--',*map(str,cmd)],cwd=cwd).returncode
    status['attempts'].append(dict(command_name=Path(str(cmd[0])).name,args=[str(v) for v in cmd[1:]],log=str(log.relative_to(ROOT)),returncode=code))
    save()
    if code:raise RuntimeError('Guarded stage failed; see '+str(log.relative_to(ROOT)))

def one(geometry,size):
    prefix=f'{geometry}_{size:g}';work=WORK/(prefix+'_curvature24')
    run([sys.executable,'cad/l2_r3/fem_stage.py','prepare','--geometry',geometry,'--size',size],ROOT,ROOT/('_support/logs/staged_'+prefix+'_prepare.log'))
    run([CCX,'-i','iterative'],work,work/'iterative.log')
    run([sys.executable,'cad/l2_r3/fem_stage.py','parse','--geometry',geometry,'--size',size],ROOT,ROOT/('_support/logs/staged_'+prefix+'_parse.log'),300)
    return json.loads((RP/f'FEM_{geometry}_{size:g}.json').read_text())

def main():
    save()
    try:
        beam=one('beam',2.4)
        assert abs(beam['analytic_error_percent'])<5,'Independent iterative beam calibration outside 5%'
        for size in [2.4,2.,1.6]:
            original=one('R32',size)
            if any(not r['force_balance_passed'] or not r['moment_balance_passed'] for r in original['results']):raise RuntimeError('Original FEM reaction equilibrium not within tolerance')
            if size==2.4 and any(abs(r['deviation_percent'])>3 for r in original['results']):
                status['G8_status']='INCOMPLETE';status['summary']='K3独立基线未达到文档±3%，停止向G8认证推进；未调载荷/材料凑数。';save();return
            final=one('L2',size)
            comparisons=[]
            for a,b in zip(original['results'],final['results']):comparisons.append(dict(original=a['name'],final=b['name'],ratio=b['k_N_per_mm']/a['k_N_per_mm']))
            status.setdefault('comparisons',[]).append(dict(size=size,cases=comparisons));save()
        status['three_mesh_comparison_complete']=True
        passed=all(c['ratio']>=1 for g in status['comparisons'] for c in g['cases'])
        status['G8_status']='PASS_LINEAR_MODEL' if passed else 'INCOMPLETE'
        status['summary']='三档独立线弹性比较已完成；'+('所有工况≥原版，真实零件和接触刚度仍未认证。' if passed else '至少一个工况低于原版，不能标为刚度通过。')
    except Exception as e:
        status['G8_status']='3D_FEM_BLOCKED';status['summary']='分离式低内存求解未完成：'+str(e)+'；已有输入和日志保留，不补造结果。'
    save();print(json.dumps(status,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
