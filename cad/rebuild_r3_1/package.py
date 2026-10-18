"""Package R3.1 without replacing any historical archive."""
from pathlib import Path
import json,zipfile,hashlib,shutil
ROOT=Path(__file__).resolve().parents[2];RP=ROOT/'reports/rebuild_r3_1';OUT=ROOT/'exports/rebuild_r3_1';DEST=ROOT/'releases/Fenrir-MiniSE-R3.1'
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
    common=[ROOT/'LICENSE',ROOT/'NOTICE.md',RP/'NOTICE_R3_1.md',RP/'README.md',ROOT/'reports/rebuild_r3/INSTALLATION.md',ROOT/'reports/rebuild_r3/COMPATIBILITY.md']
    arts=[archive('R3_1_PRINT_STL.zip',[OUT/f'print/{n}.stl' for n in printed]+common),
        archive('R3_1_STEP.zip',list(OUT.glob('*.step'))+[OUT/'assembly/BODY.step',OUT/'gauges/SENSOR_RESERVED_VOLUME.step']+common)]
    sources=[p for ver in ('rebuild_r2','rebuild_r3','rebuild_r3_1') for p in (ROOT/'cad'/ver).glob('*') if p.is_file()]
    arts.append(archive('R3_1_SOURCE.zip',sources+common+[ROOT/'README_R3.md',ROOT/'HISTORY_R3_1.md']))
    for n in ['FENRIR_MINISE_R3_1.FCStd','FENRIR_MINISE_R3_1_PLA_PRINT_PLATE.3mf']:
        shutil.copyfile(OUT/n,DEST/n);arts.append(DEST/n)
    report=dict(artifacts=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in arts],
        zip_member_readback=True,printed_parts=printed,history_overwritten=False,
        source_geometry_base='Immutable R3_SOURCE_AND_BASE.zip at commit da06237d066d8d4a6133f03f9929cff5bdd7a50e; see ENVIRONMENT.md')
    (RP/'package_checks.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
