"""Package the actual final CAD/print files without altering old releases."""
from pathlib import Path
import json,zipfile,hashlib,shutil
ROOT=Path(__file__).resolve().parents[2];RP=ROOT/'reports/rebuild_r2';OUT=ROOT/'exports/rebuild_r2'
DEST=ROOT/'releases/Fenrir-MiniSE-R2'
def archive(name,files):
    target=DEST/name
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(files):z.write(p,p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        for p in files:assert z.read(p.relative_to(ROOT).as_posix())==p.read_bytes()
    return target
def main():
    DEST.mkdir(parents=True,exist_ok=True)
    met=json.loads((RP/'cad_metrics.json').read_text())
    printed=[n for n,v in met.items() if v['printable']]
    common=[ROOT/'LICENSE',RP/'NOTICE_R2.md',RP/'INSTALLATION.md',RP/'DESIGN.md']
    artifacts=[archive('R2_PRINT_STL.zip',[OUT/f'print/{n}.stl' for n in printed]+common),
               archive('R2_STEP.zip',list((OUT/'assembly').glob('*.step'))+list((OUT/'gauges').glob('*.step'))+[OUT/'FENRIR_MINISE_R2_ASSEMBLY.step']+common)]
    for name in ('FENRIR_MINISE_R2.FCStd','FENRIR_MINISE_R2_PLA_PRINT_PLATE.3mf'):
        shutil.copyfile(OUT/name,DEST/name);artifacts.append(DEST/name)
    old=DEST/'R1_07fcd46_UNACCEPTED.zip'
    if old.exists():
        with zipfile.ZipFile(old) as z:assert z.testzip() is None
        artifacts.append(old)
    rows=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in artifacts]
    (RP/'package_checks.json').write_text(json.dumps(dict(artifacts=rows,zip_member_readback=True,printed_parts=printed),indent=2),encoding='utf8')
    print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
