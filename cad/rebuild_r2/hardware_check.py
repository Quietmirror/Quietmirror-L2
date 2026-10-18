"""Hardware, full printed assembly and finite motion checks on exported STEP.

Only the actual switch plunger travel zone is removed in motion housing checks.
No entire switch/hardware component is excluded from a collision test.
"""
from pathlib import Path
import json,itertools,math,ctypes,time
import cadquery as cq
import numpy as np
from interface_check import conflict,clip_body
ROOT=Path(__file__).resolve().parents[2];RP=ROOT/'reports/rebuild_r2';OUT=ROOT/'exports/rebuild_r2/assembly'

def posed(shape,m,t):
    if m['kind']=='translate':return shape.translate([t*x for x in m['end_vector']])
    a=m['origin'];b=[x+y for x,y in zip(a,m['axis'])]
    return shape.rotate(a,b,t*m['end_deg'])

def main():
    ctypes.windll.kernel32.SetPriorityClass(ctypes.c_void_p(-1),0x4000)
    start=time.time();met=json.loads((RP/'cad_metrics.json').read_text(encoding='utf8'))
    design=json.loads((RP/'design_metadata.json').read_text(encoding='utf8'))
    s={n:cq.importers.importStep(str(OUT/f'{n}.step')).val() for n in met}
    printed=[n for n,v in met.items() if v['printable']];hw=[n for n in s if n not in printed]
    rows=[]
    for a,b in itertools.combinations(s,2):
        if a in printed and b in printed:continue
        aa=clip_body(s[a],s[b]) if a=='BODY' else s[a]
        f=conflict(aa,s[b],part_a=a,part_b=b)
        if f:rows.append(f);print('STATIC',f,flush=True)
    (RP/'hardware_static.json').write_text(json.dumps(dict(conflicts=rows,pass_check=not rows,pairs=len(s)*(len(s)-1)//2-len(printed)*(len(printed)-1)//2),indent=2),encoding='utf8')
    motions=[]
    for m in design['mechanisms']['motions']:
        n=m['part'];moving=[n,*m.get('moving_children',[]),*m.get('moving_hardware',[])]
        if n.startswith('SIDE_'):moving.append(n+'_CAPTURE_PIN')
        switch=m['switch'];tip=np.array(m.get('plunger_tip',m['actuation_point']),float)
        if n.startswith('SIDE_'):axis=-np.array(m['end_vector'])/np.linalg.norm(m['end_vector']);height=.6
        else:
            a=math.radians(m.get('switch_tilt_deg',0));axis=np.array([0,-math.sin(a),math.cos(a)])
            tip-=axis*m['nominal_actuator_gap_mm'];height=1.
        zone=cq.Solid.makeCylinder(1.101,height+.05,cq.Vector(*(tip-axis*height)),cq.Vector(*axis))
        housing=s[switch].cut(zone)
        local_body=clip_body(s['BODY'],*[s[k] for k in moving],*[posed(s[k],m,1.) for k in moving])
        fails=[];maxv=0.
        for t in np.linspace(0,1,31):
            pp={k:posed(s[k],m,float(t)) for k in moving}
            for k,a in pp.items():
                for other,b in s.items():
                    if other in moving:continue
                    target=housing if other==switch else local_body if other=='BODY' else b
                    f=conflict(a,target,moving=k,fixed=other,fraction=float(t))
                    if f:fails.append(f);maxv=max(maxv,f['overlap_mm3'])
        row=dict(part=n,poses=31,conflicts=fails,pass_check=not fails,max_overlap_mm3=maxv,
                 nominal_contact_stroke_mm=m.get('calculated_contact_travel_mm',m.get('hard_stop_travel_mm',0)-m.get('nominal_actuator_gap_mm',0)),
                 contact_model='Only housing checked in active plunger zone; spring return, actual PT/OP/OT, friction and force need measured hardware.')
        motions.append(row);print('MOTION',n,'conflicts',len(fails),'max',maxv,flush=True)
        (RP/'hardware_motion_partial.json').write_text(json.dumps(motions,indent=2),encoding='utf8')
    rotations=[];axis=design['mechanisms']['wheel']['axis_origin'];target=[axis[0]+1,axis[1],axis[2]]
    wheel_body=clip_body(s['BODY'],s['WHEEL'],s['ENCODER_EC10E_ROTOR'])
    for angle in np.linspace(0,360,25)[:-1]:
        moving=['WHEEL','ENCODER_EC10E_ROTOR'];fails=[]
        for n in moving:
            q=s[n].rotate(axis,target,float(angle))
            for name,v in s.items():
                if name in moving:continue
                f=conflict(q,wheel_body if name=='BODY' else v,moving=n,fixed=name,angle_deg=float(angle))
                if f:fails.append(f)
        rotations.append(dict(angle_deg=float(angle),conflicts=fails))
    result=dict(static_pass=not rows,motions=motions,wheel_rotation=rotations,
       pass_check=not rows and all(r['pass_check'] for r in motions) and all(not r['conflicts'] for r in rotations),
       tolerance_mm3=.01,elapsed_seconds=time.time()-start,
       scope='Exact exported BRep intersections at finite samples, not continuous motion proof, tolerance-stack proof or physical click validation.')
    (RP/'hardware_motion_checks.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print('HARDWARE PASS',result['pass_check'],flush=True)

if __name__=='__main__':main()
