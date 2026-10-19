"""Six-DOF battery route proposal followed by exact BRep acceptance.

The signed-distance grid only plans a candidate. It never certifies clearance.
The actual 18x22x6 envelope and retained frame are checked at every replay pose.
"""
import math,time
import numpy as np
from scipy.ndimage import distance_transform_edt,map_coordinates
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
from common import *
from assembly_paths import H,LO,N,voxelize

def matrix(p):return Rotation.from_euler('xyz',p[3:],degrees=True).as_matrix()
def moved(s,pivot,p):
    out=s
    for i,axis in enumerate(np.eye(3)):
        out=out.rotate(tuple(pivot),tuple(pivot+axis),float(p[i+3]))
    return out.translate(tuple(p[:3]))

class Tree:
    def __init__(self,p):self.nodes=[np.asarray(p,float)];self.parents=[-1];self.kd=None;self.built=0
    def nearest(self,p):
        if self.kd is None or len(self.nodes)-self.built>=64:
            self.kd=cKDTree(np.array(self.nodes)*SCALE);self.built=len(self.nodes)
        distance,index=self.kd.query(p*SCALE)
        if len(self.nodes)>self.built:
            ds=np.linalg.norm((np.array(self.nodes[self.built:])-p)*SCALE,axis=1);j=int(ds.argmin())
            if ds[j]<distance:index=self.built+j
        return int(index)
    def add(self,p,parent):self.nodes.append(p);self.parents.append(parent);return len(self.nodes)-1
    def path(self,i):
        path=[]
        while i!=-1:path.append(self.nodes[i]);i=self.parents[i]
        return path[::-1]

SCALE=np.array([1,1,1,.15,.15,.15])

def main():
    began=time.time();rng=np.random.default_rng(20261019)
    cell=load('BATTERY_CELL_EST',OUT/'reference');pivot=np.array(cell.Center().toTuple())
    fixed={'BODY':load('BODY'),**{n:load(n) for n in ['SF_RETAINER','SR_RETAINER']}}
    fixed.update({n:load(n,OUT/'reference') for n in ['SF_D2F_01F','SR_D2F_01F','SF_VERTICAL_PIN','SR_VERTICAL_PIN','SF_RETAINER_M2x5','SR_RETAINER_M2x5']})
    occ=np.zeros(tuple(N),bool)
    for name,s in fixed.items():v,_=voxelize(s);occ|=v
    field=(distance_transform_edt(~occ)*H).astype(np.float32)
    # Exact box surface samples plus an interior grid. This is a planner,
    # so all accepted routes are subsequently checked against actual solids.
    half=np.array([9.,11.,3.]);points=[]
    for axis in range(3):
        others=[i for i in range(3) if i!=axis]
        ab=np.array(np.meshgrid(*[np.linspace(-half[i],half[i],int(2*half[i]/.5)+1) for i in others],indexing='ij')).reshape(2,-1).T
        for sign in [-1,1]:
            p=np.zeros((len(ab),3));p[:,axis]=sign*half[axis];p[:,others]=ab;points.append(p)
    points.append(np.mgrid[-8.5:9:1.,-10.5:11:1.,-2.5:3:1.].reshape(3,-1).T)
    points=np.unique(np.vstack(points),axis=0);evaluations=0
    def clear(p):
        nonlocal evaluations;evaluations+=1
        ps=points@matrix(p).T+pivot+p[:3]
        ids=((ps-LO)/H-.5).T
        if np.any(ids[:2]<0) or np.any(ids[0]>=N[0]-1) or np.any(ids[1]>=N[1]-1):return False
        return float(map_coordinates(field,ids,order=1,mode='constant',cval=100.,prefilter=False).min())>=.45
    def edge(a,b):
        count=max(1,int(math.ceil(np.linalg.norm(b[:3]-a[:3])/.5)),int(math.ceil(np.max(np.abs(b[3:]-a[3:]))/2.5)))
        return all(clear(a+(b-a)*t) for t in np.linspace(0,1,count+1)[1:])
    def extend(tree,target):
        i=tree.nearest(target);a=tree.nodes[i];diff=target-a;d=np.linalg.norm(diff*SCALE)
        b=target if d<=.6 else a+diff*(.6/d)
        if not edge(a,b):return None,False
        return tree.add(b,i),d<=.6
    start=np.zeros(6);goal=np.array([17.,0.,25.,0.,0.,0.]);assert clear(start) and clear(goal)
    A=Tree(start);B=Tree(goal)
    for dz in [-28.,28.]:
        for yaw in [-90.,0.,90.]:
            p=np.array([17.,0.,dz,0.,0.,yaw])
            if clear(p):B.add(p,-1)
    # A flat exterior seed gives the reverse tree almost no probability of
    # entering a triangular roof window. Seed already-outside edge-on cells
    # over the actual left/rear openings; all must pass the same planner.
    entry_seeds=[]
    for dx in [-3.,7.,17.]:
        for dy in [-5.,6.,16.]:
            for roll,pitch in [(-90.,0.),(90.,0.),(0.,-90.),(0.,90.)]:
                for yaw in [-90.,-45.,0.,45.,90.]:
                    p=np.array([dx,dy,30.,roll,pitch,yaw])
                    if clear(p):B.add(p,-1);entry_seeds.append(p)
    route=None;attempted=0
    for iteration in range(240000):
        attempted=iteration+1
        if iteration%2:a,b,reverse=A,B,False
        else:a,b,reverse=B,A,True
        choice=rng.random()
        if choice<.45:
            near=a.nodes[int(rng.integers(len(a.nodes)))];target=near+rng.normal(size=6)*np.array([.7,.7,.7,5.,5.,5.])
        elif choice<.65:
            target=np.r_[rng.uniform([-12,-25,-24],[40,25,28]),rng.uniform(-90,90,3)]
        elif choice<.85 and not reverse:
            # Biased toward edge-on roof entry instead of an unconstrained
            # random walk within the trapped battery bay.
            target=entry_seeds[int(rng.integers(len(entry_seeds)))].copy()
            target[:3]+=rng.normal(size=3)*np.array([2.,2.,2.])
        else:target=b.nodes[int(rng.integers(len(b.nodes)))]
        target[3:]=np.clip(target[3:],-120,120)
        ai,_=extend(a,target)
        if ai is not None:
            for _ in range(90):
                bi,reached=extend(b,a.nodes[ai])
                if bi is None:break
                if reached:
                    left=a.path(ai);right=b.path(bi)
                    route=right+left[::-1][1:] if reverse else left+right[::-1][1:]
                    break
        if route is not None:break
        if iteration%1000==0:print('BATTERY_RRT',iteration,len(A.nodes),len(B.nodes),evaluations,round(time.time()-began),flush=True)
    extreme={}
    for axis in range(6):
        for label,fn in [('min',np.argmin),('max',np.argmax)]:
            node=int(fn(np.array(A.nodes)[:,axis]));extreme[str(axis)+label]=[p.tolist() for p in A.path(node)]
    report=dict(exterior_edge_on_seeds=len(entry_seeds),reachable_extreme_paths=extreme,reachable_start_bounds=np.array(A.nodes).min(0).tolist()+np.array(A.nodes).max(0).tolist(),found=route is not None,planner='Six-DOF bidirectional RRT with edge-on roof-entry seeds; approximate grid only proposes route',grid_mm=H,planning_clearance_mm=.45,exact_required_clearance_mm=.5,attempted_iterations=attempted,nodes=[len(A.nodes),len(B.nodes)],planner_evaluations=evaluations,rotation_order='global X then Y then Z about battery centre; pose dx/dy/dz/roll/pitch/yaw',pivot_mm=pivot.tolist(),battery_estimated_size_mm=[18,22,6],retained_obstacles=list(fixed),service_sequence=['Disconnect battery plug and free wiring','Remove main keys, wheel carrier and removable H electronics stack','Move rigid cell along reported route; integral BODY and side module stay assembled'],limitation='Exact finite-pose rigid-envelope check, not physical handling or adhesive peel proof.',passed=False)
    save('battery_service_path.json',report)
    if route is None:raise RuntimeError('No accepted six-DOF route; do not mark battery service passed')
    # Shortcut only when the planner checks the connecting segment too.
    for _ in range(150):
        if len(route)<3:break
        i,j=sorted(rng.choice(len(route),2,replace=False))
        if j>i+1 and edge(route[i],route[j]):route=route[:i+1]+route[j:]
    replay=[]
    for a,b in zip(route[:-1],route[1:]):
        count=max(1,int(math.ceil(np.linalg.norm(b[:3]-a[:3])/.25)),int(math.ceil(np.max(np.abs(b[3:]-a[3:]))/2.5)))
        replay.extend((a+(b-a)*t).tolist() for t in np.linspace(0,1,count+1))
    exact=[]
    for i,p in enumerate(replay):
        r=scene_pairs(moved(cell,pivot,p),fixed,'BATTERY_CELL_EST',.5);exact.append(dict(pose_index=i,pose=p,**r));print('BATTERY_EXACT',i,len(replay),r['exact_global_minimum_mm'],r['passed'],flush=True)
    report.update(route=[p.tolist() for p in route],replay_poses=len(replay),exact_all_poses=exact,passed=all(r['passed'] for r in exact),elapsed_s=time.time()-began);save('battery_service_path.json',report)
    plug=load('BATTERY_PLUG_EST',OUT/'reference');pb=plug.BoundingBox();probes=[]
    for x in [pb.xmin-.55,pb.xmax+.55]:
        probe=box(x-.5,x+.5,pb.ymin+.5,pb.ymax-.5,pb.zmin,40);probes.append(dict(bounds_mm=bounds(probe),**scene_pairs(probe,fixed,'BATTERY_PLUG_ACCESS_FINGER',.05)))
    save('battery_plug_access.json',dict(probes=probes,plug_bounds_mm=bounds(plug),passed=all(r['passed'] for r in probes),definition='Two 1mm tool fingers from +Z after removable modules are removed.'))
if __name__=='__main__':main()
