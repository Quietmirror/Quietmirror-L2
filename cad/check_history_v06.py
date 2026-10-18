"""Confirm all prior version assets remain byte-identical to V0.5 Git blobs."""
from pathlib import Path
import subprocess,json
ROOT=Path(__file__).resolve().parents[1];base='ee4740639524cfde4e8b4c8cb39321150638cf51'
allowed={'README.md','HISTORY.md','requirements.txt','cad/analyze_slice.py','cad/check_3mf_roundtrip.py','cad/embed_3mf_profile.py','cad/render_views.py'}
rows=[];changes=[]
for line in subprocess.check_output(['git','ls-tree','-r','-z',base]).decode('utf8').split('\0'):
    if not line:continue
    meta,path=line.split('\t');sha=meta.split()[2]
    if path in allowed:changes.append(path);continue
    file=ROOT/path;assert file.exists(),path
    actual=subprocess.check_output(['git','hash-object','--path='+path,str(file)],text=True).strip()
    assert actual==sha,path
    rows.append(dict(path=path,unchanged=True))
archive=subprocess.check_output(['git','hash-object','--path=README_V0.5.md',str(ROOT/'README_V0.5.md')],text=True).strip()
old=subprocess.check_output(['git','rev-parse',base+':README.md'],text=True).strip();assert archive==old
report=dict(baseline_commit=base,unchanged_previous_files=len(rows),verified_files=rows,allowed_shared_or_index_updates=changes,readme_v05_exact_archive=True,note='Prior models, parameters, version-specific generators, reports, images and profiles are preserved. Shared scripts add V0.6 support; no old exports overwritten.')
(ROOT/'reports/v06/history_preservation.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('Unchanged historical files:',len(rows),'README V0.5 exact archive:',archive==old)
