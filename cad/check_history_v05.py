"""Confirm prior version files are retained against the published V0.4 commit."""
from pathlib import Path
import subprocess,json
ROOT=Path(__file__).resolve().parents[1]
BASE='4316b3531f2956c5623ffef4c64e8b869d723e04'
MUTABLE={'README.md','HISTORY.md','NOTICE.md','requirements.txt','cad/analyze_slice.py','cad/check_3mf_roundtrip.py','cad/embed_3mf_profile.py','cad/make_diagrams.py'}
entries=[]
for raw in subprocess.check_output(['git','ls-tree','-r','-z',BASE],cwd=ROOT).split(b'\0'):
    if not raw:continue
    meta,name=raw.split(b'\t',1);path=name.decode('utf8');mode,kind,sha=meta.decode().split()
    if path in MUTABLE:continue
    assert (ROOT/path).is_file(),path
    now=subprocess.check_output(['git','hash-object','--path',path,path],cwd=ROOT,text=True).strip()
    assert now==sha,(path,sha,now)
    entries.append(dict(path=path,git_blob=sha,unchanged=True))
assert (ROOT/'README_V0.4.md').read_bytes()==subprocess.check_output(['git','show',BASE+':README.md'],cwd=ROOT)
versions=[]
for v in ('0.1','0.2','0.3','0.4','0.5'):
    folder='exports/' if v=='0.1' else f"exports/v{v.replace('.','')}/"
    stem=f'quietmirror_fingertip_V{v}'+('_FIT' if v in ('0.3','0.4','0.5') else '')
    assets=[folder+stem+'.stl',folder+stem+'.step',folder+f'quietmirror_fingertip_V{v}_PRINT.3mf']
    assert all((ROOT/a).is_file() for a in assets),v
    versions.append(dict(version=v,core_assets=assets,all_present=True))
report=dict(reference_commit=BASE,method='Git canonical blob identity, with repository text normalization; each historical file compared once',protected_files_checked=len(entries),all_unchanged=True,readme_v04_archived_exactly=True,shared_files_updated=sorted(MUTABLE),version_assets=versions,files=entries)
(ROOT/'reports/v05/history_preservation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2))
