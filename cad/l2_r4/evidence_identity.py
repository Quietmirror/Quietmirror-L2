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
TEXT_SUFFIXES={'.py','.json','.txt','.log','.step','.stp','.ini','.md','.yml','.yaml'}
def verified_text_layout(data,expected):
    """Recover a hash-proven LF/CRLF layout; every non-newline byte is exact.

    Windows Git changed line endings between a producer's checkout and its
    committed result. The stored producer hash is never replaced. Binary CAD
    and meshes do not use this function.
    """
    try:data.decode('utf8')
    except UnicodeDecodeError:return None
    lf=data.replace(b'\r\n',b'\n')
    for candidate in [data,lf,lf.replace(b'\n',b'\r\n')]:
        if hashlib.sha256(candidate).hexdigest()==expected:return candidate
    return None

def hash_matches(path,expected):
    if not path.exists():return False
    raw=path.read_bytes()
    return hashlib.sha256(raw).hexdigest()==expected or (path.suffix.lower() in TEXT_SUFFIXES and verified_text_layout(raw,expected) is not None)
def same_source_text(a,b):
    # Windows tools may preserve CRLF and append one final blank line.
    # Only these representation differences are ignored, never code tokens
    # or internal whitespace. The original bytes remain hash-verified.
    normalize=lambda v:v.decode('utf-8').replace('\r\n','\n').rstrip()+'\n'
    return normalize(a)==normalize(b)

def model_files(script):
    stem=Path(script).stem;parts=ROOT/'models/L2_r4/parts'
    if stem=='fem_stage':return [parts/'BODY.step',RP/'fem/REFERENCE_R32_ROOT_PROTOCOL.json']
    if stem=='side_fem':return [parts/(n+'.step') for n in ['BODY','SF_RETAINER','SR_RETAINER']]
    if stem=='fem_reference':return [ROOT/'models/L2_r3/inputs/R32_BASELINE.FCStd']
    if stem=='fem_geometry_investigation':return [parts/'BODY.step',ROOT/'models/L2_r3/parts/BODY.step',ROOT/'cad/l2_fem_author/variants/R4_SIDE_FRAME_ONLY.step',ROOT/'exports/l2_r2_diagnostic/support_reference/MOTHER_OUTER_FROM_R32_SURFACE.step']
    if stem in ['window_checks','combine_windows'] or stem.startswith('window_'):
        # These checks read only the final BODY, immutable baseline archive,
        # construction parameters and named fixed-bearing feature solids.
        # Unrelated movable parts/electronics are not window-check inputs.
        paths=[parts/'BODY.step',ROOT/'models/L2_r3/inputs/R32_BASELINE.FCStd',ROOT/'cad/rebuild_r2/parameters.json',ROOT/'cad/rebuild_r2/build.py',*sorted((ROOT/'models/L2_r4/validation_features').glob('*FIXED_BEARINGS.step'))]
        if stem=='combine_windows':
            paths.extend(RP/f'window_{i}.json' for i in range(6))
            paths.append(ROOT/'models/L2_r4/validation_features/SWITCH_MIDDLE_MOUNT.step')
        return paths
    if stem in ['slice_plate','trial_and_plate_views']:
        return sorted(parts.glob('*.stl'))+[HERE/'PLA_0.4_0.20_ESTIMATE.ini']+sorted((ROOT/'models/L2_r4/reference').glob('*F2_TRIAL.step'))
    if stem=='static_checks_final':return sorted(parts.glob('*.step'))
    if stem in ['geometry_checks_final','diagnostic_checks','exterior_audit','mesh_metrics','wall_audit','mesh_self_intersection','mechanism_accounting']:
        paths=[*sorted(parts.glob('*.step')),*sorted(parts.glob('*.stl')),ROOT/'cad/rebuild_r2/parameters.json',ROOT/'reports/rebuild_r3_2/design_metadata.json',RP/'assembly_inventory.json']
        names={'diagnostic_checks':['SF_TUNING_SHIM_0p33','SR_TUNING_SHIM_0p33'],
               'exterior_audit':['SF_VERTICAL_PIN','SR_VERTICAL_PIN'],
               'mechanism_accounting':['SF_TUNING_SHIM_0p33','SR_TUNING_SHIM_0p33','MATCHED_LENS_EST']}.get(stem,[])
        paths.extend(ROOT/'models/L2_r4/reference'/(n+'.step') for n in names)
        if stem=='mesh_metrics':paths.append(RP/'solids.json')
        return paths
    if stem in ['assembly_paths','plan_sf_route']:
        paths=[parts/(n+'.step') for n in ['BODY','SF_RETAINER','SR_RETAINER']]
        paths.extend(ROOT/'models/L2_r4/reference'/(n+'.step') for n in ['SF_D2F_01F','SR_D2F_01F'])
        paths.extend(ROOT/'cad/l2_r4_author'/n for n in ['guided_routes.json','loose_parts.json'])
        if stem=='assembly_paths':paths.append(RP/'SF_route_planning.json')
        return paths
    paths=list(parts.glob('*.step'))
    if stem=='body_c19':
        paths.extend([ROOT/'models/L2_r4/analysis_reference/BODY_C18_BEFORE_C19.step',
                      ROOT/'models/L2_r4/validation_features/SWITCH_MIDDLE_MOUNT.step'])
    if stem in ['main_motion_checks','contact_audit','contact_audit_final','combine_motion'] or stem.startswith('motion_'):paths.extend((ROOT/'models/L2_r4/validation_features').glob('*.step'))
    inv=RP/'assembly_inventory.json'
    if inv.exists():paths.extend(ROOT/'models/L2_r4/reference'/(n+'.step') for n in json.loads(inv.read_text())['H_hardware'])
    if stem in ['diagnostic_checks','mesh_metrics','surface_mesh','wall_audit','mesh_self_intersection']:paths.extend(parts.glob('*.stl'))
    report_inputs={'contact_audit':['static_pairs.json','component_pairs.json','side_functional_motion.json'],
        'contact_audit_final':['static_pairs.json','component_pairs.json','side_functional_motion.json'],
        'combine_motion':[f'motion_{g}_{i}.json' for g in ['left','right','wheel'] for i in range(5)],
        'combine_side_motion':[f'side_{g}_{i}.json' for g in ['sf','sr'] for i in range(5)],
        'mesh_metrics':['solids.json'],
        'render':['assembly_inventory.json','side_actuation_force_and_tuning.json','assembly_routes_final.json'],
        'plot_checks':['main_and_wheel_motion_raw.json','side_functional_motion.json']}
    paths.extend(RP/p for p in report_inputs.get(stem,[]))
    paths.extend([ROOT/'cad/rebuild_r2/parameters.json',ROOT/'cad/rebuild_r3_2/electronics.json',ROOT/'reports/rebuild_r3_2/design_metadata.json'])
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
                if cache[p]!=expected:
                    equivalent=hash_matches(ROOT/p,expected)
                    snapshot=r.get('verified_source_snapshots',{}).get(p)
                    if p in r['verifier_source'] and snapshot and (ROOT/snapshot).exists() and (ROOT/p).exists():
                        original=(ROOT/snapshot).read_bytes()
                        equivalent=hashlib.sha256(original).hexdigest()==expected and same_source_text(original,(ROOT/p).read_bytes())
                    if not equivalent:problems.append('Version mismatch: '+p)
        results.append(dict(report=path,passed=not problems,problems=problems))
    return results

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--python',default=sys.executable);ap.add_argument('--script',required=True);a=ap.parse_args()
    before=snapshot();inputs=identity(a.script)
    r=subprocess.run([a.python,'-u',a.script],cwd=ROOT)
    record(a.script,before,inputs,r.returncode);sys.exit(r.returncode)

if __name__=='__main__':main()
