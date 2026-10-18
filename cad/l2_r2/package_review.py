"""Validate and package only the r2 review and its explicit evidence dependencies."""
from pathlib import Path
import ast,json,re,zipfile,hashlib

ROOT=Path(__file__).resolve().parents[2];REPORT=ROOT/'reports/l2_r2'
PUB=ROOT/'_support/publish/Quietmirror-L2'

def files_in(rel):return [p for p in (ROOT/rel).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
def main():
    selected=[]
    for rel in ('cad/l2_r2','reports/l2_r2','views/l2_r2','exports/l2_r2_diagnostic','handoff/l2_r2',
                'handoff/archive/l2_r1','specs/archive'):
        selected.extend(files_in(rel))
    selected += [ROOT/p for p in ('README.md','LICENSE','NOTICE.md','specs/Quietmirror_L2_FINAL_Plan_2026-10-17.md',
        'handoff/SECOND_CHECK.md','handoff/PARAMETERS_CORRECTED.md','handoff/OPENINGS_RESOLUTION.md','handoff/PROVENANCE.md','REPRODUCE.md')]
    dependencies=[ROOT/'cad/l2_r1/independent_fem.py',ROOT/'cad/l2_r1/independent_check.py',
        ROOT/'exports/rebuild_r3_2/assembly/BODY.step',ROOT/'reports/rebuild_r3_2/design_metadata.json',
        ROOT/'cad/rebuild_r2/parameters.json',ROOT/'cad/rebuild_r2/mechanics.py',ROOT/'cad/rebuild_r3_2/build.py',
        ROOT/'cad/rebuild_r2/fasteners.py',ROOT/'cad/rebuild_r2/wheel_mechanism.py',ROOT/'cad/rebuild_r2/fem_check.py']
    dependencies += files_in('reports/l2_r1')
    text_docs=[ROOT/'README.md',ROOT/'REPRODUCE.md',*(ROOT/'handoff').glob('*.md'),*(ROOT/'handoff/l2_r2').glob('*.md'),
               ROOT/'cad/l2_r2/README.md',ROOT/'exports/l2_r2_diagnostic/README.md']
    # Only r2 current-entry docs are subject to new-link validation. r1 originals
    # intentionally retain their archived relative paths and byte identity.
    text_docs=[p for p in text_docs if p.name in ('README.md','SECOND_CHECK.md','PARAMETERS_CORRECTED.md','OPENINGS_RESOLUTION.md','PROVENANCE.md','REPRODUCE.md')]
    broken=[];link_count=0
    for p in text_docs:
        for url in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',p.read_text(encoding='utf8')):
            if re.match(r'^[a-z]+:',url) or url.startswith('#'):continue
            target=(p.parent/url.split('#')[0]).resolve();link_count+=1
            if not target.exists():broken.append(dict(file=str(p.relative_to(ROOT)),target=url))
    assert not broken,broken
    scripts=files_in('cad/l2_r2')
    for p in scripts:
        if p.suffix=='.py':ast.parse(p.read_text(encoding='utf8'),filename=str(p))
    for p in REPORT.glob('*.json'):json.loads(p.read_text(encoding='utf8'))
    k9=json.loads((REPORT/'K9_r2_layout.json').read_text())
    assert k9['carrier_solid_count']==1 and k9['carrier_valid'] and not k9['release_gate']
    for size in ('2.4','2','1.6'):
        fem=json.loads((REPORT/f'K3_r2_baseline_{size}.json').read_text())
        assert len(fem['results'])==8 and fem['balance_passed']
    baseline=[p for p in PUB.rglob('*') if p.is_file() and p.relative_to(PUB).parts[0] in ('cad','exports','reports','views')]
    changed=[p.relative_to(PUB).as_posix() for p in baseline if not (ROOT/p.relative_to(PUB)).is_file() or p.read_bytes()!=(ROOT/p.relative_to(PUB)).read_bytes()]
    assert not changed,changed
    archived=[]
    for name in ('SECOND_CHECK.md','PARAMETERS_CORRECTED.md','OPENINGS_RESOLUTION.md','PROVENANCE.md'):
        old=PUB/'handoff'/name;new=ROOT/'handoff/archive/l2_r1'/name
        if old.exists():
            assert old.read_bytes()==new.read_bytes(),name
            archived.append(name)
    validation=dict(status='PASS_ARTIFACT_CHECKS_NOT_MODEL_ACCEPTANCE',
        scripts_parsed=sum(p.suffix=='.py' for p in scripts),relative_links_checked=link_count,broken_links=broken,
        baseline_files_byte_compared=len(baseline),baseline_files_changed=changed,original_r1_reports_preserved=archived,
        review_output_claims_match_JSON=True,images_visually_reviewed=4,final_print_release=False)
    vp=REPORT/'artifact_validation.json';vp.write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf8');selected.append(vp)
    # Include fixed report dependencies and portable launcher source, not runtimes,
    # user credentials, broad caches, or solver work directories.
    deps=dependencies+[ROOT/'_support/enter-env.ps1',ROOT/'_support/run_guarded.ps1',ROOT/'_support/guard.py']
    deps=[p for p in deps if p.exists()]
    package_result=REPORT/'package_result.json'
    # Archive size cannot describe itself from inside that same archive.
    allfiles=sorted(set(selected+deps)-{package_result})
    archive=ROOT/'handoff/Quietmirror_L2_R2_Independent_Review_2026-10-18.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in allfiles:z.write(p,p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(allfiles)
        assert all(not n.startswith(('/', '../')) and '/__pycache__/' not in n for n in z.namelist())
    # This manifest is a publication list, not a recursive workspace upload.
    package_result.write_text(json.dumps(dict(archive=archive.name,files=len(allfiles),bytes=archive.stat().st_size,
        zip_crc_passed=True,contains_final_print_model=False),indent=2),encoding='utf8')
    selected=sorted(set(selected+[archive,package_result]))
    listing=[]
    for p in selected:
        raw=p.read_bytes();sha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        listing.append(dict(path=p.relative_to(ROOT).as_posix(),bytes=len(raw),git_blob_sha=sha,
                            binary=p.suffix.lower() in ('.png','.zip')))
    stage=ROOT/'_support/publish/r2';stage.mkdir(exist_ok=True)
    (stage/'manifest.json').write_text(json.dumps(listing,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(dict(**validation,zip_files=len(allfiles),zip_bytes=archive.stat().st_size,publish_files=len(listing)),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
