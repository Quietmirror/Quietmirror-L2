# Collect every L2 / r4 FEM run (from the solver logs) into one JSON with R3.2 ratios at the same mesh size.
import json, re
from pathlib import Path
H = Path(__file__).resolve().parent
R = {}
for r in json.load(open(H/'fem_summary.json')):
    if r['variant'] == 'R32': R[(r['size'], r['case'])] = r['stiffness_N_per_mm']
runs = [('fem_L2_2.4.log', ['L2r3'], 2.4), ('fem_reinf.log', ['L2y54', 'L2tie'], 2.4), ('fem_frame.log', ['L2frame', 'L2frametie'], 2.4),
        ('fem_diag.log', ['L2frametiedia'], 2.4), ('fem_V1.log', ['V1'], 2.4), ('fem_V2.log', ['V2'], 2.4), ('fem_V3.log', ['V3'], 2.4),
        ('fem_V2_20.log', ['V2'], 2.0), ('fem_V2_16.log', ['V2'], 1.6)]
desc = {'L2r3': 'released L2-r3 BODY (models/L2_r3/parts/BODY.step @1ac9de77)', 'L2y54': 'L2r3 + Y54 outer arms restored',
        'L2tie': 'L2r3 + lower cross tie d2.0 @Y56 Z8.6', 'L2frame': 'L2r3 + side frame fused into BODY (r4_frame.json)',
        'L2frametie': 'L2frame + lower cross tie', 'L2frametiedia': 'L2frametie + rear diagonals restored to d2.6 round',
        'V1': 'L2frametie + bearing struts d2.4 @(+-9.9, 40.8)', 'V2': 'V1 + Y67.5 tie r1.5  (SELECTED r4)', 'V3': 'V1 + rear high tie r1.2 @Y75.5 Z21'}
pat = re.compile(r'^\s+(\S+)\s+delta\s+([\d.]+) mm\s+k\s+([\d.]+) N/mm\s+umax\s+([\d.]+)\s+p95\s+([\d.]+)\s+eq\s+(\w+)')
out = []
for log, variants, size in runs:
    rows = [m.groups() for m in (pat.match(l) for l in open(H/log, encoding='utf-8', errors='ignore')) if m]
    for i, v in enumerate(variants):
        for case, d, k, um, p95, eq in rows[i*6:(i+1)*6]:
            ref = R.get((size, case)); k = float(k)
            out.append(dict(variant=v, description=desc[v], mesh_mm=size, case=case, k_N_per_mm=k, R32_k=ref, ratio=round(k/ref, 4) if ref else None,
                            umax_mm=float(um), vm_p95_MPa=float(p95), equilibrium=eq == 'True'))
json.dump(dict(note='E 1500 MPa, nu 0.35; FINAL-plan load definitions (fem_variants.cases) without the two R3.2 side-fence cases; R32 refs from fem_summary.json',
               rows=out), open(H/'fem_r4_results.json', 'w'), indent=1)
for r in out: print(r['variant'], r['mesh_mm'], r['case'], r['k_N_per_mm'], r['ratio'])
