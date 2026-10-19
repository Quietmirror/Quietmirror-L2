"""Finalize source/report text after freezing the measured model bundle."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2];STAGE=ROOT/'_support/publish/r3'
def blob(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def main():
    model=json.loads((STAGE/'model_manifest.json').read_text())
    for r in model:assert blob((ROOT/r['path']).read_bytes())==r['git_blob_sha'],('Frozen model changed',r['path'])
    summary=json.loads((ROOT/'reports/l2_r3/release_summary.json').read_text(encoding='utf8'))
    assert summary['status']=='INCOMPLETE' and summary['prerelease'] is True
    files=[ROOT/'README.md',ROOT/'REPRODUCE.md',ROOT/'.github/workflows/l2-r3-release.yml',ROOT/'specs/Quietmirror_L2_r3_FINAL_Build_and_Release_2026-10-18.md',ROOT/'specs/archive/Quietmirror_L2_FINAL_Plan_2026-10-17_r2.md']
    for folder in ['cad/l2_r3','reports/l2_r3','handoff/l2_r3','handoff/archive/l2_r2']:
        files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix in ['.py','.ini','.json','.md','.txt'])
    manifest=list(model);entries=[]
    for p in sorted(set(files)):
        data=p.read_bytes();name=p.relative_to(ROOT).as_posix()
        manifest.append(dict(path=name,bytes=len(data),git_blob_sha=blob(data)))
        entries.append(dict(path=name,mode='100644',type='blob',content=data.decode('utf8')))
    manifest.sort(key=lambda r:r['path'])
    raw=json.dumps(manifest,indent=2,ensure_ascii=False)+'\n'
    (ROOT/'releases/L2-r3-files.json').write_bytes(raw.encode('utf8'))
    (STAGE/'manifest.json').write_bytes(raw.encode('utf8'))
    entries.append(dict(path='releases/L2-r3-files.json',mode='100644',type='blob',content=raw))
    text=json.dumps(entries,ensure_ascii=False);paths=[]
    for j,start in enumerate(range(0,len(text),120000)):
        p=STAGE/f'text_entries_{j:03}.txt';p.write_text(text[start:start+120000],encoding='utf8');paths.append(str(p))
    (STAGE/'text_entries_index.json').write_text(json.dumps(dict(characters=len(text),entries=len(entries),chunks=paths),indent=2))
    lines=['Branch: l2-r3','Tag: L2-r3','Release: INCOMPLETE / prerelease','']+[f"{r['path']} ({r['bytes']} bytes)" for r in manifest]+['','Model/view bundle is separate from text; GitHub source archives include the full repository.','History: base tree retained; old root landing pages archived before replacement.']
    (STAGE/'PUBLICATION_FILES.txt').write_text('\n'.join(lines),encoding='utf8');print('\n'.join(lines),flush=True)
if __name__=='__main__':main()
