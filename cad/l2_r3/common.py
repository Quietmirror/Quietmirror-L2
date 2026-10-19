from pathlib import Path
import json
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OUT=ROOT/'models/L2_r3';RP=ROOT/'reports/l2_r3';WORK=ROOT/'_support/work/l2_r3'
V=cq.Vector
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
        row['mesh']=dict(watertight=bool(m.is_watertight),winding_consistent=bool(m.is_winding_consistent),components=len(m.split(only_watertight=False)),triangles=len(m.faces),bounds_mm=m.bounds.tolist(),holes_patched=0)
    print('EXPORTED',n,round(row['volume_mm3'],4),flush=True)
    return row
def pair(a,b,an,bn,minimum=.5,intended=False):
    distance_kind='exact'
    ba=a.BoundingBox();bb=b.BoundingBox()
    lower=sum(max(0.,getattr(ba,c+'min')-getattr(bb,c+'max'),getattr(bb,c+'min')-getattr(ba,c+'max'))**2 for c in 'xyz')**.5
    if lower>=max(minimum,.3)+.05:
        return dict(a=an,b=bn,gap_mm=lower,overlap_mm3=0.,required_mm=minimum,intended_contact=intended,pass_check=True,distance_kind='AABB_distance_lower_bound')
    # Exact overlap and threshold clearance only need BODY inside a padded
    # actor AABB. Outside this box, the distance is at least the padding.
    # This avoids pathological global BSpline extremum searches.
    pad=max(.65,minimum+.15)
    if an=='BODY' or bn=='BODY':
        other=b if an=='BODY' else a;bb=other.BoundingBox()
        region=box(bb.xmin-pad,bb.xmax+pad,bb.ymin-pad,bb.ymax+pad,bb.zmin-pad,bb.zmax+pad)
        local=(a if an=='BODY' else b).intersect(region)
        if not local.Solids():return dict(a=an,b=bn,gap_mm=pad,overlap_mm3=0.,required_mm=minimum,intended_contact=intended,pass_check=True,distance_kind='lower_bound_by_AABB_exclusion')
        if an=='BODY':a=local
        else:b=local
        distance_kind='exact_if_below_padding_else_lower_bound'
    bb1=a.BoundingBox();bb2=b.BoundingBox()
    possible=all(getattr(bb1,c+'max')>=getattr(bb2,c+'min')-1e-6 and getattr(bb2,c+'max')>=getattr(bb1,c+'min')-1e-6 for c in 'xyz')
    overlap=vol(a.intersect(b)) if possible else 0.
    d=0. if overlap>.001 else a.distance(b)
    if distance_kind!='exact':d=min(d,pad)
    return dict(a=an,b=bn,gap_mm=d,overlap_mm3=overlap,required_mm=minimum,intended_contact=intended,pass_check=overlap<=.001 and (intended or d>=minimum-1e-5),distance_kind=distance_kind)
