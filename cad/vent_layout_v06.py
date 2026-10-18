"""Contour-offset, mirrored perforations. Original geometry, units mm."""
import math
import numpy as np
import cadquery as cq
from shapely.geometry import Polygon, box
from shapely import affinity
from vent_layout_v05 import halfplane_clip, manifest as old_manifest

def wire_polygon(wire):
    points=[wire.positionAt(float(t)).toTuple()[:2] for t in np.linspace(0,1,max(30,math.ceil(wire.Length()/.08)+1))]
    return Polygon(points)

def cells(p,outer):
    q=p['ventilation'];web=q['minimum_planar_web']
    section=cq.Workplane(obj=outer).section(p['shell_floor_z']+.001).val()
    outline=wire_polygon(max(section.Wires(),key=lambda w:w.Length()))
    outline=affinity.scale(outline,1,-1,origin=(0,0))
    # Enforce exact mirrored mathematical layout after numerical CAD sectioning.
    half=outline.intersection(box(0,-10,100,110))
    outline=half.union(affinity.scale(half,-1,1,origin=(0,0))).buffer(0)
    domain=outline.buffer(-(q['perimeter_web']-web/2),join_style='round').intersection(box(-80,q['front_d'],80,100))
    # Explicit local load-path reserve around the rear thumb key, mirrored on
    # the other side. Outside this zone the edge rail follows the outer contour.
    keepout=Polygon([(19.7,40),(40,40),(40,58.0),(25.4,58.0),(19.7,55.8)])
    domain=domain.difference(keepout).difference(affinity.scale(keepout,-1,1,origin=(0,0)))
    seeds=[(x,row['d']) for row in q['seed_rows'] for x in row['x']];items=[]
    for x,d in seeds:
        if x<0:continue
        raw=[[-100,0],[100,0],[100,110],[-100,110]]
        for xx,dd in seeds:
            if (x,d)==(xx,dd):continue
            raw=halfplane_clip(raw,[xx-x,dd-d],(xx*xx+dd*dd-x*x-d*d)/2)
        cell=Polygon(raw).intersection(domain)
        sharp=cell.buffer(-web/2,join_style='mitre').simplify(.025,preserve_topology=True)
        assert sharp.geom_type=='Polygon' and sharp.area>25,(x,d,sharp.area)
        # A 1 mm morphological fillet follows the sampled freeform contour;
        # 48 segments/circle and 0.005 mm simplification keep a polygonal
        # CAD profile within 0.01 mm of its circular corner construction.
        rounded=sharp.buffer(-q['corner_radius'],quad_segs=12).buffer(q['corner_radius'],quad_segs=12).simplify(.005)
        if x==0:
            half=rounded.intersection(box(0,-10,100,110))
            rounded=half.union(affinity.scale(half,-1,1,origin=(0,0))).simplify(1e-6,preserve_topology=True)
        face=cq.Face.makeFromWires(cq.Workplane('XY').polyline(list(rounded.exterior.coords)[:-1]).close().val())
        assert rounded.is_valid
        items.append(dict(seed=(x,d),cell=cell,sharp=sharp,face=face,rounded=rounded))
        if x>0:items.append(dict(seed=(-x,d),cell=affinity.scale(cell,-1,1,origin=(0,0)),sharp=affinity.scale(sharp,-1,1,origin=(0,0)),face=face.mirror('YZ'),rounded=affinity.scale(rounded,-1,1,origin=(0,0))))
    items.sort(key=lambda a:(a['seed'][1],a['seed'][0]))
    for i,a in enumerate(items):a['id']=f'H{i+1:02}'
    return outline,domain,items

def cutter(item):
    f=item['face'].mirror('XZ')
    return cq.Solid.extrudeLinear(f.outerWire(),[],cq.Vector(0,0,45)).translate((0,0,.5))

def manifest(p,outline,domain,items):
    r=old_manifest(p,domain,items);r['version']='0.6'
    r['outer_contour_xd_mm']=list(outline.exterior.coords)
    r['target_perimeter_web_mm']=p['ventilation']['perimeter_web']
    r['local_exception']='Mirrored thumb-key load reserve at D=47..58.0 mm; front key bridge and rounded multiway nodes are wider.'
    for a,h in zip(items,r['holes']):h['minimum_outer_edge_gap_mm']=a['rounded'].distance(outline.boundary)
    return r
