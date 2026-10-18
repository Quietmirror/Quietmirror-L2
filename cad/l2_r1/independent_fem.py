"""Independent Gmsh -> CalculiX validation; no project FEM helpers imported.

Units mm,N,MPa. k=F_norm**2/(f dot u), with F_norm=sum applied patch
resultant magnitudes (4 N in the opposing 2+2 N grip case).
"""
from pathlib import Path
import argparse,json,math,subprocess,sys
import numpy as np
import cadquery as cq
from scipy.interpolate import PchipInterpolator

ROOT=Path(__file__).resolve().parents[2];SUP=ROOT/'_support'
GMSH=SUP/'tools/Gmsh/gmsh-4.15.2-Windows64/gmsh.exe'
CCX=SUP/'tools/FreeCAD/FreeCAD_1.1.4-Windows-x86_64-py311/bin/ccx.exe'
OUT=ROOT/'reports/l2_r1';WORK=SUP/'work/independent_fem';WORK.mkdir(parents=True,exist_ok=True)
def run(cmd,cwd,log):
    with log.open('w',encoding='utf8') as f:r=subprocess.run([str(x) for x in cmd],cwd=cwd,stdout=f,stderr=subprocess.STDOUT)
    if r.returncode:raise RuntimeError(f'{cmd[0]} exited {r.returncode}: {log}')
def readmesh(p):
    nodes={};elems=[];section=None
    for raw in p.read_text().splitlines():
        line=raw.strip()
        if not line or line.startswith('**'):continue
        if line.startswith('*'):
            section='n' if line.upper().startswith('*NODE') and not line.upper().startswith('*NODE SET') else ('e' if line.upper().startswith('*ELEMENT') and 'C3D10' in line.upper() else None)
            continue
        v=[a.strip() for a in line.split(',') if a.strip()]
        if section=='n':nodes[int(v[0])]=np.array([float(a) for a in v[1:4]])
        elif section=='e':
            if len(v)!=11:raise ValueError(('unexpected element record',line))
            elems.append([int(a) for a in v[1:]])
    assert nodes and elems,(len(nodes),len(elems))
    used=set(i for e in elems for i in e);nodes={i:v for i,v in nodes.items() if i in used}
    return nodes,elems
def boundary(nodes,elems):
    seen={};local=((0,1,2,4,5,6),(0,3,1,7,8,4),(1,3,2,8,9,5),(2,3,0,9,7,6))
    for e in elems:
        ec=np.mean([nodes[i] for i in e[:4]],axis=0)
        for ii in local:
            ids=[e[j] for j in ii];key=tuple(sorted(ids[:3]))
            if key in seen:seen[key]=None
            else:seen[key]=(ids,ec)
    faces=[]
    for value in seen.values():
        if value is None:continue
        ids,ec=value;p=np.array([nodes[i] for i in ids]);cent=p[:3].mean(axis=0);normal=np.cross(p[1]-p[0],p[2]-p[0]);area=np.linalg.norm(normal)/2
        if area<1e-10:continue
        normal/=2*area
        if normal.dot(cent-ec)<0:normal=-normal
        faces.append(dict(ids=ids,center=cent,normal=normal,area=area))
    return faces
def mesh(name,size,source):
    work=WORK/f'{name}_{size:g}_straight_midside';work.mkdir(exist_ok=True)
    geo=work/'mesh.geo';inp=work/'mesh.inp'
    geo.write_text(f'SetFactory("OpenCASCADE");\nMerge "{source.as_posix()}";\nMesh.MeshSizeMin={size};\nMesh.MeshSizeMax={size};\nMesh.MeshSizeFromCurvature=0;\nMesh.MeshSizeExtendFromBoundary=1;\nMesh.Algorithm3D=1;\nMesh.Optimize=1;\nMesh.OptimizeNetgen=1;\nMesh.ElementOrder=2;\nMesh.SecondOrderLinear=1;\nPhysical Volume("SOLID")={{Volume{{:}}}};\nMesh.SaveGroupsOfElements=0;\n',encoding='utf8')
    if not inp.exists():run([GMSH,geo,'-3','-order','2','-format','inp','-o',inp,'-nt','1'],work,work/'gmsh.log')
    nodes,elements=readmesh(inp);faces=boundary(nodes,elements)
    print('Mesh',name,size,len(nodes),len(elements),len(faces),flush=True)
    return work,nodes,elements,faces
def patch(faces,predicate):
    selected=[f for f in faces if predicate(f['center'],f['normal'])]
    if not selected:raise ValueError('Empty load patch')
    weights={};area=sum(f['area'] for f in selected)
    for f in selected:
        # Consistent quadratic face loads on affine triangles: corner weights
        # zero, each midside node A/3. Curvature error checked by refinement.
        for i in f['ids'][3:]:weights[i]=weights.get(i,0)+f['area']/(3*area)
    return weights,dict(triangles=len(selected),area_mm2=area,center=np.average(np.array([f['center'] for f in selected]),axis=0,weights=[f['area'] for f in selected]).tolist())
def case(name,patches,reference=None):
    forces={};description=[];magnitude=0
    for weights,meta,vector in patches:
        magnitude+=np.linalg.norm(vector);description.append(dict(**meta,resultant_N=list(vector)))
        for i,a in weights.items():forces[i]=forces.get(i,np.zeros(3))+a*np.array(vector)
    return dict(name=name,forces=forces,patches=description,F_norm=magnitude,reference=reference)
def solve(work,nodes,elements,constraints,cases):
    deck=work/'independent.inp';lines=['*HEADING','Independent L2 baseline review','*NODE']
    lines += [f'{i},'+','.join(f'{x:.12g}' for x in p) for i,p in sorted(nodes.items())]
    lines+=['*ELEMENT,TYPE=C3D10,ELSET=SOLID']+[f'{j},'+','.join(map(str,e)) for j,e in enumerate(elements,1)]
    lines+=['*NSET,NSET=ALL']+[','.join(map(str,list(sorted(nodes))[j:j+16])) for j in range(0,len(nodes),16)]
    lines+=['*MATERIAL,NAME=PA12','*ELASTIC','1500.,0.35','*SOLID SECTION,ELSET=SOLID,MATERIAL=PA12','*BOUNDARY']
    lines += [f'{i},{d},{d},0' for i,d in sorted(constraints)]
    for c in cases:
        lines += ['*STEP','*STATIC','*CLOAD,OP=NEW']
        lines += [f'{i},{d+1},{v:.12g}' for i,vec in c['forces'].items() for d,v in enumerate(vec) if abs(v)>1e-14]
        lines += ['*NODE PRINT,NSET=ALL','U,RF','*END STEP']
    content='\n'.join(lines)+'\n'
    reuse=deck.exists() and deck.read_text()==content and (work/'ccx.log').exists() and 'Job finished' in (work/'ccx.log').read_text()
    if not reuse:
        deck.write_text(content)
        run([CCX,'-i','independent'],work,work/'ccx.log')
    blocks=[];force_blocks=[];current=None
    for line in (work/'independent.dat').read_text().splitlines():
        lo=line.lower()
        if 'displacements (' in lo:current={};blocks.append(current);continue
        if 'forces (' in lo:current={};force_blocks.append(current);continue
        if current is not None:
            v=line.split()
            if len(v)==4 and v[0].isdigit():current[int(v[0])]=np.array([float(x.replace('D','E')) for x in v[1:]])
    assert len(blocks)==len(cases),(len(blocks),len(cases))
    rows=[]
    assert len(force_blocks)==len(cases),(len(force_blocks),len(cases))
    for c,u,rf in zip(cases,blocks,force_blocks):
        work_Nmm=sum(float(f.dot(u[i])) for i,f in c['forces'].items());delta=work_Nmm/c['F_norm'];k=c['F_norm']/delta
        reactions={}
        for i,d in constraints:
            reactions.setdefault(i,np.zeros(3))[d-1]=rf[i][d-1]
        force_residual=sum(c['forces'].values(),np.zeros(3))+sum(reactions.values(),np.zeros(3))
        moment_residual=sum((np.cross(nodes[i],f) for i,f in c['forces'].items()),np.zeros(3))+sum((np.cross(nodes[i],f) for i,f in reactions.items()),np.zeros(3))
        row=dict(name=c['name'],nodes=len(nodes),elements=len(elements),external_work_Nmm=work_Nmm,weighted_displacement_mm=delta,k_N_per_mm=k,max_displacement_mm=max(np.linalg.norm(p) for p in u.values()),patches=c['patches'],document_k_N_per_mm=c['reference'],deviation_percent=None if c['reference'] is None else 100*(k/c['reference']-1),force_residual_N=force_residual.tolist(),moment_residual_Nmm=moment_residual.tolist(),force_balance_passed=bool(np.linalg.norm(force_residual)<c['F_norm']*1e-4),moment_balance_passed=bool(np.linalg.norm(moment_residual)<c['F_norm']*100*1e-4),solver_reused_identical_input=bool(reuse))
        rows.append(row);print(row['name'],row['k_N_per_mm'],flush=True)
    return rows
def beam(size):
    src=WORK/'beam.step'
    if not src.exists():cq.exporters.export(cq.Solid.makeBox(60,8,3,cq.Vector(0,-4,-1.5)),str(src))
    work,nodes,elems,faces=mesh('beam',size,src);w,m=patch(faces,lambda p,n:abs(p[0]-60)<1e-5)
    bc={(i,d) for i,p in nodes.items() if abs(p[0])<1e-6 for d in (1,2,3)}
    rows=solve(work,nodes,elems,bc,[case('cantilever_10N',[(w,m,(0,0,-10))])]);row=rows[0]
    E=1500;G=E/(2*1.35);I=8*3**3/12
    analytic=10*60**3/(3*E*I)+10*60/((5/6)*G*24)
    row.update(analytic_timoshenko_mm=analytic,relative_error_percent=100*(row['weighted_displacement_mm']/analytic-1),passed=bool(abs(row['weighted_displacement_mm']/analytic-1)<.05))
    (OUT/f'K2_beam_{size:g}.json').write_text(json.dumps(row,indent=2))
def body(size):
    src=ROOT/'exports/rebuild_r3_2/assembly/BODY.step';work,nodes,elems,faces=mesh('R32',size,src)
    feet=[(-23.22,12),(23.22,12),(-24.84,62.64),(24.84,62.64),(0,83.484)]
    footnodes=[i for i,p in nodes.items() if abs(p[2]-5.2)<1e-5 and any(np.linalg.norm(p[:2]-xy)<4.001 for xy in feet)]
    assert len(footnodes)>20
    pin=min(footnodes,key=lambda i:np.linalg.norm(nodes[i][:2]-feet[0]));roller=min(footnodes,key=lambda i:np.linalg.norm(nodes[i][:2]-feet[1]))
    bc={(i,3) for i in footnodes}|{(pin,1),(pin,2),(roller,2)}
    wy=np.array([0,.5,1.5,3,6,10,18,30,42,53,58,63,70,74,77,79,80.5,81.7])*1.08
    ww=np.array([.9,10,17,21,24.4,26.1,27.6,28.3,29.2,30.45,30.6,29.8,28.3,26,22,18.2,12,.9])*1.08
    hy=np.array([0,6,10,15,20,25,30,35,40,45,50,55,60,65,68,70,72,74,75,76,78,80,81.7])*1.08
    hz=np.array([9.8,12.7,14.4,16.3,18.2,20.23,22.81,24.39,25.8,26.88,27.8,28.3,27.55,25.47,23.31,21.31,18.31,13.32,9,7.4,6.8,6.8,6.8])*1.08
    width=PchipInterpolator(wy,ww);height=PchipInterpolator(hy,hz)
    def roof(p,n):
        x,y,z=p;w=float(width(y));h=float(height(y));zz=5+(h-5)*max(0,1-(abs(x)/w)**3.4)**(1/3.4)
        return n[2]>.05 and abs(zz-z)<.25
    def mk(name,pred,vector,ref):
        w,m=patch(faces,pred);return case(name,[(w,m,vector)],ref)
    cases=[mk('palm_down_20N',lambda p,n:44<=p[1]<=71 and abs(p[0])<=24 and p[2]>=23 and roof(p,n),(0,0,-20),105.64)]
    for sign,name,ref in ((-1,'left_main_root_down_5N',24.95),(1,'right_main_root_down_5N',24.28)):
        cases.append(mk(name,lambda p,n,s=sign:15<=s*p[0]<=26 and 36.5<=p[1]<=40.5 and p[2]>=19 and n[2]>.5,(0,0,-5),ref))
    for cy,ref in ((50,34.47),(65,29.37)):
        w=float(width(cy));h=float(height(cy));wall=w*(1-((15-5)/(h-5))**3.4)**(1/3.4);xf=wall-14.62
        cases.append(mk(f'side_{cy}_fence_5N',lambda p,n,c=cy,x=xf:abs(p[0]-x)<.06 and c-4.2<=p[1]<=c+8.2 and 9.65<=p[2]<=14.0 and n[0]>.8,(-5,0,0),ref))
    pp=[]
    for s in (-1,1):
        w,m=patch(faces,lambda p,n,s=s:35<=p[1]<=68 and 7<=p[2]<=12 and s*n[0]>.7 and s*p[0]>28)
        pp.append((w,m,(-2*s,0,0)))
    cases.append(case('LC3_squeeze_2x2N',pp,496.43))
    for x,y,name,ref in ((14,60,'press_A_d16',62.21),(-14,72,'press_B_d16',56.21)):
        cases.append(mk(name,lambda p,n,x=x,y=y:(p[0]-x)**2+(p[1]-y)**2<=64 and roof(p,n),(0,0,-5),ref))
    inputs=dict(mesh_mm=size,foot_nodes=len(footnodes),inplane_pin_node=pin,inplane_roller_node=roller,loads=[{k:v for k,v in c.items() if k!='forces'} for c in cases],limitations='Document does not define exact main-root, grip, fence patch boundaries, three in-plane constraint coordinates, nodal load integration or stiffness displacement metric. These independently stated choices cannot certify the author\'s +/-3% reproduction criterion.')
    (OUT/f'K3_inputs_{size:g}.json').write_text(json.dumps(inputs,indent=2))
    rows=solve(work,nodes,elems,bc,cases)
    (OUT/f'K3_independent_R32_{size:g}.json').write_text(json.dumps(dict(inputs=inputs,results=rows,exact_author_reproduction_certified=False),indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('task',choices=['beam','body','beam_pair']);ap.add_argument('--size',type=float,default=2.4);a=ap.parse_args()
    if a.task=='beam_pair':beam(2.4);beam(1.6)
    else:{'beam':beam,'body':body}[a.task](a.size)
