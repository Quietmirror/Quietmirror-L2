"""Exact full-shape minimum with AABBs used solely for safe pair exclusion."""
import numpy as np
from exact_distance import pair as exact_pair

def scene_pairs(actor,obstacles,name,minimum=.3):
    aa=actor.BoundingBox();queue=[]
    for n,b in obstacles.items():
        bb=b.BoundingBox();delta=[max(0.,getattr(aa,c+'min')-getattr(bb,c+'max'),getattr(bb,c+'min')-getattr(aa,c+'max')) for c in 'xyz']
        queue.append((float(np.linalg.norm(delta)),n,b))
    queue.sort(key=lambda r:(r[1]=='BODY',r[0]));best=float('inf');measured=[];pruned=[]
    for lower,n,b in queue:
        if lower>max(best,minimum)+1e-6:
            pruned.append(dict(part=n,lower_bound_mm=lower,reason='AABB proves this pair cannot improve an already measured exact minimum or violate clearance'));continue
        r=exact_pair(actor,b,name,n,minimum);measured.append(r);best=min(best,r['gap_mm'])
    return dict(exact_global_minimum_mm=best,measured_pairs=measured,pruned_pairs=pruned,passed=all(r['pass_check'] for r in measured))
