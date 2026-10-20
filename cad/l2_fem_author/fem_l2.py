# G8 probe: final L2-r3 BODY vs R3.2 with the FINAL-plan load definitions (fem_variants.cases), minus the two
# R3.2 side-switch fence cases (those fences no longer exist in L2; the side load path is checked under S7).
# Writes fem_summary_L2.json (does not touch fem_summary.json).
import sys, json, shutil
from pathlib import Path
import fem_variants as FV

HERE = Path(__file__).resolve().parent
src = Path(r'D:\Quietmirror_L2\l2_r4\inputs\BODY.step')
dst = HERE/'variants'/'BODY_L2r3.step'
if not dst.exists(): shutil.copy(src, dst)
FV.META['mechanisms']['side_motions'] = []            # no R3.2 side fences in L2 -> skip those two cases
_dump = json.dump
def dump(obj, fp, *a, **k):
    name = getattr(fp, 'name', '')
    if name.endswith('fem_summary.json'):
        fp.close(); fp = open(HERE/'fem_summary_L2.json', 'w')
    return _dump(obj, fp, *a, **k)
FV.json.dump = dump
orig = HERE/'fem_summary.json'; keep = HERE/'fem_summary_R32_P0P1P7_backup.json'
if not keep.exists(): shutil.copy(orig, keep)          # FV.main opens fem_summary.json for writing (truncates) -> restore after
sizes = [float(s) for s in (sys.argv[1] if len(sys.argv) > 1 else '2.4').split(',')]
try:
    FV.main(sizes, (sys.argv[2] if len(sys.argv) > 2 else 'L2r3').split(','))
finally:
    shutil.copy(keep, orig)
