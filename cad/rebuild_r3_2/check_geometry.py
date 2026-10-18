"""Check the delivered short-foot body, its real datum, mesh and ground clearance."""
from pathlib import Path
import sys,json,math,ctypes,hashlib
import cadquery as cq
import trimesh,numpy as np,pymeshlab
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OUT=ROOT/'exports/rebuild_r3_2';BASE=ROOT/'exports/rebuild_r3_1';RP=ROOT/'reports/rebuild_r3_2'
sys.path.insert(0,str(ROOT/'cad/rebuild_r2'))
from mechanics import box,cylinder,join
from mesh_motion import matrix

def dump(n,d):(RP/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
    ctypes.windll.kernel32.SetPriorityClass(ctypes.c_void_p(-1),0x4000)
    p=json.loads((HERE/'parameters.json').read_text());d=json.loads((RP/'design_metadata.json').read_text())
    met=json.loads((RP/'cad_metrics.json').read_text());z=p['foot_contact_z_mm'];r=p['foot_diameter_mm']/2;h=p['foot_land_thickness_mm']
    body=cq.importers.importStep(str(OUT/'assembly/BODY.step')).val()
    old=cq.importers.importStep(str(BASE/'assembly/BODY.step')).val()
    reserve=cq.importers.importStep(str(OUT/'gauges/SENSOR_RESERVED_VOLUME.step')).val()

    # Boolean subtraction of two nearly coincident full BSpline bodies proved
    # unstable in this OCC version (classifying the entire body as a delta).
    # Do not report that as an exact preservation proof. Independently check
    # the delivered surfaces in both directions at a bounded tessellation error.
    old_mesh=trimesh.load_mesh(BASE/'assembly/BODY.stl')
    new_mesh=trimesh.load_mesh(OUT/'assembly/BODY.stl');surface_checks=[]
    for label,source,target in [('R3.1_to_R3.2',old_mesh,new_mesh),('R3.2_to_R3.1',new_mesh,old_mesh)]:
        points,_=trimesh.sample.sample_surface(source,7000,seed=913)
        local=(points[:,0]>27)&(points[:,1]>42)&(points[:,1]<71.5)&(points[:,2]>11)&(points[:,2]<19)
        sample=points[~local];_,dist,_=trimesh.proximity.closest_point(target,sample)
        surface_checks.append(dict(direction=label,samples=len(sample),maximum_distance_mm=float(dist.max()),
            p99_distance_mm=float(np.percentile(dist,99)),threshold_mm=.055,pass_check=bool(dist.max()<=.055)))
    pads=[]
    for f in d['mechanisms']['feet']:
        x,y=f['center'];land=cylinder(r,h,(x,y,z))
        missing=land.cut(body).Volume()
        under=body.intersect(cylinder(r-.001,z+5,(x,y,-5))).Volume()
        faces=[]
        for face in body.Faces():
            b=face.BoundingBox();c=face.Center()
            if b.zlen<1e-6 and abs(b.zmin-z)<1e-6 and math.hypot(c.x-x,c.y-y)<r:
                faces.append(dict(area_mm2=face.Area(),z=b.zmin,normal=face.normalAt().toTuple()))
        area=sum(q['area_mm2'] for q in faces)
        pads.append(dict(center_xy=[x,y],contact_z=z,diameter_mm=2*r,land_thickness_mm=h,missing_disk_mm3=missing,
            material_under_landing_mm3=under,bottom_faces=faces,bottom_area_mm2=area,
            pass_check=missing<1e-5 and under<1e-5 and math.pi*r*r-1e-4<=area<math.pi*r*r+.5))
    identical={n:all((BASE/f'assembly/{n}.{ext}').read_bytes()==(OUT/f'assembly/{n}.{ext}').read_bytes() for ext in ('step','stl')) for n in met if n not in ('BODY','SIDE_FRONT_KEY','SIDE_REAR_KEY')}
    result=dict(valid=body.isValid(),connected_solids=len(body.Solids()),reference_lower_plane_z_mm=reserve.BoundingBox().zmin,
        foot_plane_z_mm=z,shortened_mm_from_R3=5.2,datum_difference_mm=abs(z-reserve.BoundingBox().zmin),pads=pads,
        five_pad_bottoms_coplanar=all(q['pass_check'] for q in pads),outside_side_apertures_surface_checks=surface_checks,
        preservation_scope='7000 area-weighted surface samples per direction, excluding the declared left-side aperture region X>27, Y42..71.5, Z11..19; 0.055mm threshold covers two 0.025mm chord targets. Not exact equality or exhaustive surface proof.',
        unchanged_parts=identical,body_extents_mm=met['BODY']['bounds_mm'],retained_R3_origin=True)
    result['pass_check']=result['valid'] and result['connected_solids']==1 and result['datum_difference_mm']<1e-6 and result['five_pad_bottoms_coplanar'] and all(q['pass_check'] for q in surface_checks) and all(identical.values())
    dump('foot_datum_checks.json',result);print('BODY PRESERVATION AND FEET',result['pass_check'],'surface checks',surface_checks,flush=True)
    assert result['pass_check'],result
    rows=[]
    for n,v in met.items():
        if not v['printable']:continue
        path=OUT/f'print/{n}.stl';m=trimesh.load_mesh(path)
        ms=pymeshlab.MeshSet();ms.load_new_mesh(str(path));ms.apply_filter('compute_selection_by_self_intersections_per_face')
        q=dict(part=n,watertight=bool(m.is_watertight),consistent_winding=bool(m.is_winding_consistent),
            connected_components=len(m.split(only_watertight=False)),self_intersecting_faces=ms.current_mesh().selected_face_number(),
            positive_volume=bool(m.volume>0),bounds_mm=m.extents.tolist(),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        q['pass_check']=q['watertight'] and q['consistent_winding'] and q['connected_components']==1 and q['self_intersecting_faces']==0 and q['positive_volume']
        rows.append(q);print('MESH',n,q['pass_check'],flush=True)
    dump('mesh_checks.json',dict(parts=rows,pass_check=all(q['pass_check'] for q in rows)))
    assert all(q['pass_check'] for q in rows)
    meshes={n:trimesh.load_mesh(OUT/f'assembly/{n}.stl') for n in met}
    for path in (OUT/'electronics/custom').glob('*.stl'):meshes[path.stem]=trimesh.load_mesh(path)
    ground=z-p['example_skate_thickness_mm'];clearances=[]
    for n,m in meshes.items():clearances.append(dict(part=n,lowest_z=float(m.bounds[0,2]),clearance_mm=float(m.bounds[0,2]-ground)))
    moves=[]
    for motion in d['mechanisms']['motions']:
        names=[motion['part'],*motion.get('moving_children',[]),*motion.get('moving_hardware',[])]
        minz=min(float(trimesh.transform_points(meshes[n].vertices,matrix(motion,float(t)))[:,2].min()) for t in np.linspace(0,1,41) for n in names)
        moves.append(dict(part=motion['part'],poses=41,lowest_z=minz,minimum_clearance_mm=minz-ground))
    low=min(q['lowest_z'] for q in clearances)
    clearance=dict(assumed_skate_thickness_mm=p['example_skate_thickness_mm'],ground_z_mm=ground,
        body_below_bonding_plane_mm=z-met['BODY']['min'][2],static=clearances,motions=moves,
        minimum_static_clearance_mm=min(q['clearance_mm'] for q in clearances),
        minimum_skate_thickness_for_desired_clearance_mm=z-low+p['desired_ground_clearance_mm'],
        desired_clearance_mm=p['desired_ground_clearance_mm'],
        estimated_lens_bottom_to_ground_mm=7.8-ground,actual_optical_working_distance_verified=False,
        scope='Uncompressed 0.5mm skate example only; no bare-body ground-clearance claim. Measure the actual skate, flatness and pad compression.',
        pass_check=min(q['clearance_mm'] for q in clearances)>=p['desired_ground_clearance_mm']-1e-5 and all(q['minimum_clearance_mm']>=p['desired_ground_clearance_mm'] for q in moves))
    dump('ground_clearance_checks.json',clearance);print('GROUND',clearance['pass_check'],'minimum',clearance['minimum_static_clearance_mm'],flush=True)
    assert clearance['pass_check']

if __name__=='__main__':main()
