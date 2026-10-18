"""Adopt the user-approved r2 plan without deleting r1 review evidence."""
from pathlib import Path
import json, shutil

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(r'C:\Users\38982\Downloads\Quietmirror_L2_FINAL_Plan_2026-10-17 (1).md')
CURRENT = ROOT/'specs/Quietmirror_L2_FINAL_Plan_2026-10-17.md'
ARCHIVE = ROOT/'specs/archive/Quietmirror_L2_FINAL_Plan_2026-10-17_r1.md'

def main():
    for rel in ('reports/l2_r2', 'views/l2_r2', 'exports/l2_r2_diagnostic',
                'handoff/archive/l2_r1', 'handoff/l2_r2', '_support/work/review_r2'):
        (ROOT/rel).mkdir(parents=True, exist_ok=True)
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    if not ARCHIVE.exists():
        assert 'r2 修订：2026-10-18' not in CURRENT.read_text(encoding='utf8')
        shutil.copy2(CURRENT, ARCHIVE)
    for name in ('SECOND_CHECK.md','PARAMETERS_CORRECTED.md','OPENINGS_RESOLUTION.md','PROVENANCE.md'):
        dst=ROOT/'handoff/archive/l2_r1'/name
        if not dst.exists():shutil.copy2(ROOT/'handoff'/name,dst)
    readme_archive=ROOT/'handoff/archive/l2_r1/ROOT_README.md'
    if not readme_archive.exists():shutil.copy2(ROOT/'README.md',readme_archive)
    assert 'r2 修订：2026-10-18' in SOURCE.read_text(encoding='utf8')
    shutil.copy2(SOURCE, CURRENT)
    status=dict(plan_revision='r2_2026-10-18',source=str(SOURCE),active_plan=str(CURRENT),
                previous_plan=str(ARCHIVE),authorization='User: 替代现有方案，继续独立复核修正项',
                scope='Adopt plan and independently review changed items; not final production CAD',
                previous_review='reports/l2_r1 and handoff/archive/l2_r1 retained',
                memory_cap_gib=4,heavy_jobs='serial; existing Windows Job guard',
                donor='ATK A1 Plus as originally named by user; identity unconfirmed',
                missing_author_inputs=['fem3d/fem_variants.py','l2_repo_scan/',
                                       'Quietmirror_L2_Repo_Scan_Recheck_2026-10-18.md'])
    (ROOT/'reports/l2_r2/plan_adoption.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(status,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
