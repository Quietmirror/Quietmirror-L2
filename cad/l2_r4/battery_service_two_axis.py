"""Coupled pitch/yaw battery service search with exact finite-pose validation.

No change to cell size or BODY. The two single-axis searches exhausted their
reachable components; this adds diagonal orientation through roof windows.
"""
import heapq,math,time
import numpy as np
from scipy.ndimage import binary_dilation
from scipy.signal import fftconvolve
from common import *
from assembly_paths import H,LO,N,voxelize,inside_points

def matrix(pitch,yaw):
    a,b=map(math.radians,[pitch,yaw]);ry=np.array([[math.cos(a),0,math.sin(a)],[0,1,0],[-math.sin(a),0,math.cos(a)]]);rz=np.array([[math.cos(b),-math.sin(b),0],[math.sin(b),math.cos(b),0],[0,0,1]])
    return rz@ry
def points_at(points,pivot,p):return (points-pivot)@matrix(*p[3:]).T+pivot+np.array(p[:3])
def moved(s,pivot,p):return s.rotate(tuple(pivot),tuple(pivot+[0,1,0]),p[3]).rotate(tuple(pivot),tuple(pivot+[0,0,1]),p[4]).translate(tuple(p[:3]))

def main():
    started=time.time();body=load('BODY');battery=load('BATTERY_CELL_EST',OUT/'reference');pivot=np.array(battery.Center().toTuple());pts=inside_points(battery)
    fixed={'BODY':body,**{n:load(n) for n in ['SF_RETAINER','SR_RETAINER']}}
    fixed.update({n:load(n,OUT/'reference') for n in ['SF_D2F_01F','SR_D2F_01F','SF_VERTICAL_PIN','SR_VERTICAL_PIN','SF_RETAINER_M2x5','SR_RETAINER_M2x5']})
    base,_=voxelize(body)
    for n,s in fixed.items():
        if n!='BODY':v,_=voxelize(s);base|=v
    q=np.mgrid[-2:3,-2:3,-2:3];occ=binary_dilation(base,np.sum(q*q,axis=0)<=4).astype(np.float32)
    axes=[np.arange(-48,141,2),np.arange(-140,101,2),np.arange(-128,161,2)];angles=list(range(-90,91,5));dims=[len(angles),len(angles),*[len(a) for a in axes]]
    strides=[int(np.prod(dims[i+1:])) for i in range(5)];cache={};mapinfo=[]
    def pack(q):return sum(a*b for a,b in zip(q,strides))
    def unpack(i):
        values=[]
        for d in strides:q,i=divmod(i,d);values.append(q)
        return tuple(values)
    def decode(q):return [float(axes[d][q[d+2]]*H) for d in range(3)]+[float(angles[q[0]]),float(angles[q[1]])]
    def blocked(q):
        key=q[:2]
        if key not in cache:
            ps=points_at(pts,pivot,[0,0,0,angles[q[0]],angles[q[1]]]);ix=np.floor((ps-LO)/H).astype(int);mn,mx=ix.min(0),ix.max(0);sz=mx-mn+1
            kernel=np.zeros(sz,np.float32);kernel[tuple((ix-mn).T)]=1
            corr=fftconvolve(occ,kernel[::-1,::-1,::-1],mode='full');selected=[axis+mn[d]+sz[d]-1 for d,axis in enumerate(axes)]
            valid=[(v>=0)&(v<corr.shape[d]) for d,v in enumerate(selected)];clipped=[np.clip(v,0,corr.shape[d]-1) for d,v in enumerate(selected)]
            values=corr[np.ix_(*clipped)];err=float(np.max(np.abs(values-np.rint(values))));assert err<.25,err
            values[~(valid[0][:,None,None]&valid[1][None,:,None]&valid[2][None,None,:])]=0
            cells=values>.5
            for d in range(2):
                bad=(axes[d]+mx[d]>=N[d])|(axes[d]+mn[d]<0);sl=[slice(None)]*3;sl[d]=bad;cells[tuple(sl)]=True
            cache[key]=np.packbits(cells.reshape(-1));mapinfo.append(dict(pitch=angles[q[0]],yaw=angles[q[1]],roundoff=err));print('BATTERY_ORIENTATION',len(cache),key,'seconds',round(time.time()-started),flush=True)
        index=q[2]*dims[3]*dims[4]+q[3]*dims[4]+q[4];return bool(cache[key][index//8]&(1<<(7-index%8)))
    def limits(q):
        p=decode(q);a=math.radians(p[3]);half=9*abs(math.sin(a))+3*abs(math.cos(a));return pivot[2]+p[2]-half,pivot[2]+p[2]+half
    def heuristic(q):
        lo,hi=limits(q);return max(0.,min(hi-2.5,35.5-lo))/.5
    start=(angles.index(0),angles.index(0),*[int(np.where(a==0)[0][0]) for a in axes]);assert not blocked(start)
    sid=pack(start);heap=[(heuristic(start),0,sid)];costs={sid:0};parent={};expanded=0;gid=None
    while heap:
        _,cost,node=heapq.heappop(heap)
        if cost!=costs[node]:continue
        q=unpack(node);lo,hi=limits(q)
        if hi<2.5 or lo>35.5:gid=node;break
        expanded+=1
        if expanded>4000000:break
        for d in range(5):
            for sign in [-1,1]:
                v=list(q);v[d]+=sign;v=tuple(v)
                if not 0<=v[d]<dims[d] or blocked(v):continue
                ni=pack(v);nc=cost+(2 if d<2 else 1)
                if nc>=costs.get(ni,10**12):continue
                parent[ni]=node;costs[ni]=nc;heapq.heappush(heap,(nc+1.1*heuristic(v),nc,ni))
        if expanded%100000==0:print('BATTERY_SEARCH',expanded,'frontier',len(heap),flush=True)
    report=dict(found=gid is not None,expanded_states=expanded,grid_mm=.25,search_translation_mm=.5,search_rotation_deg=5,rotation_order='Y pitch then Z yaw about battery centre',pivot_mm=pivot.tolist(),maps=mapinfo,retained_obstacles=list(fixed),battery_estimated_size_mm=[18,22,6],service_sequence=['Disconnect battery plug and free wiring','Remove main keys, wheel carrier and removable H electronics stack','Tilt and yaw the rigid battery along the reverse of the reported exact route; integral BODY and side module stay assembled'],limitation='Finite rigid-envelope route, not adhesive peel or actual-cell handling proof.',passed=False)
    save('battery_service_path.json',report)
    if gid is None:raise RuntimeError('Coupled pitch/yaw search found no accepted path; no service pass')
    nodes=[gid]
    while nodes[-1]!=sid:nodes.append(parent[nodes[-1]])
    ps=[decode(unpack(i)) for i in nodes];route=[ps[0]]
    for a,b,c in zip(ps[:-2],ps[1:-1],ps[2:]):
        if not np.allclose(np.array(b)-a,np.array(c)-b):route.append(b)
    route.append(ps[-1]);replay=[]
    for a,b in zip(route[:-1],route[1:]):
        a,b=np.array(a),np.array(b);count=max(1,int(math.ceil(np.linalg.norm((b-a)[:3])/.25)),int(math.ceil(np.max(np.abs((b-a)[3:]))/2.5)))
        replay.extend((a+(b-a)*t).tolist() for t in np.linspace(0,1,count+1))
    exact=[]
    for i,p in enumerate(replay):
        r=scene_pairs(moved(battery,pivot,p),fixed,'BATTERY_CELL_EST',.5);exact.append(dict(pose_index=i,pose=p,**r));print('BATTERY_EXACT',i,len(replay),r['exact_global_minimum_mm'],r['passed'],flush=True)
    report.update(route=route,replay_poses=len(replay),exact_all_poses=exact,passed=all(r['passed'] for r in exact),elapsed_s=time.time()-started);save('battery_service_path.json',report)
    plug=load('BATTERY_PLUG_EST',OUT/'reference');pb=plug.BoundingBox();probes=[]
    for x in [pb.xmin-.55,pb.xmax+.55]:
        probe=box(x-.5,x+.5,pb.ymin+.5,pb.ymax-.5,pb.zmin,40);probes.append(dict(bounds_mm=bounds(probe),**scene_pairs(probe,fixed,'BATTERY_PLUG_ACCESS_FINGER',.05)))
    save('battery_plug_access.json',dict(probes=probes,plug_bounds_mm=bounds(plug),passed=all(r['passed'] for r in probes),definition='Two 1mm tool fingers from +Z after specified removable modules are removed; no latch force assertion.'))
if __name__=='__main__':main()
