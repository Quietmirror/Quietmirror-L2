# Summarise fem_summary.json: stiffness ratios vs R32 per case and mesh level, convergence, stress, volume.
import json, sys
from pathlib import Path
from collections import defaultdict
HERE = Path(__file__).resolve().parent
rows = json.load(open(HERE/'fem_summary.json'))
base = sys.argv[1] if len(sys.argv) > 1 else 'R32'
S = defaultdict(dict)                      # (variant, size) -> case -> row
for r in rows: S[(r['variant'], r['size'])][r['case']] = r
variants = sorted({r['variant'] for r in rows}, key=lambda v: (v != base, v))
sizes = sorted({r['size'] for r in rows}, reverse=True)
cases = list(dict.fromkeys(r['case'] for r in rows))
out = dict(base=base, sizes=sizes, variants=variants, table=[])
print(f'base {base}; sizes {sizes}')
for size in sizes:
    print(f'\n== mesh {size} mm ==')
    for v in variants:
        if (v, size) not in S: continue
        any_r = next(iter(S[(v, size)].values()))
        print(f'  {v}: nodes {any_r["nodes"]} elements {any_r["elements"]}')
    print(f'  {"case":32s}' + ''.join(f'{v:>22s}' for v in variants))
    for c in cases:
        line = f'  {c:32s}'
        for v in variants:
            r = S.get((v, size), {}).get(c); b = S.get((base, size), {}).get(c)
            if not r or not b: line += f'{"-":>22s}'; continue
            ratio = r['stiffness_N_per_mm']/b['stiffness_N_per_mm']
            line += f'{r["stiffness_N_per_mm"]:9.2f} ({ratio*100:6.1f}%)'
            out['table'].append(dict(size=size, case=c, variant=v, k=r['stiffness_N_per_mm'], ratio=ratio,
                                     p95=r['vm_p95_MPa'], vmax=r['vm_max_MPa'], umax=r['umax_mm'], eq=r['equilibrium_pass']))
        print(line)
print('\n== stiffness ratio vs base across mesh levels (convergence) ==')
for v in variants:
    if v == base: continue
    for c in cases:
        vals = [t['ratio'] for t in out['table'] if t['variant'] == v and t['case'] == c]
        if vals: print(f'  {v:5s} {c:32s} ' + '  '.join(f'{x*100:6.1f}%' for x in vals) + f'   spread {max(vals)*100-min(vals)*100:4.1f} pts')
print('\n== P95 von Mises (MPa) at finest common mesh ==')
fin = min(s for s in sizes if all((v, s) in S for v in variants)) if all(any((v, s) in S for s in sizes) for v in variants) else sizes[-1]
for c in cases:
    print(f'  {c:32s}' + ''.join(f'{S[(v, fin)][c]["vm_p95_MPa"]:10.3f}' if c in S.get((v, fin), {}) else f'{"-":>10s}' for v in variants))
print('\nequilibrium all pass:', all(t['eq'] for t in out['table']))
json.dump(out, open(HERE/'fem_analysis.json', 'w'), indent=1)
