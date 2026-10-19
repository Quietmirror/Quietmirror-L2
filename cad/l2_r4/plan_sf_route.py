"""Find an SF route with the actual installed SR terminals present.

FFT correlation constructs finite configuration-space collision maps from the
same 0.25 mm point cloud/voxel representation used by G6. Search uses a stronger
26-neighbor dilation, then the resulting route is independently replayed by
assembly_paths.py, including exact BRep turning-point distances. Search success
alone is never acceptance.
"""
import heapq,json,math,time,os
import numpy as np
from scipy.ndimage import binary_dilation
from scipy.signal import fftconvolve
from common import *
from assembly_paths import H,LO,HI,N,voxelize,inside_points,pivot_from_author,transformed

def main():
    starttime=time.time();body=load('BODY');sr=load('SR_D2F_01F',OUT/'reference');sf=load('SF_D2F_01F',OUT/'reference')
    base,grid=voxelize(body);extra,_=voxelize(sr);occ=binary_dilation(base|extra,np.ones((3,3,3),bool)).astype(np.float32)
    specs=json.loads((ROOT/'cad/l2_r4_author/loose_parts.json').read_text(encoding='utf-8-sig'))
    pts=inside_points(sf);pivot=pivot_from_author(specs['SF_switch']['boxes'])
    axes=[np.arange(-80,9),np.arange(-8,81),np.arange(-60,41)];shape=(19,*[len(a) for a in axes]);blocked=np.zeros(shape,bool)
    interpolation=[]
    for j,yaw in enumerate(range(0,91,5)):
        rotated=transformed(pts,pivot,[0,0,0,yaw]);indices=np.floor((rotated-LO)/H).astype(int)
        mn=indices.min(0);mx=indices.max(0);size=mx-mn+1;kernel=np.zeros(size,np.float32);kernel[tuple((indices-mn).T)]=1
        corr=fftconvolve(occ,kernel[::-1,::-1,::-1],mode='full')
        ix=[axis+mn[d]+size[d]-1 for d,axis in enumerate(axes)]
        assert all(a.min()>=0 and a.max()<corr.shape[d] for d,a in enumerate(ix))
        values=corr[np.ix_(*ix)];error=float(np.max(np.abs(values-np.rint(values))))
        assert error<.25,('Correlation precision insufficient',error)
        blocked[j]=values>.5
        # XY outside the voxel workspace and Z above it are not empty space.
        for d in range(3):
            invalid=(axes[d]+mx[d]>=N[d])
            if d<2:invalid|=(axes[d]+mn[d]<0)
            sl=[slice(None)]*3;sl[d]=invalid;blocked[j][tuple(sl)]=True
        interpolation.append(dict(yaw_deg=yaw,maximum_roundoff=error,blocked_states=int(blocked[j].sum())))
        print('CONFIGURATION_MAP',yaw,'blocked',int(blocked[j].sum()),'seconds',round(time.time()-starttime,1),flush=True)
        del corr,values,kernel
    sx,sy,sz=shape[1:];plane=sy*sz;orient=sx*plane
    def pack(q):a,x,y,z=q;return a*orient+x*plane+y*sz+z
    def unpack(i):a,r=divmod(i,orient);x,r=divmod(r,plane);y,z=divmod(r,sz);return (a,x,y,z)
    def encode(p):return (int(round(p[3]/5)),*[int(round(p[d]/H))-int(axes[d][0]) for d in range(3)])
    def decode(q):return [float(axes[d][q[d+1]]*H) for d in range(3)]+[float(q[0]*5)]
    start=encode([-15.75,16.,-14.75,90]);goal=encode([-.5,0.,.5,0]);assert not blocked[start] and not blocked[goal],('Endpoint blocked',bool(blocked[start]),bool(blocked[goal]))
    flat=blocked.ravel();sid,gid=pack(start),pack(goal)
    def heuristic(q):return sum(abs(q[d]-goal[d]) for d in [1,2,3])+4*abs(q[0]-goal[0])
    heap=[(1.12*heuristic(start),0,sid)];distance={sid:0};parent={};expanded=0;found=False
    while heap:
        _,cost,node=heapq.heappop(heap)
        if cost!=distance[node]:continue
        if node==gid:found=True;break
        q=unpack(node);expanded+=1
        if expanded%50000==0:print('SEARCH',expanded,'frontier',len(heap),'seconds',round(time.time()-starttime,1),flush=True)
        if expanded>1_500_000:break
        for dim in range(4):
            for sign in [-1,1]:
                v=list(q);v[dim]+=sign
                if not 0<=v[dim]<shape[dim]:continue
                ni=pack(v)
                if flat[ni]:continue
                nc=cost+(4 if dim==0 else 1)
                if nc>=distance.get(ni,10**12):continue
                distance[ni]=nc;parent[ni]=node;heapq.heappush(heap,(nc+1.12*heuristic(v),nc,ni))
    report=dict(source_commit=os.getenv('GITHUB_SHA'),part='SF_D2F_01F',found=found,expanded_states=expanded,
                map_shape=shape,grid_mm=H,yaw_step_deg=5,voxel_method=grid,dilation='26-neighbor 0.25mm, stricter search than the final six-neighbor replay',maps=interpolation,
                exact_acceptance='Requires independent assembly_paths.py replay and exact BRep turning-point checks; no automatic gate pass.')
    if found:
        nodes=[gid]
        while nodes[-1]!=sid:nodes.append(parent[nodes[-1]])
        poses=[decode(unpack(i)) for i in reversed(nodes)];keep=[poses[0]]
        for a,b,c in zip(poses[:-2],poses[1:-1],poses[2:]):
            if not np.allclose(np.array(b)-a,np.array(c)-b,atol=1e-9):keep.append(b)
        keep.append(poses[-1]);report.update(route=keep,search_poses=len(poses))
    save('SF_route_planning.json',report)
    if not found:raise RuntimeError('No SF route found within the declared search domain/budget; no assembly pass claimed')
    print('FOUND_SF_ROUTE',len(keep),'waypoints',len(poses),'poses',flush=True)

if __name__=='__main__':main()
