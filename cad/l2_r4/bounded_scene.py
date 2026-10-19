"""Exact nearest scene distance with certified cropped-BODY exclusion.

Measure inexpensive rigid components before the large frame. An omitted
frame region is farther than the crop padding from every point of the actor.
If both that bound and the exact cropped distance exceed an already measured
minimum and the criterion, the frame cannot change the result. Such rows are
recorded only as pruning proofs, never as measured minimum distances.
"""
import math
from collections import OrderedDict
import numpy as np
from common import pair as exact_pair,box
_cache=OrderedDict()

def scene_pairs(actor,obstacles,name,minimum=.3):
    aa=actor.BoundingBox();queue=[]
    for n,b in obstacles.items():
        bb=b.BoundingBox();delta=[max(0.,getattr(aa,c+'min')-getattr(bb,c+'max'),getattr(bb,c+'min')-getattr(aa,c+'max')) for c in 'xyz']
        queue.append((float(np.linalg.norm(delta)),n,b))
    queue.sort(key=lambda r:(r[1]=='BODY',r[0]));best=float('inf');measured=[];pruned=[]
    for lower,n,b in queue:
        threshold=max(best,minimum)
        if lower>threshold+1e-6:
            pruned.append(dict(part=n,lower_bound_mm=lower,reason='Cannot improve previously measured exact minimum or violate required clearance'));continue
        if n=='BODY' and math.isfinite(threshold) and threshold<3.-1e-6:
            pad=3.;limits=tuple(q for c in 'xyz' for q in [math.floor(getattr(aa,c+'min'))-pad,math.ceil(getattr(aa,c+'max'))+pad])
            key=(id(b),limits)
            if key in _cache:_,crop=_cache[key];_cache.move_to_end(key)
            else:
                crop=b.intersect(box(*limits));_cache[key]=(b,crop)
                if len(_cache)>64:_cache.popitem(last=False)
            if not crop.Solids():
                pruned.append(dict(part=n,lower_bound_mm=pad,crop_bounds_xyz_mm=limits,reason='Exact frame crop empty; all omitted frame points farther than3mm; existing measured minimum and criterion are smaller'));continue
            r=exact_pair(actor,crop,name,'FRAME_CROP',minimum)
            if r['gap_mm']>=pad-1e-6:
                pruned.append(dict(part=n,lower_bound_mm=pad,crop_exact_gap_mm=r['gap_mm'],crop_bounds_xyz_mm=limits,reason='Exact crop gap and omitted-region bound both exceed existing measured minimum and criterion'));continue
            r['b']=n;r['distance_kind']='BRepExtrema_exact_crop_certified_global_minimum_below_3mm'
        else:r=exact_pair(actor,b,name,n,minimum)
        measured.append(r);best=min(best,r['gap_mm'])
    return dict(exact_global_minimum_mm=best,measured_pairs=measured,pruned_pairs=pruned,passed=all(r['pass_check'] for r in measured))
