"""Explicit alternative cell-envelope proposals, with exact CAD acceptance.

No proposal modifies the delivered assembly. Similar package volume does not
establish capacity, chemistry, safety or the required twelve-hour endurance.
The original 18x22x6 estimate and unsuccessful service searches are retained.
"""
import itertools,math,time,json
import numpy as np
from scipy.ndimage import distance_transform_edt,map_coordinates
from common import *
from assembly_paths import H,LO,N,voxelize
from battery_service_rrt import Tree,SCALE,matrix,moved

def main():
    began=time.time();rng=np.random.default_rng(2026101903)
    inv=json.loads((RP/'assembly_inventory.json').read_text())
    printed={n:load(n) for n in inv['printable']}
    hardware={n:load(n,OUT/'reference') for n in inv['H_hardware'] if n not in ['BATTERY_CELL_EST','BATTERY_ROUTE_EST']}
    fixed={n:printed[n] for n in ['BODY','SF_RETAINER','SR_RETAINER','SIDE_FRONT_KEY','SIDE_REAR_KEY']}
    fixed.update({n:hardware[n] for n in ['SF_D2F_01F','SR_D2F_01F','SF_VERTICAL_PIN','SR_VERTICAL_PIN','SF_RETAINER_M2x5','SR_RETAINER_M2x5']})
    occ=np.zeros(tuple(N),bool)
    for s in fixed.values():v,_=voxelize(s);occ|=v
    field=(distance_transform_edt(~occ)*H).astype(np.float32)
    rest=occ.copy()
    for n,s in {**printed,**hardware}.items():
        if n not in fixed:v,_=voxelize(s);rest|=v
    rest_field=(distance_transform_edt(~rest)*H).astype(np.float32);del rest,occ
    outer=load('MOTHER_OUTER_FROM_R32_SURFACE',ROOT/'exports/l2_r2_diagnostic/support_reference')
    outer_grid,_=voxelize(outer);outer_grid=outer_grid.astype(np.float32)
    trials=[];accepted=None
    for dimensions in [[14,28,6],[12,33,6],[16,25,6]]:
        half=np.array(dimensions)/2;cell=box(-half[0],half[0],-half[1],half[1],-half[2],half[2]);pivot=np.zeros(3)
        points=[]
        for axis in range(3):
            other=[i for i in range(3) if i!=axis]
            ab=np.array(np.meshgrid(*[np.linspace(-half[i],half[i],int(2*half[i]/.5)+1) for i in other],indexing='ij')).reshape(2,-1).T
            for sign in [-1,1]:
                q=np.zeros((len(ab),3));q[:,axis]=sign*half[axis];q[:,other]=ab;points.append(q)
        interior=np.array(np.meshgrid(*[np.arange(-h+.5,h,.9) for h in half],indexing='ij')).reshape(3,-1).T
        points=np.unique(np.vstack([*points,interior]),axis=0)
        evaluations=0
        def indices(p):return ((points@matrix(p).T+p[:3]-LO)/H-.5).T
        def clear(p):
            nonlocal evaluations;evaluations+=1
            ids=indices(p)
            if np.any(ids[:2]<0) or np.any(ids[0]>=N[0]-1) or np.any(ids[1]>=N[1]-1):return False
            return float(map_coordinates(field,ids,order=1,mode='constant',cval=100.,prefilter=False).min())>=.65
        def edge(a,b):
            count=max(1,int(math.ceil(np.linalg.norm(b[:3]-a[:3])/.5)),int(math.ceil(np.max(np.abs(b[3:]-a[3:]))/2.5)))
            return all(clear(a+(b-a)*t) for t in np.linspace(0,1,count+1)[1:])
        # Explicit candidate placements are screened before route search;
        # a successful placement still needs exact static and route checks.
        goals=[]
        for x,y,z,yaw in itertools.product(np.arange(-22.,-10.,1.5),np.arange(45.,66.,2.),[14.5,15.5,16.4,17.5,18.5],[0.,90.,-10.,10.]):
            p=np.array([x,y,z,0.,0.,yaw]);ids=indices(p)
            if float(map_coordinates(outer_grid,ids,order=0,mode='constant',cval=0,prefilter=False).min())<.5:continue
            if float(map_coordinates(rest_field,ids,order=1,mode='constant',cval=0,prefilter=False).min())>=.65:goals.append(p)
        trial=dict(dimensions_mm=dimensions,goal_candidates=len(goals),passed=False);trials.append(trial)
        print('CELL_GOALS',dimensions,len(goals),flush=True)
        save('battery_alternative_envelopes.json',dict(trials=trials,accepted=None,passed=False))
        if not goals:continue
        seeds=[]
        for x,y,z,roll,pitch,yaw in itertools.product([-20.,-10.,0.],[30.,45.,60.],[-20.,50.],[-90.,0.,90.],[0.,90.],[-90.,0.,90.]):
            p=np.array([x,y,z,roll,pitch,yaw])
            if clear(p):seeds.append(p)
        A=Tree(goals[0]);B=Tree(seeds[0])
        for p in goals[1:]:A.add(p,-1)
        for p in seeds[1:]:B.add(p,-1)
        def extend(tree,target):
            i=tree.nearest(target);a=tree.nodes[i];diff=target-a;d=np.linalg.norm(diff*SCALE);b=target if d<=.8 else a+diff*(.8/d)
            if not edge(a,b):return None,False
            return tree.add(b,i),d<=.8
        route=None
        for iteration in range(130000):
            a,b,reverse=(A,B,False) if iteration%2 else (B,A,True)
            if rng.random()<.6:
                p=a.nodes[int(rng.integers(len(a.nodes)))];target=p+rng.normal(size=6)*np.array([1.3,1.3,1.3,7.,7.,7.])
            else:target=b.nodes[int(rng.integers(len(b.nodes)))]
            ai,_=extend(a,target)
            if ai is not None:
                for _ in range(70):
                    bi,reached=extend(b,a.nodes[ai])
                    if bi is None:break
                    if reached:
                        left,right=a.path(ai),b.path(bi)
                        route=right+left[::-1][1:] if reverse else left+right[::-1][1:];break
            if route is not None:break
            if iteration%5000==0:print('CELL_SEARCH',dimensions,iteration,len(A.nodes),len(B.nodes),round(time.time()-began),flush=True)
        trial.update(nodes=[len(A.nodes),len(B.nodes)],evaluations=evaluations,route_found=route is not None)
        if route is None:continue
        for _ in range(120):
            if len(route)<3:break
            i,j=sorted(rng.choice(len(route),2,replace=False))
            if j>i+1 and edge(route[i],route[j]):route=route[:i+1]+route[j:]
        candidate=moved(cell,pivot,route[0]);outside=vol(candidate.cut(outer));static=scene_pairs(candidate,{**printed,**hardware},'BATTERY_ALTERNATIVE_EST',.5)
        trial.update(placement=route[0].tolist(),outside_mother_mm3=outside,static=static,route=[p.tolist() for p in route])
        if outside>.001 or not static['passed']:continue
        replay=[]
        for a,b in zip(route[:-1],route[1:]):
            count=max(1,int(math.ceil(np.linalg.norm(b[:3]-a[:3])/.25)),int(math.ceil(np.max(np.abs(b[3:]-a[3:]))/2.5)))
            replay.extend(a+(b-a)*t for t in np.linspace(0,1,count+1))
        exact=[]
        for i,p in enumerate(replay):
            r=scene_pairs(moved(cell,pivot,p),fixed,'BATTERY_ALTERNATIVE_EST',.5);exact.append(dict(pose=p.tolist(),**r));print('CELL_EXACT',dimensions,i,len(replay),r['exact_global_minimum_mm'],r['passed'],flush=True)
        trial.update(exact_poses=exact,passed=all(r['passed'] for r in exact))
        if trial['passed']:
            accepted=trial;cq.exporters.export(candidate,str(OUT/'reference/BATTERY_ALTERNATIVE_PROPOSAL.step'));break
    report=dict(trials=trials,accepted=accepted,elapsed_s=time.time()-began,original_estimate_mm=[18,22,6],planning_clearance_mm=.65,exact_clearance_mm=.5,passed=False,status='ALTERNATIVE_ENVELOPE_PROPOSED' if accepted else 'NO_ACCEPTED_ALTERNATIVE',definition='Proposal only. Original assembly remains unchanged. New package aspect ratio must be explicitly adopted and all affected checks repeated; similar volume is not a capacity claim.',retained_obstacles=list(fixed))
    save('battery_alternative_envelopes.json',report)
    if not accepted:raise RuntimeError('No exact accepted alternative cell package and route')

if __name__=='__main__':main()

