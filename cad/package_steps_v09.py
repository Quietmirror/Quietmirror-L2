"""Losslessly package the three large, named STEP assemblies for GitHub."""
from pathlib import Path
import json,zipfile,shutil

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'exports/v09'
NAMES=[f'quietmirror_V0.9_{n}.step' for n in ('MECHANICAL_ASSEMBLY','ATK_A1_PLUS_ESTIMATED','PAW3950_CUSTOM_ESTIMATED')]
ARCHIVES={n:OUT/(Path(n).stem+'.zip') for n in NAMES}
BODY_ARCHIVE=OUT/'quietmirror_V0.9_BODY_STEP.zip'

def ensure_body_step():
    missing=[OUT/d/'BODY.step' for d in ('placed','print') if not (OUT/d/'BODY.step').exists()]
    if missing:
        with zipfile.ZipFile(BODY_ARCHIVE) as z:
            for target in missing:
                target.parent.mkdir(parents=True,exist_ok=True)
                with z.open('BODY.step') as src,target.open('wb') as dst:shutil.copyfileobj(src,dst)

def package_body():
    with zipfile.ZipFile(BODY_ARCHIVE,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.write(OUT/'placed/BODY.step','BODY.step')
    with zipfile.ZipFile(BODY_ARCHIVE) as z:
        assert z.testzip() is None and z.namelist()==['BODY.step']
        row=dict(archive=str(BODY_ARCHIVE.relative_to(ROOT)),step_bytes=z.getinfo('BODY.step').file_size,zip_bytes=BODY_ARCHIVE.stat().st_size,zip_crc_readback_pass=True,targets=['exports/v09/placed/BODY.step','exports/v09/print/BODY.step'],note='Both BODY files are identical. Extract the single saved CAD solid into either location; helper recreates both on demand.')
    (ROOT/'reports/v09/body_step_archive.json').write_text(json.dumps(row,indent=2),encoding='utf8')
    print('Body STEP packaged',row['zip_bytes'],flush=True)

def ensure_steps():
    ensure_body_step()
    missing=[n for n in NAMES if not (OUT/n).exists()]
    for n in missing:
        with zipfile.ZipFile(ARCHIVES[n]) as z:
            # Only this fixed basename can be extracted into OUT.
            with z.open(n) as src,(OUT/n).open('wb') as dst:shutil.copyfileobj(src,dst)

def main():
    package_body()
    rows=[]
    for n in NAMES:
        archive=ARCHIVES[n]
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.write(OUT/n,n)
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None and z.namelist()==[n]
            rows.append(dict(name=n,archive=str(archive.relative_to(ROOT)),bytes=z.getinfo(n).file_size,compressed_bytes=z.getinfo(n).compress_size,archive_bytes=archive.stat().st_size))
        print('Packed',n,archive.stat().st_size,flush=True)
    (ROOT/'reports/v09/step_archive.json').write_text(json.dumps(dict(files=rows,zip_crc_readback_pass=True,reason='Separate lossless ZIPs keep individual uploads within the GitHub connector transfer limit. Extract the named STEP before opening in CAD.'),indent=2),encoding='utf8')

if __name__=='__main__':main()
