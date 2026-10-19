"""Plan from actual aperture-entry corridors, then replay every pose exactly.

Outside roots alone poorly sample a triangular aperture. Descend each explicit
orientation toward the actual frame and retain only connected entry prefixes.
No coarse field or search failure is treated as a proof of physical fit.
"""
import itertools,math,time,json,os,sys,subprocess
import numpy as np
from scipy.ndimage import distance_transform_edt,map_coordinates
from common import *
from bounded_scene import scene_pairs
from assembly_paths import H,LO,N,voxelize
from battery_service_rrt import Tree,SCALE,matrix,moved

def main(dimensions,report_name):
    began=time.time();rng=np.random.default_rng(2026102001)
    original=load('BATTERY_CELL_EST',OUT/'reference');pivot=np.array(original.Center().toTuple());half=np.array(dimensions)/2
    cell=box(pivot[0]-half[0],pivot[0]+half[0],pivot[1]-half[1],pivot[1]+half[1],pivot[2]-half[2],pivot[2]+half[2])
    fixed={n:load(n) for n in ['BODY','SF_RETAINER','SR_RETAINER','SIDE_FRONT_KEY','SIDE_REAR_KEY']}
    fixed.update({n:load(n,OUT/'reference') for n in ['SF_D2F_01F','SR_D2F_01F','SF_VERTICAL_PIN','SR_VERTICAL_PIN','SF_RETAINER_M2x5','SR_RETAINER_M2x5']})
    occ=np.zeros(tuple(N),bool)
    for shape in fixed.values():v,_=voxelize(shape);occ|=v
    field=(distance_transform_edt(~occ)*H).astype(np.float32);del occ
    points=[]
    for axis in range(3):
        other=[i for i in range(3) if i!=axis]
        grid=np.array(np.meshgrid(*[np.linspace(-half[i],half[i],int(2*half[i]/.5)+1) for i in other],indexing='ij')).reshape(2,-1).T
        for sign in [-1,1]:
            p=np.zeros((len(grid),3));p[:,axis]=sign*half[axis];p[:,other]=grid;points.append(p)
    grid=np.array(np.meshgrid(*[np.arange(-h+.5,h,.8) for h in half],indexing='ij')).reshape(3,-1).T
    points=np.unique(np.vstack([*points,grid]),axis=0);evaluations=0
    def clear(p):
        nonlocal evaluations;evaluations+=1
        ids=((points@matrix(p).T+pivot+p[:3]-LO)/H-.5).T
        if np.any(ids[:2]<0) or np.any(ids[0]>=N[0]-1) or np.any(ids[1]>=N[1]-1):return False
        return float(map_coordinates(field,ids,order=1,mode='constant',cval=100.,prefilter=False).min())>=.55
    def dense(a,b,linear=.5):
        count=max(1,int(math.ceil(np.linalg.norm(b[:3]-a[:3])/linear)),int(math.ceil(np.max(np.abs(b[3:]-a[3:]))/2.5)))
        return [a+(b-a)*t for t in np.linspace(0,1,count+1)]
    def edge(a,b):return all(clear(p) for p in dense(a,b)[1:])
    zero=np.zeros(6);assert clear(zero)
    A=Tree(zero);B=None;entries=[]
    orientations=[(r,p,y) for r,p in [(-90.,0.),(90.,0.),(0.,-90.),(0.,90.),(0.,0.)] for y in [-60.,-45.,-30.,0.,30.,45.,60.,90.]]
    # Actual aperture approach prefixes, both top and bottom. A seed becomes
    # an internal target only after a continuous sampled link to the exterior.
    for x,y,(roll,pitch,yaw),direction in itertools.product([-23.,-20.,-17.,-14.,-11.],[48.,52.,56.,60.,64.,68.],orientations,[-1,1]):
        outside=np.array([x-pivot[0],y-pivot[1],(50. if direction>0 else -15.)-pivot[2],roll,pitch,yaw])
        if not clear(outside):continue
        near=outside.copy()
        for z in np.arange(49. if direction>0 else -14.,15. if direction>0 else 25.,-1. if direction>0 else 1.):
            p=near.copy();p[2]=z-pivot[2]
            if not edge(near,p):break
            near=p
        if abs(near[2]-outside[2])<8:continue
        if B is None:B=Tree(outside);root=0
        else:root=B.add(outside,-1)
        index=B.add(near,root);entries.append(index)
    assert B is not None and entries,'No sampled aperture entry prefix'
    depths=[B.nodes[i][2]+pivot[2] for i in entries]
    report=dict(dimensions_mm=dimensions,pivot_mm=pivot.tolist(),entry_prefix_count=len(entries),entry_center_z_range_mm=[min(depths),max(depths)],passed=False,status='PLANNING',retained_obstacles=list(fixed))
    save(report_name,report)
    if os.getenv('GITHUB_ACTIONS')=='true':subprocess.run([sys.executable,str(HERE/'ci_checkpoint.py')],cwd=ROOT,check=True)
    route=None
    def extend(tree,target):
        i=tree.nearest(target);a=tree.nodes[i];delta=target-a;length=np.linalg.norm(delta*SCALE);p=target if length<=.8 else a+delta*(.8/length)
        if not edge(a,p):return None,False
        return tree.add(p,i),length<=.8
    # First try direct coupled motion to each already-connected aperture.
    for i in sorted(entries,key=lambda j:np.linalg.norm(B.nodes[j]*SCALE)):
        if edge(zero,B.nodes[i]):route=[zero]+B.path(i)[::-1];break
    for iteration in range(100000):
        if route is not None:break
        a,b,reverse=(A,B,False) if iteration%2 else (B,A,True)
        choice=rng.random()
        if choice<.5:
            near=a.nodes[int(rng.integers(len(a.nodes)))];target=near+rng.normal(size=6)*np.array([.8,.8,.8,6.,6.,6.])
        elif choice<.85:
            target=(B.nodes[entries[int(rng.integers(len(entries)))]] if not reverse else A.nodes[int(rng.integers(len(A.nodes)))]).copy()
        else:target=np.r_[rng.uniform([-12,-15,-20],[28,20,24]),rng.uniform(-100,100,3)]
        ai,_=extend(a,target)
        if ai is not None:
            for _ in range(80):
                bi,reached=extend(b,a.nodes[ai])
                if bi is None:break
                if reached:
                    left,right=a.path(ai),b.path(bi);route=right+left[::-1][1:] if reverse else left+right[::-1][1:];break
        if iteration%10000==0:print('APERTURE_RRT',dimensions,iteration,len(A.nodes),len(B.nodes),round(time.time()-began),flush=True)
    report.update(status='ROUTE_FOUND_PENDING_EXACT' if route is not None else 'NO_ROUTE',nodes=[len(A.nodes),len(B.nodes)],planner_evaluations=evaluations,elapsed_s=time.time()-began)
    save(report_name,report)
    if route is None:raise RuntimeError('No route between actual connected aperture prefixes and stated final bay')
    for _ in range(150):
        if len(route)<3:break
        i,j=sorted(rng.choice(len(route),2,replace=False))
        if j>i+1 and edge(route[i],route[j]):route=route[:i+1]+route[j:]
    replay=[]
    for a,b in zip(route[:-1],route[1:]):replay.extend(dense(a,b,.25))
    report.update(route=[p.tolist() for p in route],replay_poses=len(replay));save(report_name,report)
    if os.getenv('GITHUB_ACTIONS')=='true':subprocess.run([sys.executable,str(HERE/'ci_checkpoint.py')],cwd=ROOT,check=True)
    rows=[]
    for i,p in enumerate(replay):
        r=scene_pairs(moved(cell,pivot,p),fixed,'BATTERY_CELL_PROPOSAL',.5);rows.append(dict(pose=p.tolist(),**r));print('APERTURE_EXACT',i,len(replay),r['exact_global_minimum_mm'],r['passed'],flush=True)
        if not r['passed']:break
    report.update(exact_all_poses=rows,passed=len(rows)==len(replay) and all(r['passed'] for r in rows),scope='Finite exact rigid-envelope path only; reduced envelopes are proposals, capacity and actual handling unverified.',status='EXACT_FINISHED',elapsed_s=time.time()-began)
    save(report_name,report)
    if not report['passed']:raise RuntimeError('Aperture proposal failed exact0.5mm replay')

if __name__=='__main__':main([18,22,6],'battery_aperture_original.json')
