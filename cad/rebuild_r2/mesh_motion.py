"""Finite assembly motion on actual exported meshes with exact CAD confirmation
of detected overlaps. The 0.025 mm tessellation is explicit, not continuous CAD
sweep proof. All mesh imports and Boolean operations must have NoError status.
"""
from pathlib import Path
import ctypes,itertools,json,math,time,hashlib
import cadquery as cq
import numpy as np
import trimesh
import manifold3d as md
from interface_check import conflict,clip_body
from hardware_check import posed
ROOT=Path(__file__).resolve().parents[2];RP=ROOT/'reports/rebuild_r2';OUT=ROOT/'exports/rebuild_r2'
WORK=ROOT.parent/'_support/work/fenrir_rebuild_r2/motion';WORK.mkdir(parents=True,exist_ok=True)

def from_mesh(mesh):
    m=md.Manifold(md.Mesh64(np.ascontiguousarray(mesh.vertices,dtype=np.float64),np.ascontiguousarray(mesh.faces,dtype=np.uint64)))
    assert str(m.status())=='Error.NoError',str(m.status())
    assert not m.is_empty(),'Empty mesh input'
    return m

def from_shape(s,name):
    path=WORK/(name+'.stl');s.exportStl(str(path),tolerance=.01,angularTolerance=.10,relative=False,parallel=False)
    mesh=trimesh.load_mesh(path);mesh.merge_vertices(digits_vertex=6)
    mesh.update_faces(mesh.nondegenerate_faces(height=1e-7));mesh.update_faces(mesh.unique_faces())
    return from_mesh(mesh)

def intersection(a,b):
    aa=a.bounding_box();bb=b.bounding_box()
    if any(aa[i+3]<=bb[i]+1e-7 or bb[i+3]<=aa[i]+1e-7 for i in range(3)):return 0.
    r=a^b;assert str(r.status())=='Error.NoError',str(r.status())
    return max(0.,r.volume())

def matrix(m,t):
    if m['kind']=='translate':
        q=np.eye(4);q[:3,3]=np.asarray(m['end_vector'])*t;return q
    return trimesh.transformations.rotation_matrix(math.radians(t*m['end_deg']),m['axis'],m['origin'])

def main():
    ctypes.windll.kernel32.SetPriorityClass(ctypes.c_void_p(-1),0x4000)
    start=time.time();met=json.loads((RP/'cad_metrics.json').read_text(encoding='utf8'))
    design=json.loads((RP/'design_metadata.json').read_text(encoding='utf8'))
    models={n:from_mesh(trimesh.load_mesh(OUT/f'assembly/{n}.stl')) for n in met}
    cad={};printed=[n for n,v in met.items() if v['printable']]
    def shape(n):
        if n not in cad:cad[n]=cq.importers.importStep(str(OUT/f'assembly/{n}.step')).val()
        return cad[n]
    selftest=[intersection(md.Manifold.cube([2,2,2]),md.Manifold.cube([2,2,2]).translate([1,0,0])),intersection(md.Manifold.cube([2,2,2]),md.Manifold.cube([2,2,2]).translate([3,0,0]))]
    assert abs(selftest[0]-4)<1e-9 and selftest[1]==0
    static=[];nstatic=0
    for a,b in itertools.combinations(models,2):
        nstatic+=1;v=intersection(models[a],models[b])
        if v>.01:
            exact=conflict(shape(a),shape(b),part_a=a,part_b=b)
            static.append(dict(a=a,b=b,mesh_overlap_mm3=v,exact_conflict=exact))
            print('STATIC CANDIDATE',static[-1],flush=True)
    print('STATIC DONE',nstatic,'confirmed',sum(bool(x['exact_conflict']) for x in static),flush=True)
    motions=[]
    for m in design['mechanisms']['motions']:
        n=m['part'];moving=[n,*m.get('moving_children',[]),*m.get('moving_hardware',[])]
        if n.startswith('SIDE_'):moving.append(n+'_CAPTURE_PIN')
        switch=m['switch'];tip=np.array(m.get('plunger_tip',m['actuation_point']),float)
        if n.startswith('SIDE_'):axis=-np.array(m['end_vector'])/np.linalg.norm(m['end_vector']);height=.6
        else:
            angle=math.radians(m.get('switch_tilt_deg',0));axis=np.array([0.,-math.sin(angle),math.cos(angle)])
            tip-=axis*m['nominal_actuator_gap_mm'];height=1.
        zone=cq.Solid.makeCylinder(1.101,height+.05,cq.Vector(*(tip-axis*height)),cq.Vector(*axis))
        housing=shape(switch).cut(zone);hm=from_shape(housing,switch+'_HOUSING')
        rows=[]
        for t in np.linspace(0.,1.,31):
            mat=matrix(m,float(t));fail=[]
            for k in moving:
                a=models[k].transform(mat[:3,:])
                for other,b in models.items():
                    if other in moving:continue
                    v=intersection(a,hm if other==switch else b)
                    if v>.01:
                        exact=conflict(posed(shape(k),m,float(t)),housing if other==switch else shape(other),moving=k,fixed=other,fraction=float(t))
                        fail.append(dict(moving=k,fixed=other,mesh_overlap_mm3=v,exact_conflict=exact))
            rows.append(dict(fraction=float(t),candidates=fail))
        r=dict(part=n,poses=rows,pass_check=not any(f['exact_conflict'] for row in rows for f in row['candidates']),
               nominal_contact_stroke_mm=m.get('calculated_contact_travel_mm',m.get('hard_stop_travel_mm',0)-m.get('nominal_actuator_gap_mm',0)))
        motions.append(r);print('MOTION DONE',n,r['pass_check'],flush=True)
        (RP/'mesh_motion_partial.json').write_text(json.dumps(motions,indent=2),encoding='utf8')
    spin=[];origin=design['mechanisms']['wheel']['axis_origin']
    for angle in range(0,360,15):
        mat=trimesh.transformations.rotation_matrix(math.radians(angle),[1,0,0],origin)
        failures=[]
        for n in ('WHEEL','ENCODER_EC10E_ROTOR'):
            a=models[n].transform(mat[:3,:])
            for other,b in models.items():
                if other in ('WHEEL','ENCODER_EC10E_ROTOR'):continue
                v=intersection(a,b)
                if v>.01:failures.append(dict(part=n,fixed=other,mesh_overlap_mm3=v))
        spin.append(dict(angle_deg=angle,conflicts=failures))
    # Sensor reservations and the entire USB insertion corridor are measured
    # independently from the exported STEP gauges, against every printed part.
    interfaces=[]
    for name in ('USB_PLUG_GAUGE','SENSOR_RESERVED_VOLUME','SENSOR_DOWNWARD_OPTICAL_PATH'):
        s=cq.importers.importStep(str(OUT/f'gauges/{name}.step')).val();g=from_shape(s,name)
        fractions=np.linspace(0,1,31) if name=='USB_PLUG_GAUGE' else [1.]
        for t in fractions:
            g1=g.translate([0,-30*(1-t),0]) if name=='USB_PLUG_GAUGE' else g
            failures=[]
            for n in printed:
                v=intersection(g1,models[n])
                if v>.01:failures.append(dict(part=n,mesh_overlap_mm3=v))
            interfaces.append(dict(gauge=name,fraction=float(t),conflicts=failures))
    results=dict(self_test=selftest,static_pairs=nstatic,static_candidates=static,
       static_pass=not any(r['exact_conflict'] for r in static),motions=motions,
       wheel_rotation=spin,interfaces=interfaces,pose_count_each=31,wheel_angles=24,
       export_chord_mm=.025,volume_reporting_threshold_mm3=.01,elapsed_seconds=time.time()-start,
       scope='Manifold 3.5.4 exact polyhedral Booleans on the exported STL (0.025 mm CAD chord target). CAD BRep confirms mesh overlap candidates for static/click tests. Clear mesh poses are not advertised as a continuous CAD sweep, arbitrary-tolerance fit, real click-force or physical-print test.',
       inputs={n:hashlib.sha256((OUT/f'assembly/{n}.stl').read_bytes()).hexdigest() for n in met})
    results['pass_check']=results['static_pass'] and all(r['pass_check'] for r in motions) and not any(r['conflicts'] for r in spin+interfaces)
    (RP/'mesh_assembly_checks.json').write_text(json.dumps(results,indent=2),encoding='utf8')
    print('ASSEMBLY MESH PASS',results['pass_check'],'seconds',round(time.time()-start,1),flush=True)
    if not results['pass_check']:raise RuntimeError('Assembly collision gate failed')

if __name__=='__main__':main()
