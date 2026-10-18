"""Recheck r2 section 1.2 using independent r1 solver plumbing.

No author's geometry/FEM function is imported. The previous independent mesh,
assembly, consistent quadratic traction and reaction checks are reused. The
new face predicates below are transcribed independently from the adopted plan.
"""
from pathlib import Path
import argparse, importlib.util, json, shutil
import numpy as np
from scipy.interpolate import PchipInterpolator

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('our_independent_r1',ROOT/'cad/l2_r1/independent_fem.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
core.OUT=ROOT/'reports/l2_r2';core.OUT.mkdir(exist_ok=True)
core.WORK=ROOT/'_support/work/fem_r2';core.WORK.mkdir(exist_ok=True)

def body(size):
    name=f'R32_{size:g}_straight_midside'
    old=ROOT/'_support/work/independent_fem'/name/'mesh.inp'
    new=core.WORK/name/'mesh.inp'
    if old.exists() and not new.exists():
        new.parent.mkdir(exist_ok=True);shutil.copy2(old,new)
    src=ROOT/'exports/rebuild_r3_2/assembly/BODY.step'
    work,nodes,elems,faces=core.mesh('R32',size,src)
    p=json.loads((ROOT/'cad/rebuild_r2/parameters.json').read_text(encoding='utf-8-sig'))
    meta=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text(encoding='utf-8-sig'))
    feet=[(-23.22,12),(23.22,12),(-24.84,62.64),(24.84,62.64),(0,83.484)]
    fn=[i for i,a in nodes.items() if abs(a[2]-5.2)<1e-5 and any(np.linalg.norm(a[:2]-xy)<4.001 for xy in feet)]
    pin=min(fn,key=lambda i:np.linalg.norm(nodes[i][:2]-feet[0]))
    roller=min(fn,key=lambda i:np.linalg.norm(nodes[i][:2]-feet[1]))
    bc={(i,3) for i in fn}|{(pin,1),(pin,2),(roller,2)}
    wy=np.array([0,.5,1.5,3,6,10,18,30,42,53,58,63,70,74,77,79,80.5,81.7])*1.08
    ww=np.array([.9,10,17,21,24.4,26.1,27.6,28.3,29.2,30.45,30.6,29.8,28.3,26,22,18.2,12,.9])*1.08
    hy=np.array([0,6,10,15,20,25,30,35,40,45,50,55,60,65,68,70,72,74,75,76,78,80,81.7])*1.08
    hz=np.array([9.8,12.7,14.4,16.3,18.2,20.23,22.81,24.39,25.8,26.88,27.8,28.3,27.55,25.47,23.31,21.31,18.31,13.32,9,7.4,6.8,6.8,6.8])*1.08
    width=PchipInterpolator(wy,ww);height=PchipInterpolator(hy,hz)
    def roof(a):
        x,y,z=a;w=float(width(y));h=float(height(y))
        return 5+(h-5)*max(0,1-(abs(x)/w)**3.4)**(1/3.4)
    def outside(a):
        x,y,z=a;w=float(width(y));h=float(height(y))
        surface_x=w*max(0,1-((z-5)/(h-5))**3.4)**(1/3.4)
        return abs(abs(x)-surface_x)<.35
    refs={2.4:[105.64,24.95,24.28,34.47,29.37,496.43,62.21,56.21],
          1.6:[105.04,24.47,23.93,32.81,27.38,497.99,61.77,55.31]}.get(size,[None]*8)
    def mk(name,pred,vec,ref):
        w,m=core.patch(faces,pred);return core.case(name,[(w,m,vec)],ref)
    cases=[mk('palm_down_20N',lambda a,n:44<=a[1]<=71 and abs(a[0])<=24 and a[2]>=23 and n[2]>.3 and abs(a[2]-roof(a))<.35,(0,0,-20),refs[0])]
    root_y=p['main']['root_y']
    for sign,label,ref in ((1,'left',refs[1]),(-1,'right',refs[2])):
        cases.append(mk(label+'_main_root_down_5N',lambda a,n,s=sign:root_y-3<=a[1]<=root_y+4 and 6<=s*a[0]<=24 and a[2]>=11 and n[2]>.2,(0,0,-5),ref))
    for i,m in enumerate(meta['mechanisms']['side_motions']):
        tx,ty,tz=m['plunger_tip']
        cases.append(mk(f'side_{i+1}_switch_fence_inward_5N',lambda a,n,tx=tx,ty=ty,tz=tz:abs(a[0]-(tx-7.5))<.04 and abs(a[1]-ty)<=7.25 and tz-2.9<=a[2]<=tz+2.9 and n[0]>.95,(-5,0,0),refs[3+i]))
    grip=[]
    for s in (-1,1):
        w,m=core.patch(faces,lambda a,n,s=s:s*a[0]>20 and 45<=a[1]<=70 and 8<=a[2]<=14 and s*n[0]>.5 and outside(a))
        grip.append((w,m,(-2*s,0,0)))
    cases.append(core.case('LC3_squeeze_2x2N',grip,refs[5]))
    for x,y,label,ref in ((14,60,'A',refs[6]),(-14,72,'B',refs[7])):
        cases.append(mk(f'press_{label}_d16',lambda a,n,x=x,y=y:(a[0]-x)**2+(a[1]-y)**2<=64 and a[2]>=18 and n[2]>.3 and abs(a[2]-roof(a))<.35,(0,0,-5),ref))
    inputs=dict(plan='r2 section 1.2',mesh_mm=size,root_y=root_y,foot_nodes=len(fn),
                anchors=[dict(node=pin,xyz=nodes[pin].tolist(),dofs=[1,2]),dict(node=roller,xyz=nodes[roller].tolist(),dofs=[2])],
                load_patches=[{k:v for k,v in c.items() if k!='forces'} for c in cases],
                geometry='Unchanged R3.2 BODY',traction='Consistent quadratic triangular load; affine C3D10 faces: corner 0, midside A/3',
                outer_mask='Roof vertical residual <0.35 mm; grip horizontal residual from superellipse <0.35 mm',
                limitations=['Author fem_variants.py and mesh/solver decks not supplied; compare independently generated mesh.',
                             'Affine midside nodes are retained to avoid the invalid curved mesh found in r1; convergence reported explicitly.',
                             'Nearest foot nodes realize the stated in-plane constraints; their exact coordinates may differ from author mesh.'])
    (core.OUT/f'K3_inputs_{size:g}.json').write_text(json.dumps(inputs,indent=2))
    rows=core.solve(work,nodes,elems,bc,cases)
    for r in rows:r['within_document_3_percent']=None if r['deviation_percent'] is None else bool(abs(r['deviation_percent'])<=3)
    compared=all(r['within_document_3_percent'] is not None for r in rows)
    output=dict(inputs=inputs,results=rows,all_eight_within_3_percent=all(r['within_document_3_percent'] is True for r in rows) if compared else None,
                balance_passed=all(r['force_balance_passed'] and r['moment_balance_passed'] for r in rows),
                final_L2_stiffness_certified=False)
    (core.OUT/f'K3_r2_baseline_{size:g}.json').write_text(json.dumps(output,indent=2))
    print('ALL_EIGHT_WITHIN_3_PERCENT',output['all_eight_within_3_percent'],flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--size',type=float,default=2.4);a=ap.parse_args();body(a.size)
