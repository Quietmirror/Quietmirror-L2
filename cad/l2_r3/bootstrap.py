"""Adopt the supplied r3 brief without rewriting any previous revision."""
from pathlib import Path
import json, shutil
ROOT=Path(__file__).resolve().parents[2]
for sub in ('cad/l2_r3','reports/l2_r3','views/l2_r3','models/L2_r3/parts','models/L2_r3/reference','handoff/l2_r3','_support/work/l2_r3','_support/work/fem_r3','_support/logs','specs/archive'):
    (ROOT/sub).mkdir(parents=True,exist_ok=True)
source=Path.home()/'Downloads/Quietmirror_L2_r3_FINAL_Build_and_Release_2026-10-18.md'
target=ROOT/'specs'/source.name
if target.exists(): assert target.read_bytes()==source.read_bytes()
else: shutil.copy2(source,target)
old=ROOT/'specs/Quietmirror_L2_FINAL_Plan_2026-10-17.md'
archive=ROOT/'specs/archive/Quietmirror_L2_FINAL_Plan_2026-10-17_r2.md'
if not archive.exists():shutil.copy2(old,archive)
data=dict(version='L2-r3',status='IN_PROGRESS',source=source.name,
    adoption='User explicitly authorized independent review, modeling and GitHub publication; incomplete acceptance must be a pre-release.',
    missing_author_inputs=['l2_r3_check/r3_parameters.json','l2_r3_check/*.py and *.step','fem3d/fem_variants.py','l2_repo_scan/','background plan r3'],
    numerical_source='Independent transcription of supplied r3 brief, not the absent author JSON.',
    corrections=['Stop rib height is 0.5 mm from Z15.9..16.4; retain both specified end planes.',
                 'Trigger guarantee requires shim adjustment to 0..0.03 mm residual gap.',
                 'Use existing -MemoryGiB 4 guard rather than nonexistent -LimitGB 8.',
                 'Donor user designation remains ATK A1 Plus, exact product and PCB unverified.'],
    unchanged_baseline='Quietmirror/github@f1b1090931d717117287ea2b79c2e14ddc234937',
    inherited_review='Quietmirror/Quietmirror-L2@ab2240f3f60f553606c0d2bbb4ad78691ef51ec1')
(ROOT/'reports/l2_r3/adoption.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
print('r3 brief adopted; old r2 plan archived; absent author files recorded')
