import numpy as np
from pathlib import Path
import json
import cadquery as cq
import math
from collections import OrderedDict
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OUT=ROOT/'models/L2_r4';RP=ROOT/'reports/l2_r4';WORK=ROOT/'_support/work/l2_r4'
V=cq.Vector
_BODY_CLIP_CACHE=OrderedDict()
def save(name,data):
    (RP/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def vol(s):
    if not s.Solids():return 0.
    p=GProp_GProps();BRepGProp.VolumeProperties_s(s.wrapped,p,1e-8,True,False);return p.Mass()
def box(x0,x1,y0,y1,z0,z1):return cq.Solid.makeBox(x1-x0,y1-y0,z1-z0,V(x0,y0,z0))
def cyl(r,h,p,axis=(0,0,1)):return cq.Solid.makeCylinder(r,h,V(*p),V(*axis))
def unite(*shapes):
    result=shapes[0]
    for s in shapes[1:]:result=result.fuse(s)
    return result.clean()
def bounds(s):
    b=s.BoundingBox();return [b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]
def load(name,base=None):return cq.importers.importStep(str((base or OUT/'parts')/(name+'.step'))).val()
def baseline(n):return load(n,ROOT/'exports/rebuild_r3_2/assembly')
def valid(s,n):
    if not s.isValid() or len(s.Solids())!=1:raise RuntimeError(f'{n}: valid={s.isValid()} solids={len(s.Solids())}')
    return s.Solids()[0]
def export(s,n,printable=True):
    s=valid(s,n);folder=OUT/('parts' if printable else 'reference');folder.mkdir(exist_ok=True)
    path=folder/(n+'.step');cq.exporters.export(s,str(path))
    back=valid(cq.importers.importStep(str(path)).val(),n+' STEP roundtrip')
    row=dict(name=n,printable=printable,valid=True,solids=1,volume_mm3=vol(back),bounds_mm=bounds(back))
    if printable:
        import trimesh
        raw=WORK/(n+'_raw.stl');back.exportStl(str(raw),tolerance=.025,angularTolerance=.12,relative=False,parallel=False)
        m=trimesh.load_mesh(raw);m.merge_vertices(digits_vertex=6)
        m.update_faces(m.nondegenerate_faces(height=1e-7));m.update_faces(m.unique_faces());m.remove_unreferenced_vertices()
        m.export(folder/(n+'.stl'))
        row['mesh']=dict(watertight=bool(m.is_watertight),winding_consistent=bool(m.is_winding_consistent),components=len(trimesh.graph.connected_components(m.face_adjacency,nodes=np.arange(len(m.faces)),engine='scipy',min_len=1)),triangles=len(m.faces),bounds_mm=m.bounds.tolist(),holes_patched=0)
    print('EXPORTED',n,round(row['volume_mm3'],4),flush=True)
    return row
def pair(a,b,an,bn,minimum=.5,intended=False):
    """Exact BRep distance; AABBs are only a broad-phase aid.

    A cropped BODY is accepted only if its measured nearest distance is less
    than the crop padding: every omitted point is farther by construction.
    Otherwise the original complete BODY is measured. No distance lower
    bound is returned as a minimum distance.
    """
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    original_a,original_b=a,b
    method='BRepExtrema_DistShapeShape_complete'
    pad=3.0
    if an=='BODY' or bn=='BODY':
        actor=b if an=='BODY' else a;bb=actor.BoundingBox()
        # Outward quantization can reuse an identical exact crop through many
        # nearby poses. Every omitted point is still at least pad away. Keep
        # the original shape alive in the cache to prevent Python id reuse.
        limits=tuple(q for c in 'xyz' for q in [math.floor(getattr(bb,c+'min'))-pad,math.ceil(getattr(bb,c+'max'))+pad])
        body=a if an=='BODY' else b;key=(id(body),limits)
        if key in _BODY_CLIP_CACHE:
            _,candidate=_BODY_CLIP_CACHE[key];_BODY_CLIP_CACHE.move_to_end(key)
        else:
            candidate=body.intersect(box(*limits));_BODY_CLIP_CACHE[key]=(body,candidate)
            if len(_BODY_CLIP_CACHE)>128:_BODY_CLIP_CACHE.popitem(last=False)
        if candidate.Solids():
            if an=='BODY':a=candidate
            else:b=candidate
            method='BRepExtrema_crop_certified_by_distance_below_3mm'
    op=BRepExtrema_DistShapeShape(a.wrapped,b.wrapped)
    if not op.IsDone():raise RuntimeError(f'BRep distance failed {an}/{bn}')
    d=op.Value()
    if method.startswith('BRepExtrema_crop') and d>=pad-1e-6:
        a,b=original_a,original_b
        op=BRepExtrema_DistShapeShape(a.wrapped,b.wrapped)
        if not op.IsDone():raise RuntimeError(f'Global BRep distance failed {an}/{bn}')
        d=op.Value();method='BRepExtrema_DistShapeShape_complete'
    overlap=vol(a.intersect(b)) if d<1e-6 else 0.
    near=[]
    if op.NbSolution():
        for p in [op.PointOnShape1(1),op.PointOnShape2(1)]:near.append([p.X(),p.Y(),p.Z()])
    return dict(a=an,b=bn,gap_mm=d,overlap_mm3=overlap,required_mm=minimum,
                intended_contact=intended,pass_check=overlap<=.001 and (intended or d>=minimum-1e-5),
                distance_kind=method,nearest_points_mm=near)

def scene_pairs(actor,obstacles,name,minimum=.3):
    """Exact global nearest distance with certified broad-phase pruning.

    An AABB lower bound is used only to prove that a pair cannot improve the
    already measured exact minimum or fail the requested clearance. No bound
    is emitted as an exact gap, and all potentially colliding pairs are run.
    """
    aa=actor.BoundingBox();queue=[]
    for n,b in obstacles.items():
        bb=b.BoundingBox();delta=[max(0.,getattr(aa,c+'min')-getattr(bb,c+'max'),getattr(bb,c+'min')-getattr(aa,c+'max')) for c in 'xyz']
        queue.append((float(np.linalg.norm(delta)),n,b))
    queue.sort(key=lambda x:x[0]);best=float('inf');measured=[];pruned=[]
    for lower,n,b in queue:
        if lower>max(best,minimum)+1e-6:
            pruned.append(dict(part=n,lower_bound_mm=lower,reason='Cannot improve measured exact nearest distance or violate required clearance'))
            continue
        r=pair(actor,b,name,n,minimum);measured.append(r);best=min(best,r['gap_mm'])
    return dict(exact_global_minimum_mm=best,measured_pairs=measured,pruned_pairs=pruned,
                passed=all(r['pass_check'] for r in measured))
