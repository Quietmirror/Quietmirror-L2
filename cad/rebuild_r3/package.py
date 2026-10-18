"""Versioned R3 deliverables with byte-for-byte archive readback."""
from pathlib import Path
import json,zipfile,hashlib,shutil
ROOT=Path(__file__).resolve().parents[2];RP=ROOT/'reports/rebuild_r3';OUT=ROOT/'exports/rebuild_r3';DEST=ROOT/'releases/Fenrir-MiniSE-R3'
def archive(name,files):
    target=DEST/name;files=sorted(set(files))
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
        for p in files:z.write(p,p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        for p in files:assert z.read(p.relative_to(ROOT).as_posix())==p.read_bytes()
    return target
def main():
    DEST.mkdir(parents=True,exist_ok=True)
    met=json.loads((RP/'cad_metrics.json').read_text());printed=[n for n,v in met.items() if v['printable']]
    common=[ROOT/'LICENSE',ROOT/'NOTICE.md',RP/'NOTICE_R3.md',RP/'INSTALLATION.md',RP/'COMPATIBILITY.md',RP/'README.md']
    arts=[archive('R3_PRINT_STL.zip',[OUT/f'print/{n}.stl' for n in printed]+common),
          archive('R3_STEP.zip',list((OUT/'assembly').glob('*.step'))+list((OUT/'gauges').glob('*.step'))+list((OUT/'electronics').rglob('*.step'))+list(OUT.glob('*.step'))+common)]
    sources=[]
    for version in ('rebuild_r2','rebuild_r3'):
        sources.extend(p for p in (ROOT/'cad'/version).glob('*') if p.is_file())
    base=[p for sub in ('assembly','print','gauges') for p in (ROOT/'exports/rebuild_r2'/sub).glob('*') if p.suffix.lower() in ('.step','.stl')]
    required=[ROOT/'reports/rebuild_r2'/n for n in ['cad_metrics.json','design_metadata.json','NOTICE_R2.md']]
    required += [ROOT/'slicing/V0.6_PLA_0.4_0.20_ESTIMATE.ini',ROOT/'README_R2.md',ROOT/'HISTORY_R3.md']
    arts.append(archive('R3_SOURCE_AND_BASE.zip',sources+base+required+common))
    for n in ['FENRIR_MINISE_R3.FCStd','FENRIR_MINISE_R3_PLA_PRINT_PLATE.3mf']:
        shutil.copyfile(OUT/n,DEST/n);arts.append(DEST/n)
    report=dict(artifacts=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in arts],
        zip_member_readback=True,printed_parts=printed,history_overwritten=False,
        scenario_status={'mechanical':'nominal finite geometry accepted, physical trial pending','custom_PAW3950':'estimated envelopes only, not electronics manufacturing release','ATK':'intentional failure diagnostic, actual board unknown'})
    (RP/'package_checks.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
