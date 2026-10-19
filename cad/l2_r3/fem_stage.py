"""Low-memory staged FEM: prepare -> separate CCX -> stream result parsing.

Loads and traction integration reuse our independently implemented r2 review.
Final side-key loads use a documented rigid-transfer resultant/moment on the
two mounting-ear contact patches, not the deleted original switch fence.
"""
import argparse,inspect,importlib.util,json,math
from pathlib import Path
import numpy as np
from fem_mesh import core,ROOT
spec=importlib.util.spec_from_file_location('review_loads',ROOT/'cad/l2_r2/fem_recheck.py')
loads=importlib.util.module_from_spec(spec);spec.loader.exec_module(loads)
loads.core=core
class Prepared(Exception):pass

def prepare_only(work,nodes,elements,constraints,cases):
    lines=['*HEADING','L2 r3 independent staged FEM','*NODE']
    lines += [f'{i},'+','.join(f'{v:.12g}' for v in xyz) for i,xyz in sorted(nodes.items())]
    lines += ['*ELEMENT,TYPE=C3D10,ELSET=SOLID']+[f'{j},'+','.join(map(str,e)) for j,e in enumerate(elements,1)]
    ids=sorted(nodes);lines += ['*NSET,NSET=ALL']+[','.join(map(str,ids[j:j+16])) for j in range(0,len(ids),16)]
    lines += ['*MATERIAL,NAME=PA12','*ELASTIC','1500.,0.35','*SOLID SECTION,ELSET=SOLID,MATERIAL=PA12','*BOUNDARY']
    lines += [f'{i},{d},{d},0' for i,d in sorted(constraints)]
    for c in cases:
        lines += ['*STEP','*STATIC,SOLVER=ITERATIVE CHOLESKY','*CLOAD,OP=NEW']
        lines += [f'{i},{d+1},{v:.12g}' for i,vec in c['forces'].items() for d,v in enumerate(vec) if abs(v)>1e-14]
        lines += ['*NODE PRINT,NSET=ALL','U,RF','*END STEP']
    (work/'iterative.inp').write_text('\n'.join(lines)+'\n');del lines
    cache=dict(nodes=len(nodes),elements=len(elements),constraints=[list(v) for v in sorted(constraints)],cases=[])
    for c in cases:cache['cases'].append(dict(name=c['name'],F_norm=float(c['F_norm']),reference=c['reference'],patches=c['patches'],forces={str(i):v.tolist() for i,v in c['forces'].items()}))
    (work/'staged_inputs.json').write_text(json.dumps(cache))
    np.savez(work/'node_positions.npz',ids=np.array(ids),xyz=np.array([nodes[i] for i in ids]))
    print('PREPARED',str(work),len(nodes),'nodes; separate solver required',flush=True);raise Prepared()

def side_cases(faces,nodes):
    weights={};patches=[]
    for xa,xb,ya,yb in [(24,28.2,41.8,45.8),(24,29.2,64.9,67.9)]:
        w,m=core.patch(faces,lambda a,n,xa=xa,xb=xb,ya=ya,yb=yb:xa<=a[0]<=xb and ya<=a[1]<=yb and abs(a[2]-10.75)<1e-4 and n[2]>.95)
        for i,v in w.items():weights[i]=weights.get(i,0)+v/2
        patches.append(m)
    ids=list(weights);A=np.zeros((6,3*len(ids)));W=np.repeat([weights[i] for i in ids],3)
    for j,i in enumerate(ids):
        x,y,z=nodes[i];A[:3,3*j:3*j+3]=np.eye(3)
        A[3:,3*j:3*j+3]=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
    result=[]
    for j,target in enumerate([(25.62,50.25,16.6),(26.12,64.45,16.6)],1):
        f=np.array([-5.,0,0]);rhs=np.r_[f,np.cross(target,f)]
        nodal=W*(A.T@np.linalg.solve((A*W)@A.T,rhs));res=A@nodal-rhs
        assert np.linalg.norm(res)<1e-7
        result.append(dict(name=f'side_{j}_equivalent_ear_5N',forces={i:nodal[3*k:3*k+3] for k,i in enumerate(ids)},F_norm=5.,reference=None,patches=[dict(method='Rigid transfer to both ear footprints; exact resultant and global moment',target=list(target),force_N=f.tolist(),residual=res.tolist(),contact_patches=patches)]))
    return result

def prepare(geometry,size):
    core.solve=prepare_only
    if geometry=='beam':
        try:core.beam(size)
        except Prepared:pass
        return
    if geometry=='R32':fn=loads.body
    else:
        text=inspect.getsource(loads.body)
        text=text.replace("ROOT/'exports/rebuild_r3_2/assembly/BODY.step'","ROOT/'models/L2_r3/parts/BODY.step'").replace("core.mesh('R32',size,src)","core.mesh('L2',size,src)")
        a=text.index("    for i,m in enumerate(meta['mechanisms']['side_motions']):")
        b=text.index('    grip=[]',a)
        text=text[:a]+'    cases.extend(side_cases(faces,nodes))\n'+text[b:]
        env=dict(loads.__dict__,core=core,side_cases=side_cases);exec(compile(text,'independent_final_loads','exec'),env);fn=env['body']
    try:fn(size)
    except Prepared:pass

def parse(geometry,size):
    work=core.WORK/f'{geometry}_{size:g}_curvature24'
    log=work/'iterative.log'
    if not log.exists() or 'Job finished' not in log.read_text(errors='replace'):raise RuntimeError('Solver completion not confirmed')
    data=json.loads((work/'staged_inputs.json').read_text());arr=np.load(work/'node_positions.npz');xyz={int(i):p for i,p in zip(arr['ids'],arr['xyz'])}
    bc={}
    for i,d in data['constraints']:bc.setdefault(i,[]).append(d-1)
    cases=data['cases'];index=-1;section=None;rows=[]
    for c in cases:c['forces']={int(i):np.array(v) for i,v in c['forces'].items()}
    with (work/'iterative.dat').open() as stream:
        for line in stream:
            low=line.lower()
            if 'displacements (' in low:
                index+=1;section='u';c=cases[index];rows.append(dict(work=0.,max_displacement_mm=0.,reaction=np.zeros(3),reaction_moment=np.zeros(3)));continue
            if 'forces (' in low:section='rf';continue
            v=line.split()
            if section is None or len(v)!=4 or not v[0].isdigit():continue
            i=int(v[0]);vec=np.array([float(s.replace('D','E')) for s in v[1:]]);r=rows[index]
            if section=='u':
                if i in c['forces']:r['work']+=float(c['forces'][i].dot(vec))
                r['max_displacement_mm']=max(r['max_displacement_mm'],float(np.linalg.norm(vec)))
            elif i in bc:
                force=np.zeros(3);force[bc[i]]=vec[bc[i]];r['reaction']+=force;r['reaction_moment']+=np.cross(xyz[i],force)
    assert len(rows)==len(cases)
    output=[]
    for c,r in zip(cases,rows):
        fn=c['F_norm'];delta=r['work']/fn;k=fn/delta
        fr=r['reaction']+sum(c['forces'].values(),np.zeros(3));mr=r['reaction_moment']+sum((np.cross(xyz[i],f) for i,f in c['forces'].items()),np.zeros(3))
        output.append(dict(name=c['name'],k_N_per_mm=k,weighted_displacement_mm=delta,max_displacement_mm=r['max_displacement_mm'],reference=c['reference'],deviation_percent=None if c['reference'] is None else 100*(k/c['reference']-1),force_residual_N=fr.tolist(),moment_residual_Nmm=mr.tolist(),force_balance_passed=bool(np.linalg.norm(fr)<fn*1e-4),moment_balance_passed=bool(np.linalg.norm(mr)<fn*.01)))
    report=dict(geometry=geometry,size_mm=size,nodes=data['nodes'],elements=data['elements'],solver='CalculiX 2.22 ITERATIVE CHOLESKY',results=output,scope='Linear isotropic solid model; finite mesh; final side loads are rigid resultant/moment transfer, not a full carrier/contact simulation')
    if geometry=='beam':
        exact=10*60**3/(3*1500*(8*3**3/12))+10*60/((5/6)*(1500/(2*1.35))*24)
        report['analytic_error_percent']=100*(output[0]['weighted_displacement_mm']/exact-1)
    (core.OUT/f'FEM_{geometry}_{size:g}.json').write_text(json.dumps(report,indent=2));print(report,flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','parse']);ap.add_argument('--geometry',choices=['R32','L2','beam'],default='R32');ap.add_argument('--size',type=float,default=2.4);a=ap.parse_args()
    {'prepare':prepare,'parse':parse}[a.action](a.geometry,a.size)
