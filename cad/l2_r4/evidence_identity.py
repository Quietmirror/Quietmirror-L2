"""Tie reports to the actual geometry and verifier source used to produce them.

Hashes here establish version identity across CI phases, not a routine security
check. Metadata is kept separate so existing numerical JSON schemas stay intact.
"""
import argparse,ast,hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;RP=ROOT/'reports/l2_r4'
MANIFEST=RP/'evidence_manifest.json'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def relative(p):return p.relative_to(ROOT).as_posix()

def model_files(script):
    stem=Path(script).stem;parts=ROOT/'models/L2_r4/parts'
    if stem=='fem_stage':return [parts/'BODY.step',RP/'fem/REFERENCE_R32_ROOT_PROTOCOL.json']
    if stem=='side_fem':return [parts/(n+'.step') for n in ['BODY','SF_RETAINER','SR_RETAINER']]
    if stem=='fem_reference':return [ROOT/'models/L2_r3/inputs/R32_BASELINE.FCStd']
    if stem=='fem_geometry_investigation':return [parts/'BODY.step',ROOT/'models/L2_r3/parts/BODY.step',ROOT/'cad/l2_fem_author/variants/R4_SIDE_FRAME_ONLY.step',ROOT/'exports/l2_r2_diagnostic/support_reference/MOTHER_OUTER_FROM_R32_SURFACE.step']
    if stem in ['slice_plate','trial_and_plate_views']:
        return sorted(parts.glob('*.stl'))+[HERE/'PLA_0.4_0.20_ESTIMATE.ini']+sorted((ROOT/'models/L2_r4/reference').glob('*F2_TRIAL.step'))
    paths=list(parts.glob('*.step'))
    if stem in ['main_motion_checks','contact_audit']:paths.extend((ROOT/'models/L2_r4/validation_features').glob('*.step'))
    inv=RP/'assembly_inventory.json'
    if inv.exists():paths.extend(ROOT/'models/L2_r4/reference'/(n+'.step') for n in json.loads(inv.read_text())['H_hardware'])
    if stem in ['diagnostic_checks','mesh_metrics','surface_mesh','wall_audit','mesh_self_intersection']:paths.extend(parts.glob('*.stl'))
    return sorted(set(paths))

def source_files(script):
    pending=[ROOT/script];seen=set()
    if Path(script).stem in ['fem_stage','side_fem','fem_reference']:pending.append(ROOT/'cad/rebuild_r2/fem_check.py')
    while pending:
        p=pending.pop()
        if p in seen or not p.exists():continue
        seen.add(p)
        for node in ast.walk(ast.parse(p.read_text(encoding='utf-8-sig'))):
            names=[]
            if isinstance(node,ast.Import):names=[x.name for x in node.names]
            elif isinstance(node,ast.ImportFrom) and node.module:names=[node.module]
            for name in names:
                q=HERE/(name.split('.')[0]+'.py')
                if q.exists() and q not in seen:pending.append(q)
    return sorted(seen)

def identity(script):
    return dict(geometry={relative(p):digest(p) for p in model_files(script) if p.exists()},
                verifier_source={relative(p):digest(p) for p in source_files(script)})

def snapshot():
    return {relative(p):(p.stat().st_size,p.stat().st_mtime_ns) for p in RP.rglob('*') if p.is_file() and p!=MANIFEST}

def record(script,before,inputs,returncode):
    records=json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    for path,stat in snapshot().items():
        if before.get(path)==stat or path.endswith(('execution.json','reference_execution.json','inspection_execution.json')):continue
        records[path]=dict(script=script,source_commit=os.getenv('GITHUB_SHA'),returncode=returncode,
                           report_sha256=digest(ROOT/path),**inputs)
    MANIFEST.write_text(json.dumps(records,indent=2))

def verify(paths):
    records=json.loads(MANIFEST.read_text());results=[];cache={}
    for path in paths:
        key='reports/l2_r4/'+path;r=records.get(key);problems=[]
        if not r:problems.append('No version-linked execution record')
        else:
            if r['returncode']!=0:problems.append('Producer failed')
            for p,expected in {**r['geometry'],**r['verifier_source'],key:r['report_sha256']}.items():
                if p not in cache:cache[p]=digest(ROOT/p) if (ROOT/p).exists() else None
                if cache[p]!=expected:problems.append('Version mismatch: '+p)
        results.append(dict(report=path,passed=not problems,problems=problems))
    return results

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--python',default=sys.executable);ap.add_argument('--script',required=True);a=ap.parse_args()
    before=snapshot();inputs=identity(a.script)
    r=subprocess.run([a.python,'-u',a.script],cwd=ROOT)
    record(a.script,before,inputs,r.returncode);sys.exit(r.returncode)

if __name__=='__main__':main()
