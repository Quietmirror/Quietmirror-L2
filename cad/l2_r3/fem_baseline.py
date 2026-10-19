"""Re-use our independent load integration, with the newly specified mesh settings."""
from pathlib import Path
import argparse, importlib.util
from fem_mesh import core, mesh, ROOT
spec=importlib.util.spec_from_file_location('independent_r2_loads',ROOT/'cad/l2_r2/fem_recheck.py')
loads=importlib.util.module_from_spec(spec);spec.loader.exec_module(loads)
loads.core=core
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--size',type=float,default=2.4);ap.add_argument('--beam',action='store_true');a=ap.parse_args()
    if a.beam:core.beam(a.size)
    else:
        loads.body(a.size)
        p=core.OUT/f'K3_r2_baseline_{a.size:g}.json'
        p.rename(core.OUT/f'K3_r3_baseline_{a.size:g}.json')
