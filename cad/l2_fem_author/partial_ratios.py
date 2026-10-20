# Print stiffness ratios vs R32 for whatever variants/sizes are already in fem_summary.json
import json
from pathlib import Path
rows = json.load(open(Path(__file__).resolve().parent/'fem_summary.json'))
R = {(r['variant'], r['size'], r['case']): r for r in rows}
for size in sorted({r['size'] for r in rows}, reverse=True):
    cases = [r['case'] for r in rows if r['variant'] == 'R32' and r['size'] == size]
    for v in ('P0d', 'P1d', 'P7d'):
        for c in cases:
            a = R.get((v, size, c)); b = R.get(('R32', size, c))
            if a and b:
                print(f"h{size} {v} {c:32s} k {a['stiffness_N_per_mm']:8.2f}  {a['stiffness_N_per_mm']/b['stiffness_N_per_mm']*100:6.1f}%  p95 {a['vm_p95_MPa']:.3f} (R32 {b['vm_p95_MPa']:.3f})")
