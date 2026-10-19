"""Derive a lower-memory solver deck without altering geometry or load data."""
from pathlib import Path
import argparse,json
ROOT=Path(__file__).resolve().parents[2]
ap=argparse.ArgumentParser();ap.add_argument('--work',default='_support/work/fem_r3/R32_2.4_curvature24');a=ap.parse_args()
work=ROOT/a.work;src=work/'independent.inp';dst=work/'iterative.inp'
text=src.read_text();assert '\n*STATIC\n' in text
dst.write_text(text.replace('\n*STATIC\n','\n*STATIC,SOLVER=ITERATIVE SCALING\n'))
(work/'iterative_method.json').write_text(json.dumps(dict(source='independent.inp',change='Only *STATIC solver selection changed to ITERATIVE SCALING',basis='CalculiX official *STATIC reference: diagonal scaling uses less memory than direct factorization',geometry_loads_material_constraints_unchanged=True,solution_acceptance='Requires completed solver, force/moment residual checks and independent beam validation'),indent=2))
print(dst)
