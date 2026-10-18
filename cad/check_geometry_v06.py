"""Independent symmetry, contour-rib, hole-through and bottom-containment checks."""
from pathlib import Path
import json,math
import numpy as np
import cadquery as cq
import trimesh
from shapely.geometry import Polygon,Point,MultiPoint
from shapely import affinity
from shapely.ops import unary_union
from validate_mouse import ray_distances
ROOT=Path(__file__).resolve().parents[1];rp=ROOT/'reports/v06'
p=json.loads((ROOT/'cad/parameters_v06.json').read_text());layout=json.loads((rp/'vent_layout.json').read_text())
polys=[Polygon(h['rounded_xd_mm']) for h in layout['holes']];holes=unary_union(polys);outline=Polygon(layout['outer_contour_xd_mm'])
mirror_area=holes.symmetric_difference(affinity.scale(holes,-1,1,origin=(0,0))).area
assert mirror_area<1e-7
assert min(a.distance(b) for i,a in enumerate(polys) for b in polys[i+1:])>2.19
perimeter=[]
for f in np.linspace(0,1,1201):
    pt=outline.exterior.interpolate(float(f),normalized=True)
    if 58.5<pt.y<88.5:perimeter.append(dict(xd_mm=[pt.x,pt.y],distance_to_nearest_aperture_mm=pt.distance(holes)))
dist=[a['distance_to_nearest_aperture_mm'] for a in perimeter]
skin=cq.importers.importStep(str(ROOT/'.tools/v06_vented_skin.step')).val()
skin.exportStl(str(ROOT/'.tools/v06_vented_skin.stl'),tolerance=.02,angularTolerance=.15,relative=False)
sm=trimesh.load_mesh(ROOT/'.tools/v06_vented_skin.stl');through=[]
for h,poly in zip(layout['holes'],polys):
    b=poly.bounds;xy=[]
    for x in np.arange(b[0]+.3,b[2],1):
        for d in np.arange(b[1]+.3,b[3],1):
            if poly.buffer(-.25).contains(Point(x,d)):xy.append([x,-d,50])
    _,idx,_=sm.ray.intersects_location(xy,[[0,0,-1]]*len(xy),multiple_hits=True)
    core=[q for q in xy if poly.buffer(-1.2).contains(Point(q[0],-q[1]))]
    _,ci,_=sm.ray.intersects_location(core,[[0,0,-1]]*len(core),multiple_hits=True)
    through.append(dict(id=h['id'],rays=len(xy),blocked_near_edge=int(len(np.unique(idx))),core_rays=len(core),blocked_core=int(len(np.unique(ci))),note='Underside shoulder rails may enter the first 1.2 mm inside the projected edge; central aperture must remain open.'))
assert all(a['blocked_core']==0 and a['core_rays']>10 for a in through),through
sym=cq.importers.importStep(str(ROOT/'.tools/v06_symmetric_body.step')).val()
sym.exportStl(str(ROOT/'.tools/v06_symmetric_body.stl'),tolerance=.02,angularTolerance=.15,relative=False)
ym=trimesh.load_mesh(ROOT/'.tools/v06_symmetric_body.stl');pts,_=trimesh.sample.sample_surface(ym,6000,seed=20261015);pts[:,0]*=-1
_,sd,_=trimesh.proximity.closest_point(ym,pts)
fm=trimesh.load_mesh(ROOT/'exports/v06/quietmirror_fingertip_V0.6_FIT.stl');pts,_=trimesh.sample.sample_surface(fm,9000,seed=26)
# The windows, guides, caps and their 1.2 mm fixed tacks are the sole permitted
# non-mirrored region. Apply the same exclusion to its reflection.
keep=~((abs(pts[:,0])>15)&(pts[:,1]<-23)&(pts[:,1]>-57)&(pts[:,2]>10)&(pts[:,2]<26))
pts=pts[keep];pts[:,0]*=-1;_,fd,_=trimesh.proximity.closest_point(fm,pts)
assert max(sd)<.06 and max(fd)<.06,(max(sd),max(fd))
base=trimesh.load_mesh(ROOT/'.tools/v06_base.stl')
outside=[Point(x,-y).distance(outline) for x,y,z in base.vertices]
assert max(outside)<.08,max(outside)
om=trimesh.load_mesh(ROOT/'.tools/v06_outer.stl');websamples=[]
byid={h['id']:h for h in layout['holes']}
for pair in layout['adjacent_pairs']:
    a,b=[Polygon(byid[k]['cell_xd_mm']) for k in (pair['a'],pair['b'])]
    edge=a.boundary.intersection(b.buffer(1e-7))
    if edge.geom_type=='MultiLineString':edge=max(edge.geoms,key=lambda q:q.length)
    for f in (.25,.5,.75):
        pt=edge.interpolate(f,normalized=True);loc,_,tri=om.ray.intersects_location([[pt.x,-pt.y,50]],[[0,0,-1]],multiple_hits=True)
        if not len(loc):continue
        j=np.argmax(loc[:,2]);surface=loc[j];n=om.face_normals[tri[j]];h=ray_distances(fm,[surface+n*.1],[-n])[0]
        chord=h[1]-h[0] if len(h)>1 and .02<h[0]<.2 else None
        websamples.append(dict(pair=[pair['a'],pair['b']],xyz=surface.tolist(),normal_chord_mm=chord))
valid=[a['normal_chord_mm'] for a in websamples if a['normal_chord_mm'] is not None]
result=dict(version='0.6',mirror_profile_area_mm2=mirror_area,symmetry=dict(common_body_samples=len(sd),common_body_max_mirror_distance_mm=float(max(sd)),final_fit_samples_outside_side_key_region=len(fd),final_fit_max_mirror_distance_mm=float(max(fd)),exception='Two left caps, their windows, guides and FIT tacks; no bottom lip exception.'),base=dict(max_projection_outside_shell_mm=max(outside),method='All saved base STL vertices against the section at Z=1.001; no external lip permitted.'),hole_count=len(polys),through=through,perimeter_rib=dict(method='Projected contour-to-nearest-aperture distances on D58.5..88.5, excluding the front key/side-key load reserve. Junction distances are expected to be larger.',target_mm=2.4,samples=len(dist),min_mm=min(dist),median_mm=float(np.median(dist)),p95_mm=float(np.percentile(dist,95)),max_mm=max(dist),details=perimeter),web_normal_chords=dict(count=len(valid),minimum_mm=min(valid),median_mm=float(np.median(valid)),under_1_6_mm=sum(v<1.6 for v in valid),samples=websamples),limitations='Finite mesh/section samples, not a global minimum-wall or structural test. CAD corners are polygonal approximations of R1 construction, chord tolerance approximately 0.01 mm.')
(rp/'geometry_checks.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k not in ('perimeter_rib','web_normal_chords')},indent=2));print('perimeter',min(dist),np.median(dist),max(dist),'web',len(valid),min(valid),flush=True)
assert min(valid)>1.6 and len(valid)>35
