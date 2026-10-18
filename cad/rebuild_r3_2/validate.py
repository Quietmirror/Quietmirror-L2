"""R3_2 mesh Booleans + CAD confirmation, contacts and explicit estimate limits."""
from pathlib import Path
import sys,ctypes,itertools,json,math,time,hashlib
import numpy as np
import cadquery as cq
import trimesh
import manifold3d as md
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'cad/rebuild_r2'))
from mesh_motion import from_mesh,intersection,matrix
from interface_check import conflict
from hardware_check import posed
OUT=ROOT/'exports/rebuild_r3_2';RP=ROOT/'reports/rebuild_r3_2'
WORK=ROOT.parent/'_support/work/fenrir_rebuild_r3_2/validation';WORK.mkdir(parents=True,exist_ok=True)

def loadmesh(p):
    m=trimesh.load_mesh(p);m.merge_vertices(digits_vertex=6)
    m.update_faces(m.nondegenerate_faces(height=1e-7));m.update_faces(m.unique_faces())
    return from_mesh(m)
def tomesh(s,n):
    p=WORK/(n+'.stl');s.exportStl(str(p),tolerance=.01,angularTolerance=.1,relative=False,parallel=False)
    return loadmesh(p)
def dump(n,d):
    (RP/n).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def sphere(r,p):return md.Manifold.sphere(r,24).translate(p)

def main():
    ctypes.windll.kernel32.SetPriorityClass(ctypes.c_void_p(-1),0x4000)
    start=time.time();met=json.loads((RP/'cad_metrics.json').read_text())
    d=json.loads((RP/'design_metadata.json').read_text());p=json.loads((HERE/'electronics.json').read_text())
    files={n:OUT/f'assembly/{n}.stl' for n in met}
    if '--mechanical-only' not in sys.argv:
        for folder in ('custom','routes'):
            for f in (OUT/f'electronics/{folder}').glob('*.stl'):files[f.stem]=f
    models={n:loadmesh(f) for n,f in files.items()};cad={}
    def shape(n):
        if n not in cad:cad[n]=cq.importers.importStep(str(files[n].with_suffix('.step'))).val()
        return cad[n]
    # Thread major diameter and printed pilot deliberately overlap only here.
    allowed={}
    for row in d['thread_engagements']:
        x,y,z=row['center'];h=row['height_mm']
        zone=cq.Solid.makeCylinder(row['diameter_mm']/2,h,cq.Vector(x,y,z-h/2))
        allowed[frozenset((row['screw'],row['host']))]=tomesh(zone,row['screw']+'_thread_zone')
    # Each wire end may enter its explicitly named connector only inside a
    # local endpoint ball. Do not ignore an entire connector/route pair.
    for row in p['routes']:
        if row['name'] not in models:continue
        for pt,name in zip((row['points'][0],row['points'][-1]),row['end_contacts']):
            allowed[frozenset((row['name'],name))]=sphere(row['radius']+.02,pt)
    def volume(a,b,n1=None,n2=None):
        aa=a^b
        assert str(aa.status())=='Error.NoError'
        zone=allowed.get(frozenset((n1,n2)))
        return max(0.,(aa-zone if zone is not None else aa).volume())
    hits=[];intended=[]
    for a,b in itertools.combinations(models,2):
        v=intersection(models[a],models[b])
        if v<=.01:continue
        remaining=volume(models[a],models[b],a,b)
        if remaining>.01:
            exact=conflict(shape(a),shape(b),part_a=a,part_b=b)
            hits.append(dict(a=a,b=b,mesh_overlap_mm3=v,unallowed_mm3=remaining,exact_conflict=exact))
        else:intended.append(dict(a=a,b=b,overlap_mm3=v,unallowed_mm3=remaining))
    dump('static_checks.json',dict(parts=len(models),pairs=len(models)*(len(models)-1)//2,conflicts=hits,
        allowed_local_contacts=intended,pass_check=not hits,threshold_mm3=.01))
    print('STATIC',len(models),'parts',len(hits),'conflicts',json.dumps(hits)[:8000],flush=True)
    if '--static-only' in sys.argv:return
    if hits and '--continue-on-failure' not in sys.argv:
        print('Stop before motion: resolve static conflicts first.',flush=True)
        return
    motions=[];strokes=[];confirmed={}
    for m in d['mechanisms']['motions']:
        n=m['part'];moving=[n,*m.get('moving_children',[]),*m.get('moving_hardware',[])]
        if n.startswith('SIDE_'):moving.append(n+'_CAPTURE_PIN')
        switch=m['switch'];q=np.array(m['actuation_point']);gap=m['nominal_actuator_gap_mm']
        if m['kind']=='translate':normal=-np.array(m['end_vector'])/np.linalg.norm(m['end_vector']);height=.6
        else:
            a=math.radians(m.get('switch_tilt_deg',0));normal=np.array([0,-math.sin(a),math.cos(a)]);height=1.
        tip=q-gap*normal
        zone=cq.Solid.makeCylinder(1.101,height+.05,cq.Vector(*(tip-normal*height)),cq.Vector(*normal))
        housing=shape(switch).cut(zone);hm=tomesh(housing,switch+'_housing')
        bad=[]
        for t in np.linspace(0,1,41):
            mat=matrix(m,float(t))
            for k in moving:
                a=models[k].transform(mat[:3,:])
                for other,b in models.items():
                    if other in moving:continue
                    target=hm if other==switch else b
                    v=intersection(a,target)
                    if v>.01:
                        ident=(n,k,other)
                        if ident not in confirmed:
                            confirmed[ident]=conflict(posed(shape(k),m,float(t)),housing if other==switch else shape(other),moving=k,fixed=other,fraction=float(t))
                        bad.append(dict(moving=k,fixed=other,fraction=float(t),overlap_mm3=v,representative_exact=confirmed[ident]))
        mat=matrix(m,1.);qp=mat[:3,:3]@q+mat[:3,3];nn=mat[:3,:3]@normal
        stroke=float(np.dot(nn,tip-qp)/np.dot(nn,normal));offset=float(np.linalg.norm(tip-stroke*normal-qp))
        strokes.append(dict(part=n,along_plunger_axis_mm=stroke,PT_max_mm=.5,headroom_over_PT_max_mm=stroke-.5,
            actuator_face_contact_offset_mm=offset,free_height_assumed=True,physical_click_and_OT_not_verified=True))
        motions.append(dict(part=n,poses=41,conflicts=bad,pass_check=not bad));print('MOTION',n,len(bad),'conflicts',json.dumps(bad)[:1200],flush=True)
        dump('motion_partial.json',motions)
    spin=[]
    cm=next(m for m in d['mechanisms']['motions'] if m['part']=='WHEEL_CARRIER')
    origin=d['mechanisms']['wheel']['axis_origin']
    for press in (0.,.5,1.):
        pressmat=matrix(cm,press);members=set([cm['part'],*cm['moving_children'],*cm['moving_hardware']])
        for angle in range(0,360,15):
            mat=pressmat@trimesh.transformations.rotation_matrix(math.radians(angle),[1,0,0],origin)
            bad=[]
            for name in ('WHEEL','ENCODER_EC10E_ROTOR'):
                a=models[name].transform(mat[:3,:])
                for other,b in models.items():
                    if other in ('WHEEL','ENCODER_EC10E_ROTOR'):continue
                    target=b.transform(pressmat[:3,:]) if other in members else b
                    v=intersection(a,target)
                    if v>.01:bad.append(dict(moving=name,fixed=other,overlap_mm3=v))
            spin.append(dict(press_fraction=press,spin_deg=angle,conflicts=bad))
    dump('motion_checks.json',dict(motions=motions,wheel_combined_press_and_spin=spin,
        pass_check=all(m['pass_check'] for m in motions) and all(not s['conflicts'] for s in spin),
        scope='41 finite key/click poses and 72 wheel combinations, .025mm exported mesh chord, CAD confirms key collision candidates; not continuous swept or physical-fit proof.'))
    dump('mating_checks.json',dict(strokes=strokes,axis_projection_formula='intersection of moved actuator plane with fixed plunger axis',
        manufacturer_PT_max_mm=.5,manufacturer_OT_min_mm=.25,
        warning='PT maximum plus OT minimum is not a guaranteed safe total travel. Measure actual free/operating/total-travel positions and adjust the stop; no electrical click test.',
        sources=['https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2f.pdf','https://tech.alpsalpine.com/cms.media/product_catalog_ec_03_ec10e_en_a9ede251c7.pdf']))
    if '--mechanical-only' not in sys.argv:
        outer=loadmesh(OUT/'gauges/MOTHER_OUTER_REFERENCE.stl');contained=[]
        for row in p['custom']:
            n=row['name'];outside=max(0.,(models[n]-outer).volume())
            contained.append(dict(part=n,outside_reference_outer_mm3=outside,pass_check=outside<=.02))
        reservechecks=[]
        for row in p['reserves']:
            g=loadmesh(OUT/f"electronics/reserves/{row['name']}.stl");bad=[]
            for n,s in models.items():
                if n in row['allowed']:continue
                v=intersection(g,s)
                if v>.01:bad.append(dict(part=n,overlap_mm3=v))
            reservechecks.append(dict(reserve=row['name'],conflicts=bad,pass_check=not bad))
        dump('electronic_space_checks.json',dict(containment=contained,reserves=reservechecks,
            pass_check=all(c['pass_check'] for c in contained+reservechecks),
            actual_PCB_measured=False,optical_working_distance_verified=False,battery_capacity_verified=False,
            physical_mounting_release=False,scope='Only the declared estimated volumes; no supplier footprint, electrical circuit, antenna tuning, capacity or physical assembly claim.'))
        print('CONTAINMENT',json.dumps([x for x in contained if not x['pass_check']]),'RESERVES',json.dumps(reservechecks),flush=True)
    print('VALIDATION FINISHED seconds',round(time.time()-start,1),flush=True)
    passed=not hits and all(m['pass_check'] for m in motions) and all(not s['conflicts'] for s in spin)
    if '--mechanical-only' not in sys.argv:passed=passed and all(c['pass_check'] for c in contained+reservechecks)
    dump('validation_inputs.json',dict(pass_check=passed,files={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [*files.values(),RP/'design_metadata.json',HERE/'electronics.json']},
        boundary='Nominal finite geometry only. Actual electronic mounting, optics, capacity, electrical function and physical tolerances remain open.'))
    if not passed:raise SystemExit(1)

if __name__=='__main__':main()
