"""Exact checks of the actual candidate; failures are data, never a release pass.

The gate aggregation runs only after any reported exceptions have been resolved.
This intentionally keeps the full-body distances, including functional contacts,
visible rather than silently treating every BODY/lever pair as an exception.
"""
import itertools,json,math,time
import numpy as np
import trimesh
from common import *
from exact_distance import pair
from side_module import KEYS,RETAINER_MOUNTS,UPPER_LUG_TOP

def main():
    parts={p.stem:load(p.stem) for p in sorted((OUT/'parts').glob('*.step'))}
    static=[]
    for (an,a),(bn,b) in itertools.combinations(parts.items(),2):
        row=pair(a,b,an,bn,.3);static.append(row);save('static_pairs.json',static)
        if not row['pass_check']:print('STATIC_REVIEW',row,flush=True)

if __name__=='__main__':main()
