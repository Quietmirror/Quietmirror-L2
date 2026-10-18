"""Original mirrored triangular lattice; Mini SE visual reference, not copied CAD."""
import itertools, math
import numpy as np
import cadquery as cq
from scipy.spatial import Delaunay
from shapely.geometry import Polygon,box
from shapely import affinity
from vent_layout_v06 import wire_polygon

def cells(p,outer):
    q=p['ventilation'];halfweb=q['minimum_planar_web']/2
    sec=cq.Workplane(obj=outer).section(p['shell_floor_z']+.001).val()
    outline=affinity.scale(wire_polygon(max(sec.Wires(),key=lambda w:w.Length())),1,-1,origin=(0,0))
    half=outline.intersection(box(0,-10,100,110))
    outline=half.union(affinity.scale(half,-1,1,origin=(0,0))).buffer(0)
    # Straight triangular sides deliberately approximate the curved boundary.
    # The contact-side strips and carrier aperture are structural keep-outs.
    boundary=[(8.9,29.5),(20,29.5),(20,56),(25.0,59),(23.0,70),(18.0,80),(10.8,82.5),(0,84),(0,44),(8.9,44)]
    pts=np.array(boundary+[(14.4,40),(10,54),(11,67),(8,78)],float)
    domain=Polygon(boundary);items=[]
    for ids in Delaunay(pts).simplices:
        tri=Polygon(pts[ids])
        if tri.difference(domain).area>1e-6:continue
        sharp=tri.buffer(-halfweb,join_style='mitre')
        if sharp.is_empty or sharp.area<5:continue
        # Three straight sides with tangent corner arcs; never clipped into a
        # quadrilateral or Voronoi cell. Small triangles keep a viable radius.
        radius=min(q['corner_radius'],math.sqrt(sharp.area)*.12)
        rounded=sharp.buffer(-radius,quad_segs=8).buffer(radius,quad_segs=8).simplify(.006)
        if rounded.is_empty:continue
        for sign in (1,-1):
            a=lambda g:affinity.scale(g,sign,1,origin=(0,0))
            items.append(dict(triangle=a(tri),sharp=a(sharp),rounded=a(rounded),radius=radius))
    items.sort(key=lambda x:(x['triangle'].centroid.y,x['triangle'].centroid.x))
    for i,h in enumerate(items):h['id']=f'T{i+1:02}'
    return outline,domain,items

def cutter(h):
    # Exact tangent arcs keep six analytic faces per cutter. Polygonizing the
    # arcs into dozens of faces multiplies downstream loft trim complexity.
    poly=h['sharp']
    tool=cq.Workplane('XY').polyline([(x,-d) for x,d in list(poly.exterior.coords)[:-1]]).close().extrude(40)
    return tool.edges('|Z').fillet(h['radius']).val().translate((0,0,4.8))

def manifest(p,outline,domain,items):
    pairs=[]
    for a,b in itertools.combinations(items,2):
        if a['triangle'].distance(b['triangle'])<1e-5:
            pairs.append(dict(a=a['id'],b=b['id'],gap_mm=a['rounded'].distance(b['rounded'])))
    return dict(version='0.9',style='rounded triangle',total_holes=len(items),front_holes=[],
        holes=[dict(id=h['id'],triangle_vertices_xd_mm=list(h['triangle'].exterior.coords)[:-1],sharp_xd_mm=list(h['sharp'].exterior.coords),rounded_xd_mm=list(h['rounded'].exterior.coords),area_mm2=h['rounded'].area,corner_radius_mm=h['radius'],minimum_outer_edge_gap_mm=h['rounded'].distance(outline.boundary)) for h in items],
        adjacent_pairs=pairs,minimum_planar_web_mm=min(x['gap_mm'] for x in pairs),
        target_planar_web_mm=p['ventilation']['minimum_planar_web'],outer_contour_xd_mm=list(outline.exterior.coords),
        scope='All upper-shell weight-reduction profiles are triangles. The frozen lower structural openings and functional apertures are retained.',
        local_exception='Grip/contact strips, button-guide roots, carrier slot and load-bearing junctions remain wider. Edge triangles approximate the shell contour; the boundary rail is not mathematically constant width.')
