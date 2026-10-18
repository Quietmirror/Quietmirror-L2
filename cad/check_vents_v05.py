"""Measure rounded profiles and saved crown geometry, including web samples."""
from pathlib import Path
import json, math
import numpy as np
import cadquery as cq
import trimesh
from shapely.geometry import Polygon, Point
from shapely import affinity
from shapely.ops import unary_union
from vent_layout_v05 import cells, cutter, manifest
from build_v03 import vent_cutter
from validate_mouse import ray_distances

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/v05'
p=json.loads((ROOT/'cad/parameters_v05.json').read_text())
domain,items=cells(p);layout=manifest(p,domain,items)
assert layout['hole_count']==10 and layout['mirror_symmetric_difference_mm2']<1e-8
assert all(abs(a['minimum_rounded_profile_gap_mm']-p['ventilation']['minimum_planar_web'])<.002 for a in layout['adjacent_pairs'])
oldp=json.loads((ROOT/'cad/parameters_v04.json').read_text())
olds=[vent_cutter(oldp,x,-row['y']) for row in oldp['ventilation']['rows'] for x in row['x']]
old_area=olds[0].Volume()/45
old_gap=min(a.distance(b) for i,a in enumerate(olds) for b in olds[i+1:])
old_bb=olds[0].BoundingBox()

# The crown is saved before the deliberately one-sided thumb-button guides.
crown=cq.importers.importStep(str(ROOT/'.tools/v05_symmetric_crown.step')).val()
crown.exportStl(str(ROOT/'.tools/v05_symmetric_crown.stl'),tolerance=.02,angularTolerance=.15,relative=False)
cm=trimesh.load_mesh(ROOT/'.tools/v05_symmetric_crown.stl')
pts,_=trimesh.sample.sample_surface(cm,5000,seed=20261015);pts[:,0]*=-1
_,distance,_=trimesh.proximity.closest_point(cm,pts)
assert max(distance)<.03,max(distance)

# Vertical rays through a 1 mm grid of interior hole points must miss the crown.
hole_results=[]
for a in items:
    poly=a['rounded'];b=poly.bounds;xy=[]
    for x in np.arange(b[0]+.35,b[2],1):
        for d in np.arange(b[1]+.35,b[3],1):
            if poly.buffer(-.25).contains(Point(x,d)):xy.append([x,-d,50])
    _,ray_ids,_=cm.ray.intersects_location(xy,[[0,0,-1]]*len(xy),multiple_hits=True)
    blocked=len(np.unique(ray_ids))
    hole_results.append(dict(id=a['id'],ray_count=len(xy),blocked_rays=blocked))
assert all(a['blocked_rays']==0 for a in hole_results),hole_results

# Inspect normal chords in the narrow webs, which the broad wall sampler
# intentionally excludes near openings. Record these separately, not as a
# fabricated universal minimum thickness or a mechanical strength test.
om=trimesh.load_mesh(ROOT/'.tools/v05_outer.stl')
fm=trimesh.load_mesh(ROOT/'exports/v05/quietmirror_fingertip_V0.5_FIT.stl')
byid={a['id']:a for a in items};web_samples=[]
for pair in layout['adjacent_pairs']:
    a,b=byid[pair['a']],byid[pair['b']]
    shared=a['cell'].boundary.intersection(b['cell'].buffer(1e-7))
    if shared.geom_type=='MultiLineString':shared=max(shared.geoms,key=lambda q:q.length)
    for f in (.25,.5,.75):
        pos=shared.interpolate(f,normalized=True);orig=[pos.x,-pos.y,50]
        loc,_,tri=om.ray.intersects_location([orig],[[0,0,-1]],multiple_hits=True)
        i=np.argmax(loc[:,2]);surface=loc[i];normal=om.face_normals[tri[i]]
        h=ray_distances(fm,[surface+normal*.1],[-normal])[0]
        thickness=h[1]-h[0] if len(h)>=2 and .02<h[0]<.2 else None
        web_samples.append(dict(a=a['id'],b=b['id'],fraction=f,point_xyz_mm=surface.tolist(),normal=normal.tolist(),normal_chord_mm=thickness))
valid=[a['normal_chord_mm'] for a in web_samples if a['normal_chord_mm'] is not None]
assert len(valid)==len(web_samples), 'Inspect a missed web surface'
assert min(valid)>1.6, 'Inspect narrow-web normal thickness'
changed=[k for k in p if p.get(k)!=oldp.get(k)]
assert set(changed)=={'version','notes','ventilation'},changed
result=dict(version='0.5',changed_parameter_fields=changed,old=dict(version='0.4',count=len(olds),rounded_aperture_width_mm=old_bb.xlen,rounded_aperture_length_mm=old_bb.ylen,single_hole_area_mm2=old_area,total_hole_area_mm2=old_area*len(olds),sharp_polygon_minimum_gap_mm=oldp['ventilation']['minimum_planar_web'],rounded_cutter_minimum_gap_mm=old_gap),new=dict(count=len(items),width_range_mm=[min(h['width_mm'] for h in layout['holes']),max(h['width_mm'] for h in layout['holes'])],length_range_mm=[min(h['length_mm'] for h in layout['holes']),max(h['length_mm'] for h in layout['holes'])],area_range_mm2=[min(h['area_mm2'] for h in layout['holes']),max(h['area_mm2'] for h in layout['holes'])],mean_area_mm2=np.mean([h['area_mm2'] for h in layout['holes']]),total_hole_area_mm2=sum(h['area_mm2'] for h in layout['holes']),adjacency_count=len(layout['adjacent_pairs']),adjacent_gap_range_mm=layout['adjacent_web_range_mm']),symmetry=dict(planar_symmetric_difference_mm2=layout['mirror_symmetric_difference_mm2'],crown_saved_step_mirrored_mesh_sample_count=len(distance),crown_max_mirrored_surface_distance_mm=float(max(distance)),crown_percentile_99_mm=float(np.percentile(distance,99)),scope='Crown with both main keys and perforations, before right-hand guides. The complete FIT is intentionally asymmetric at two left side buttons and the frozen right lip; no claim of complete-object symmetry.'),hole_through_checks=hole_results,web_normal_chords=dict(method='57 samples at quarter/mid/three-quarter points on 19 Voronoi shared edges. Cast inward along saved outer mesh normals through final FIT. This samples local normal chords, not a continuous global minimum.',count=len(valid),minimum_mm=min(valid),median_mm=float(np.median(valid)),maximum_mm=max(valid),under_1_6_mm=sum(v<1.6 for v in valid),samples=web_samples),limitations='Shared straight runs have nominal 2.2 mm planar spacing. Filleted multiway junctions and perimeter load rails are wider; normal wall thickness is a different measure. No FEA, printed strength or flex test performed.')
(OUT/'vent_verification.json').write_text(json.dumps(result,indent=2),encoding='utf8')
compact={k:v for k,v in result.items() if k!='web_normal_chords'};compact['web_normal_chords']={k:v for k,v in result['web_normal_chords'].items() if k!='samples'}
print(json.dumps(compact,indent=2))
