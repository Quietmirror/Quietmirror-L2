"""Find an accessible placement for the SAME cell envelope in the SAME BODY.

Previous fixed-location searches failed. This probes a layout change, not a
smaller cell or relaxed clearance. It never updates assembly geometry itself.
"""
import math,time,json
import numpy as np
from scipy.ndimage import distance_transform_edt,map_coordinates
from common import *
from bounded_scene import scene_pairs
from assembly_paths import H,LO,N,voxelize
from battery_service_rrt import Tree,SCALE,matrix,moved

def main():
    began=time.time();rng=np.random.default_rng(2026101902)
    cell=load('BATTERY_CELL_EST',OUT/'reference');pivot=np.array(cell.Center().toTuple())
    inv=json.loads((RP/'assembly_inventory.json').read_text())
    printed={n:load(n) for n in inv['printable']}
    hardware={n:load(n,OUT/'reference') for n in inv['H_hardware'] if n not in ['BATTERY_CELL_EST','BATTERY_ROUTE_EST']}
    fixed={n:printed[n] for n in ['BODY','SF_RETAINER','SR_RETAINER','SIDE_FRONT_KEY','SIDE_REAR_KEY']}
    fixed.update({n:hardware[n] for n in ['SF_D2F_01F','SR_D2F_01F','SF_VERTICAL_PIN','SR_VERTICAL_PIN','SF_RETAINER_M2x5','SR_RETAINER_M2x5']})
    occ=np.zeros(tuple(N),bool)
    for n,s in fixed.items():v,_=voxelize(s);occ|=v
    field=(distance_transform_edt(~occ)*H).astype(np.float32)
    rest=occ.copy()
    for n,s in {**printed,**hardware}.items():
        if n not in fixed:v,_=voxelize(s);rest|=v
    rest_field=(distance_transform_edt(~rest)*H).astype(np.float32);del rest,occ
    outer=load('MOTHER_OUTER_FROM_R32_SURFACE',ROOT/'exports/l2_r2_diagnostic/support_reference')
    outer_grid,_=voxelize(outer);outer_grid=outer_grid.astype(np.float32)
    half=np.array([9.,11.,3.]);points=[]
    for axis in range(3):
        other=[i for i in range(3) if i!=axis]
        ab=np.array(np.meshgrid(*[np.linspace(-half[i],half[i],int(2*half[i]/.5)+1) for i in other],indexing='ij')).reshape(2,-1).T
        for sign in [-1,1]:
            q=np.zeros((len(ab),3));q[:,axis]=sign*half[axis];q[:,other]=ab;points.append(q)
    points.append(np.mgrid[-8.5:9:1.,-10.5:11:1.,-2.5:3:1.].reshape(3,-1).T);points=np.unique(np.vstack(points),axis=0)
    evaluations=0;attempts=[];accepted=None
    def sample(p):return ((points@matrix(p).T+pivot+p[:3]-LO)/H-.5).T
    def clear(p):
        nonlocal evaluations;evaluations+=1
        ids=sample(p)
        if np.any(ids[:2]<0) or np.any(ids[0]>=N[0]-1) or np.any(ids[1]>=N[1]-1):return False
        return float(map_coordinates(field,ids,order=1,mode='constant',cval=100.,prefilter=False).min())>=.70
    def edge(a,b):
        count=max(1,int(math.ceil(np.linalg.norm(b[:3]-a[:3])/.5)),int(math.ceil(np.max(np.abs(b[3:]-a[3:]))/2.5)))
        return all(clear(a+(b-a)*t) for t in np.linspace(0,1,count+1)[1:])
    seeds=[]
    for dx in [-3.,7.,17.]:
        for dy in [-8.,3.,14.]:
            for roll,pitch in [(0.,0.),(-90.,0.),(90.,0.),(0.,-90.),(0.,90.)]:
                for yaw in [-90.,-45.,0.,45.,90.]:
                    for dz in [-35.,32.]:
                        p=np.array([dx,dy,dz,roll,pitch,yaw])
                        if clear(p):seeds.append(p)
    tree=Tree(seeds[0])
    for p in seeds[1:]:tree.add(p,-1)
    for iteration in range(180000):
        if rng.random()<.65:
            # Final bay poses, biased toward the original left-side pocket.
            target=np.r_[rng.uniform([-10,-18,-4],[23,20,9]),rng.choice([-90.,-45.,0.,45.,90.],3)+rng.normal(size=3)*8]
        else:
            near=tree.nodes[int(rng.integers(len(tree.nodes)))];target=near+rng.normal(size=6)*np.array([1.4,1.4,1.4,8.,8.,8.])
        target[3:]=np.clip(target[3:],-125,125)
        node=tree.nearest(target);a=tree.nodes[node];diff=target-a;d=np.linalg.norm(diff*SCALE)
        p=target if d<=1 else a+diff/d
        if not edge(a,p):continue
        index=tree.add(p,node)
        if -4<p[2]<12 and np.linalg.norm(p[:2])<30:
            ids=sample(p)
            if float(map_coordinates(outer_grid,ids,order=0,mode='constant',cval=0,prefilter=False).min())>.5 and float(map_coordinates(rest_field,ids,order=1,mode='constant',cval=0,prefilter=False).min())>=.70:
                candidate=moved(cell,pivot,p);outside=vol(candidate.cut(outer));check=scene_pairs(candidate,{**printed,**hardware},'BATTERY_LAYOUT_CANDIDATE',.5)
                attempt=dict(pose=p.tolist(),outside_mother_mm3=outside,static=check,passed=outside<=.001 and check['passed']);attempts.append(attempt)
                save('battery_layout_proposal.json',dict(status='SEARCHING',attempts=attempts,passed=False))
                print('LAYOUT',p.tolist(),'outside',outside,'gap',check['exact_global_minimum_mm'],attempt['passed'],flush=True)
                if attempt['passed']:
                    route=tree.path(index)[::-1]
                    for _ in range(80):
                        if len(route)<3:break
                        i,j=sorted(rng.choice(len(route),2,replace=False))
                        if j>i+1 and edge(route[i],route[j]):route=route[:i+1]+route[j:]
                    replay=[]
                    for aa,bb in zip(route[:-1],route[1:]):
                        count=max(1,int(math.ceil(np.linalg.norm(bb[:3]-aa[:3])/.25)),int(math.ceil(np.max(np.abs(bb[3:]-aa[3:]))/2.5)))
                        replay.extend(aa+(bb-aa)*t for t in np.linspace(0,1,count+1))
                    exact=[]
                    for i,pose in enumerate(replay):
                        result=scene_pairs(moved(cell,pivot,pose),fixed,'BATTERY_LAYOUT_CANDIDATE',.5);exact.append(dict(pose=pose.tolist(),**result));print('LAYOUT_ROUTE',i,len(replay),result['exact_global_minimum_mm'],result['passed'],flush=True)
                    if all(r['passed'] for r in exact):accepted=dict(placement=p.tolist(),route=[q.tolist() for q in route],exact_poses=exact,static=attempt);break
                    attempt['route_failures']=[r for r in exact if not r['passed']]
        if iteration%5000==0:print('LAYOUT_SEARCH',iteration,len(tree.nodes),evaluations,round(time.time()-began),flush=True)
    report=dict(status='ACCESSIBLE_LAYOUT_PROPOSED' if accepted else 'NO_ACCEPTED_LAYOUT',accepted=accepted,attempts=attempts,nodes=len(tree.nodes),evaluations=evaluations,elapsed_s=time.time()-began,cell_size_mm=[18,22,6],pivot_mm=pivot.tolist(),planning_clearance_mm=.70,exact_clearance_mm=.5,unchanged=['BODY','all printed mechanical parts','cell dimensions','all other H components'],removed_for_service=['main keys','wheel carrier group','removable H electronics'],definition='Placement proposal only. Rebuild assembly, service reserve and wiring, then repeat every affected gate before acceptance.',passed=False)
    save('battery_layout_proposal.json',report)
    if not accepted:raise RuntimeError('No accessible same-size placement found; CAD battery service remains unresolved')

if __name__=='__main__':main()
