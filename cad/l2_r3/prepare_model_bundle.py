"""Freeze measured models/views for upload while numerical checks finish."""
from pathlib import Path
import hashlib,json,zipfile,base64
ROOT=Path(__file__).resolve().parents[2];STAGE=ROOT/'_support/publish/r3';STAGE.mkdir(parents=True,exist_ok=True)
def main():
    files=[]
    for folder in ['models/L2_r3','views/l2_r3']:
        files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix in ['.step','.stl','.3mf','.FCStd','.png'])
    manifest=[];archive=ROOT/'releases/L2-r3-bundle.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(files):
            data=p.read_bytes();name=p.relative_to(ROOT).as_posix();sha=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
            assert len(data)<50_000_000,name
            manifest.append(dict(path=name,bytes=len(data),git_blob_sha=sha));z.writestr(name,data)
        z.writestr('MANIFEST.json',json.dumps(manifest,indent=2))
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    (STAGE/'model_manifest.json').write_text(json.dumps(manifest,indent=2))
    payloads=[];raw=archive.read_bytes()
    for j,start in enumerate(range(0,len(raw),5_000_000),1):
        name=f'releases/L2-r3-bundle.zip.{j:03}';data=raw[start:start+5_000_000];(ROOT/name).write_bytes(data)
        b64=base64.b64encode(data).decode();chunks=[]
        for k,begin in enumerate(range(0,len(b64),180000)):
            p=STAGE/f'model_seed_{j}_{k:03}.txt';p.write_text(b64[begin:begin+180000],encoding='ascii');chunks.append(str(p))
        payloads.append(dict(path=name,bytes=len(data),git_blob_sha=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(),chunks=chunks,base64_length=len(b64)))
    (STAGE/'model_payloads.json').write_text(json.dumps(payloads,indent=2));print('Frozen',len(files),'models/views;',len(raw),'compressed bytes;',len(payloads),'upload segments',flush=True)
if __name__=='__main__':main()
