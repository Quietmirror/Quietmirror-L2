"""Serial candidate execution; publish only work-branch checkpoints, no Release."""
from pathlib import Path
import json,os,subprocess,sys,time,traceback,argparse
import psutil
ROOT=Path(__file__).resolve().parents[2];RP=ROOT/'reports/l2_r4';WORK=ROOT/'_support/work/l2_r4'
def main():
    RP.mkdir(parents=True,exist_ok=True);WORK.mkdir(parents=True,exist_ok=True)
    parser=argparse.ArgumentParser();parser.add_argument('--config',default='cad/l2_r4/RUN.json');parser.add_argument('--index',type=int)
    args=parser.parse_args();config=json.loads((ROOT/args.config).read_text());single=args.index
    report_path=RP/config.get('report_file','execution.json')
    indices=range(len(config['scripts'])) if single is None else [single]
    if single is not None and single>0:
        report=json.loads(report_path.read_text());assert report['phase']==config['phase'] and report['source_commit']==os.getenv('GITHUB_SHA')
    else:report=dict(status='RUNNING',phase=config['phase'],source_commit=os.getenv('GITHUB_SHA'),steps=[])
    for index in indices:
        script=config['scripts'][index]
        start=time.time();log=WORK/(Path(script).stem+'.log');mem=psutil.virtual_memory()
        print('START',script,'available_GB',round(mem.available/1e9,2),flush=True)
        with log.open('w') as f:
            p=subprocess.run([sys.executable,'-u',str(ROOT/script)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
        tail=log.read_text(errors='replace')[-6000:];print(tail,flush=True)
        report['steps'].append(dict(script=script,returncode=p.returncode,seconds=round(time.time()-start,2),available_memory_before_GB=mem.available/1e9,log_tail=tail))
        report['status']='FAILED' if p.returncode else 'RUNNING';report_path.write_text(json.dumps(report,indent=2))
        if os.getenv('GITHUB_ACTIONS')=='true':
            # Preserve finite completed stages while later checks run; no
            # release or pass status is inferred from these checkpoints.
            subprocess.run([sys.executable,str(ROOT/'cad/l2_r4/ci_checkpoint.py')],cwd=ROOT,check=True)
        if p.returncode:return p.returncode
    report['status']='PHASE_COMPLETED' if single is None or single==len(config['scripts'])-1 else 'RUNNING';report_path.write_text(json.dumps(report,indent=2));return 0
if __name__=='__main__':sys.exit(main())
