"""Directed coupled lift/rotation hypotheses for the unchanged original cell.

Retain the original18x22x6 estimate. Approximate planning never grants a pass:
every accepted path must survive exact0.5mm BRep clearance replay.
"""
import itertools,json,math,time
import numpy as np
from scipy.ndimage import distance_transform_edt,map_coordinates
from common import *
from bounded_scene import scene_pairs
from assembly_paths import H,LO,N,voxelize
from battery_service_rrt import moved,matrix

def main(dimensions=None,report_name='battery_direct_service.json',raise_on_failure=True,center_mm=None):
    began=time.time();cell=load('BATTERY_CELL_EST',OUT/'reference');pivot=np.array(cell.Center().toTuple())
    dimensions=dimensions or [18,22,6]
    if center_mm is not None:pivot=np.array(center_mm,float)
    if dimensions!=[18,22,6] or center_mm is not None:
        h=np.array(dimensions)/2
        cell=box(pivot[0]-h[0],pivot[0]+h[0],pivot[1]-h[1],pivot[1]+h[1],pivot[2]-h[2],pivot[2]+h[2])
    fixed={n:load(n) for n in ['BODY','SF_RETAINER','SR_RETAINER','SIDE_FRONT_KEY','SIDE_REAR_KEY']}
    fixed.update({n:load(n,OUT/'reference') for n in ['SF_D2F_01F','SR_D2F_01F','SF_VERTICAL_PIN','SR_VERTICAL_PIN','SF_RETAINER_M2x5','SR_RETAINER_M2x5']})
    occ=np.zeros(tuple(N),bool)
    for s in fixed.values():v,_=voxelize(s);occ|=v
    field=(distance_transform_edt(~occ)*H).astype(np.float32)
    half=np.array(dimensions)/2;points=[]
    for axis in range(3):
        other=[i for i in range(3) if i!=axis]
        ab=np.array(np.meshgrid(*[np.linspace(-half[i],half[i],int(2*half[i]/.5)+1) for i in other],indexing='ij')).reshape(2,-1).T
        for sign in [-1,1]:
            q=np.zeros((len(ab),3));q[:,axis]=sign*half[axis];q[:,other]=ab;points.append(q)
    interior=np.array(np.meshgrid(*[np.arange(-h+.5,h,1.) for h in half],indexing='ij')).reshape(3,-1).T
    points=np.unique(np.vstack([*points,interior]),axis=0)
    evaluations=0
    def clear(p):
        nonlocal evaluations;evaluations+=1
        ids=((points@matrix(p).T+pivot+p[:3]-LO)/H-.5).T
        if np.any(ids[:2]<0) or np.any(ids[0]>=N[0]-1) or np.any(ids[1]>=N[1]-1):return False
        return float(map_coordinates(field,ids,order=1,mode='constant',cval=100.,prefilter=False).min())>=.45
    def dense(route,step=.5):
        out=[]
        for a,b in zip(route[:-1],route[1:]):
            count=max(1,int(math.ceil(np.linalg.norm(b[:3]-a[:3])/step)),int(math.ceil(np.max(np.abs(b[3:]-a[3:]))/2.5)))
            out.extend(a+(b-a)*t for t in np.linspace(0,1,count+1))
        return out
    def edge(a,b):return all(clear(p) for p in dense([a,b]))
    zero=np.zeros(6);assert clear(zero)
    proposals=[];accepted=None;tested=0
    for dx,dy,dz,angle,rotaxis,pre in itertools.product([0.,-2.,2.,4.,6.,9.,12.],[-8.,-6.,-4.,-2.,0.,2.,4.,6.,8.],[0.,1.,2.,3.,4.],[-90.,-75.,-60.,60.,75.,90.],[3,4],[False,True]):
        first=np.array([dx,dy,dz,0.,0.,0.]);first[rotaxis]=angle
        prefix=[zero,np.array([0.,dy,0.,0.,0.,0.]),first] if pre else [zero,first]
        if not all(edge(a,b) for a,b in zip(prefix[:-1],prefix[1:])):continue
        for exit_dx,exit_y,exit_z in itertools.product([dx,0.,6.],[-35.,dy,12.],[-32.,32.]):
            middle=first.copy();middle[0]=exit_dx;middle[1]=exit_y
            last=middle.copy();last[2]=exit_z
            route=prefix+[middle,last];tested+=1
            if not all(edge(a,b) for a,b in zip(route[:-1],route[1:])):continue
            exact=[]
            for i,p in enumerate(dense(route,.25)):
                r=scene_pairs(moved(cell,pivot,p),fixed,'BATTERY_CELL_EST',.5);exact.append(dict(pose=p.tolist(),**r))
                print('DIRECT_CELL_EXACT',i,r['exact_global_minimum_mm'],r['passed'],flush=True)
                if not r['passed']:break
            proposal=dict(route=[p.tolist() for p in route],exact_poses=exact,passed=bool(exact) and all(r['passed'] for r in exact));proposals.append(proposal)
            if proposal['passed']:accepted=proposal;break
        if accepted:break
    report=dict(accepted=accepted,proposals=proposals,tested_exit_routes=tested,planner_evaluations=evaluations,elapsed_s=time.time()-began,battery_estimated_size_mm=dimensions,pivot_mm=pivot.tolist(),planning_clearance_mm=.45,exact_clearance_mm=.5,retained_obstacles=list(fixed),passed=bool(accepted),scope='Directed coupled rigid-envelope service hypotheses; formal assembly unchanged; exact finite replay only, not adhesive or handling proof.')
    save(report_name,report)
    if not accepted and raise_on_failure:raise RuntimeError('No directed service route accepted for stated cell estimate')
    return report

if __name__=='__main__':main()
