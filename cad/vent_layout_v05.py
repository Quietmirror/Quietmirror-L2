"""Symmetric, contour-fitted perforations with shared constant-width webs.

Cell coordinates use X and D (positive distance back from the nose), in mm.
The right-hand cells are built once; their left partners are exact mirrors.
"""
from pathlib import Path
import json, math
import numpy as np
from shapely.geometry import Polygon, box
from shapely import affinity
from shapely.ops import unary_union
import cadquery as cq

ROOT=Path(__file__).resolve().parents[1]

def halfplane_clip(vertices, normal, limit):
    """Clip a polygon to dot(normal, position) <= limit."""
    result=[]
    for a,b in zip(vertices,vertices[1:]+vertices[:1]):
        va=np.dot(normal,a)-limit;vb=np.dot(normal,b)-limit
        if va<=1e-9:result.append(a)
        if (va<0 and vb>0) or (va>0 and vb<0):
            result.append((np.asarray(a)+(np.asarray(b)-a)*va/(va-vb)).tolist())
    return result

def cells(p):
    q=p['ventilation'];right=q['domain_right_xd_mm']
    domain=Polygon(right+[[-x,d] for x,d in right[::-1]])
    seeds=[(x,row['d']) for row in q['seed_rows'] for x in row['x']]
    results=[]
    for i,(x,d) in enumerate(seeds):
        if x<0:continue
        raw=[[-100,0],[100,0],[100,100],[-100,100]]
        for xx,dd in seeds:
            if (x,d)==(xx,dd):continue
            raw=halfplane_clip(raw,[xx-x,dd-d],(xx*xx+dd*dd-x*x-d*d)/2)
        cell=Polygon(raw).intersection(domain)
        hole=cell.buffer(-q['minimum_planar_web']/2,join_style='mitre').simplify(.015,preserve_topology=True)
        assert hole.geom_type=='Polygon' and hole.area>30,(x,d,hole.area)
        # Round inwards, leaving all shared straight runs exactly web apart.
        face=cq.Face.makeFromWires(cq.Workplane('XY').polyline(list(hole.exterior.coords)[:-1]).close().val())
        face=face.fillet2D(q['corner_radius'],face.Vertices())
        # Trace each actual circular arc/line for independent planar checks.
        edges=face.outerWire().Edges();points=[]
        # A wire's edge list is not guaranteed to follow connection order.
        ordered=list(face.outerWire())
        for edge in ordered:
            n=max(2,math.ceil(edge.Length()/.04)+1)
            pts=[edge.positionAt(t).toTuple()[:2] for t in np.linspace(0,1,n)]
            if points and np.linalg.norm(np.array(points[-1])-pts[-1])<np.linalg.norm(np.array(points[-1])-pts[0]):pts.reverse()
            points.extend(pts if not points else pts[1:])
        rounded=Polygon(points)
        assert rounded.is_valid and abs(rounded.area-face.Area())<.02,(x,d,rounded.is_valid)
        item=dict(seed=(x,d),cell=cell,sharp=hole,face=face,rounded=rounded)
        results.append(item)
        if x>0:
            results.append(dict(seed=(-x,d),cell=affinity.scale(cell,-1,1,origin=(0,0)),sharp=affinity.scale(hole,-1,1,origin=(0,0)),face=face.mirror('YZ'),rounded=affinity.scale(rounded,-1,1,origin=(0,0))))
    results.sort(key=lambda a:(a['seed'][1],a['seed'][0]))
    for i,a in enumerate(results):a['id']=f'H{i+1:02}'
    return domain,results

def cutter(item):
    # D -> -Y while preserving the planar profile and a vertical optical axis.
    face=item['face'].mirror('XZ')
    return cq.Solid.extrudeLinear(face.outerWire(),[],cq.Vector(0,0,45)).translate((0,0,5))

def manifest(p,domain,items):
    pairs=[]
    for i,a in enumerate(items):
        for b in items[i+1:]:
            shared=a['cell'].boundary.intersection(b['cell'].buffer(1e-7)).length
            distance=a['rounded'].distance(b['rounded'])
            if shared>.15:
                pairs.append(dict(a=a['id'],b=b['id'],shared_cell_edge_length_mm=shared,minimum_rounded_profile_gap_mm=distance))
    both=unary_union([a['rounded'] for a in items]);mirror=affinity.scale(both,-1,1,origin=(0,0))
    result=dict(version='0.5',coordinate_system='XY cutter uses Y=-D; layout uses X,D in mm',algorithm='Clipped Voronoi cells, inset by web/2, internal R fillet; positive-X profiles mirrored exactly',domain_xd_mm=list(domain.exterior.coords),hole_count=len(items),target_planar_web_mm=p['ventilation']['minimum_planar_web'],corner_radius_mm=p['ventilation']['corner_radius'],symmetry_axis='X=0',mirror_symmetric_difference_mm2=both.symmetric_difference(mirror).area,total_open_profile_area_mm2=both.area,adjacent_pairs=pairs,holes=[])
    for a in items:
        b=a['rounded'].bounds
        result['holes'].append(dict(id=a['id'],seed_xd_mm=a['seed'],cell_xd_mm=list(a['cell'].exterior.coords),sharp_xd_mm=list(a['sharp'].exterior.coords),rounded_xd_mm=list(a['rounded'].exterior.coords),bounds_xd_mm=b,width_mm=b[2]-b[0],length_mm=b[3]-b[1],area_mm2=a['face'].Area()))
    result['adjacent_web_range_mm']=[min(a['minimum_rounded_profile_gap_mm'] for a in pairs),max(a['minimum_rounded_profile_gap_mm'] for a in pairs)]
    return result

def main():
    p=json.loads((ROOT/'cad/parameters_v05.json').read_text())
    domain,items=cells(p);r=manifest(p,domain,items)
    out=ROOT/'reports/v05';out.mkdir(parents=True,exist_ok=True)
    (out/'vent_layout.json').write_text(json.dumps(r,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in r.items() if k not in ('holes','domain_xd_mm')},indent=2))

if __name__=='__main__':main()
