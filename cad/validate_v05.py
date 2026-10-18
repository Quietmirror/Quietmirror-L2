"""Check saved V0.5 CAD and mesh, sample wall normals and skate planes."""
from pathlib import Path
import json,math
import cadquery as cq
import numpy as np
import trimesh,pymeshlab
from shapely.geometry import MultiPoint,Point,box,Polygon
from validate_mouse import ray_distances
from build_v05 import bounds
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'exports/v05';report=ROOT/'reports/v05'
p=json.loads((ROOT/'cad/parameters_v05.json').read_text())
m=trimesh.load_mesh(out/'quietmirror_fingertip_V0.5_FIT.stl')
s=cq.importers.importStep(str(out/'quietmirror_fingertip_V0.5_FIT.step')).val()
ms=pymeshlab.MeshSet();ms.load_new_mesh(str(out/'quietmirror_fingertip_V0.5_FIT.stl'))
ms.compute_selection_by_self_intersections_per_face();nself=ms.current_mesh().selected_face_number();topo=ms.get_topological_measures()
outer=cq.importers.importStep(str(ROOT/'.tools/v05_outer.step')).val()
outer.exportStl(str(ROOT/'.tools/v05_outer.stl'),tolerance=.025,angularTolerance=.12,relative=False)
om=trimesh.load_mesh(ROOT/'.tools/v05_outer.stl')
points,indices=trimesh.sample.sample_surface(om,5000,seed=20261014)
normals=om.face_normals[indices]
# Sample crown and both grip sides; exclude the foot plane and end rims.
keep=(points[:,2]>8)&(points[:,1]<-4)&(points[:,1]>-80)
# Do not mistake a normal ray exiting a nearby slot edge for wall thickness.
# Keep 2.4 mm in XY away from each key perimeter and wheel opening; remove
# rounded side-button transition samples as their grazing chords are not walls.
exclusions=[]
for name in ('left_key','right_key'):
    k=p[name];r=4.5
    q=box(k['x']-k['width']/2+r,-k['y']-k['length']/2+r,k['x']+k['width']/2-r,-k['y']+k['length']/2-r).buffer(r)
    exclusions.append(q.boundary.buffer(2.4))
w=p['wheel'];exclusions.append(box(w['x']-w['opening_width']/2,-w['y']-w['opening_length']/2,w['x']+w['opening_width']/2,-w['y']+w['opening_length']/2).buffer(2.4))
for i,pt in enumerate(points):
    if pt[2]>6 and any(q.contains(Point(pt[0],pt[1])) for q in exclusions):keep[i]=False
    for b in p['side_buttons']:
        if pt[0]<-22 and abs(pt[1]+b['y'])<b['length']/2+2.4 and abs(pt[2]-b['z'])<4.8:keep[i]=False
layout=json.loads((report/'vent_layout.json').read_text())
vent_shapes=[Polygon([(x,-d) for x,d in h['rounded_xd_mm']]) for h in layout['holes']]
for i,pt in enumerate(points):
    if any(q.buffer(2.4).contains(Point(pt[0],pt[1])) for q in vent_shapes):keep[i]=False
points=points[keep];normals=normals[keep]
orig=points+normals*.10;directions=-normals
hits=ray_distances(m,orig,directions);samples=[];skipped=0
for pt,n,h in zip(points,normals,hits):
    # A near surface miss is a slot/opening, not a thickness measurement.
    if len(h)<2 or not 0.02<h[0]<.20:skipped+=1;continue
    samples.append(dict(point_mm=pt.tolist(),normal=n.tolist(),thickness_mm=round(h[1]-h[0],5)))
vals=[a['thickness_mm'] for a in samples]
feet=[]
for f in json.loads((report/'cad_metrics.json').read_text())['feet']:
    pts=[(f['x'],f['y'])]+[(f['x']+3.7*math.cos(t),f['y']+3.7*math.sin(t)) for t in np.linspace(0,2*math.pi,8,endpoint=False)]
    h=ray_distances(m,[[x,y,-1] for x,y in pts],[[0,0,1]]*9)
    z=[r[0]-1 for r in h if r];feet.append(dict(id=f['id'],center_xy_mm=[f['x'],f['y']],sample_count=len(z),bottom_z_range_mm=[min(z),max(z)]))
# A section at z=1.2 includes the low shell rim as well as the internal ribs.
sec=m.section(plane_origin=[0,0,1.2],plane_normal=[0,0,1]);planar,_=sec.to_2D()
area=sum(q.area for q in planar.polygons_full);hull=MultiPoint(m.vertices[:,:2]).convex_hull.area
grip=[]
for d,z in [(40,13),(46,13),(52,13)]:
    hx=ray_distances(m,[[-40,-d,z]],[[1,0,0]])[0]
    grip.append(dict(distance_from_front_mm=d,z_mm=z,outer_span_mm=round(hx[-1]-hx[0],4)))
bb=bounds(s)
er=json.loads((report/'envelope_interferences.json').read_text());pairs=[]
for i,a in enumerate(er['envelopes']):
    ac=np.array(a['center']);ad=np.array(a['size'])/2
    for b in er['envelopes'][i+1:]:
        bc=np.array(b['center']);bd=np.array(b['size'])/2
        ov=np.minimum(ac+ad,bc+bd)-np.maximum(ac-ad,bc-bd)
        if np.all(ov>1e-6):pairs.append(dict(a=a['name'],b=b['name'],overlap_mm3=round(float(np.prod(ov)),3)))
result=dict(version='0.5',units='mm',step=dict(valid=s.isValid(),solids=len(s.Solids()),dimensions_xyz_mm=[bb[i+3]-bb[i] for i in range(3)],volume_mm3=s.Volume(tol=1e-9),volume_integration_tolerance=1e-9),mesh=dict(dimensions_xyz_mm=m.extents.tolist(),faces=len(m.faces),vertices=len(m.vertices),watertight=m.is_watertight,winding_consistent=m.is_winding_consistent,connected_components=len(m.split(only_watertight=False)),self_intersecting_faces=nself,volume_mm3=m.volume,topology=topo),wall_check=dict(method='Seeded area sampling of original outer surface; local facet normals; exclude end rims, z<8, 2.4 mm around slot boundaries, vent boundaries and side-button transitions. These edge chords are not normal wall measurements. Not a continuous global minimum-wall proof.',nominal_offset_mm=p['wall'],samples_taken=len(vals),skipped_openings=skipped,min_mm=min(vals),percentiles_mm=np.percentile(vals,[1,5,50,95,99]).tolist(),max_mm=max(vals),under_1_6_mm=sum(v<1.6 for v in vals),samples=samples),feet=feet,grip_width_samples=grip,base_section=dict(z_mm=1.2,solid_section_area_mm2=area,xy_convex_hull_area_mm2=hull,open_area_fraction=1-area/hull),envelope_pairs=pairs)
extra=[]
for name in ['quietmirror_fingertip_V0.5_SHELL','side_button_1_V0.5_PRINT','side_button_2_V0.5_PRINT']:
    mesh=trimesh.load_mesh(out/(name+'.stl'));step=cq.importers.importStep(str(out/(name+'.step'))).val()
    qms=pymeshlab.MeshSet();qms.load_new_mesh(str(out/(name+'.stl')));qms.compute_selection_by_self_intersections_per_face()
    item=dict(name=name,cad_valid=step.isValid(),cad_solids=len(step.Solids()),watertight=mesh.is_watertight,winding_consistent=mesh.is_winding_consistent,components=len(mesh.split(only_watertight=False)),self_intersecting_faces=qms.current_mesh().selected_face_number(),dimensions_xyz_mm=mesh.extents.tolist(),volume_mm3=step.Volume(tol=1e-9))
    extra.append(item)
    assert item['cad_valid'] and item['cad_solids']==1 and item['watertight'] and item['winding_consistent'] and item['components']==1 and item['self_intersecting_faces']==0,item
result['additional_models']=extra
result['vent_planar_web_mm']=min(a.distance(b) for i,a in enumerate(vent_shapes) for b in vent_shapes[i+1:])
assert result['vent_planar_web_mm']>=p['ventilation']['minimum_planar_web']-.01
flat=[]
for version,filename in [('0.4','exports/v04/quietmirror_fingertip_V0.4_FIT.stl'),('0.5','exports/v05/quietmirror_fingertip_V0.5_FIT.stl')]:
    mesh=trimesh.load_mesh(ROOT/filename);widths=[]
    for d in range(32,61,2):
        h=ray_distances(mesh,[[-40,-d,13]],[[1,0,0]])[0];widths.append([d,round(h[-1]-h[0],4)])
    flat.append(dict(version=version,z_mm=13,from_front_mm=[32,60],width_samples=widths,width_range_mm=max(a[1] for a in widths)-min(a[1] for a in widths)))
result['side_flatness_comparison']=flat
result['volume_mesh_step_relative_error']=abs(m.volume-result['step']['volume_mm3'])/result['step']['volume_mm3']
assert result['volume_mesh_step_relative_error']<.005
result['side_cap_clearance']=json.loads((report/'cad_metrics.json').read_text())['side_cap_clearance']
assert all(c['shell_intersection_mm3']<1e-5 and c['minimum_shell_distance_mm']>.05 for c in result['side_cap_clearance'])
result['local_feature_dimensions']=dict(normal_wall_sample_min_mm=min(vals),nominal_cap_flange_thickness_mm=p['side_interface']['flange_thickness'],fit_only_attachment_min_nominal_dimension_mm=1.2,vent_corner_radius_mm=p['ventilation']['corner_radius'],vent_min_planar_ligament_mm=result['vent_planar_web_mm'],contact_face_edge_radius_mm=1.1,note='Curve rims and hole mouths require deburring. Sampling does not certify a continuous global minimum.')
(report/'validation.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf8')
compact={k:v for k,v in result.items() if k not in ('wall_check','envelope_pairs')};compact['wall_check']={k:v for k,v in result['wall_check'].items() if k!='samples'}
print(json.dumps(compact,indent=2),flush=True)
assert s.isValid() and len(s.Solids())==1
assert m.is_watertight and m.is_winding_consistent and nself==0 and topo['connected_components_number']==1
assert len(vals)>500 and min(vals)>1.58
assert all(f['sample_count']==9 and max(abs(z) for z in f['bottom_z_range_mm'])<.01 for f in feet)
