"""Find and replay a rigid battery service path with removable modules absent.

The battery size remains an estimate. This checks the final integral frame and
retained side switches/retainers; it does not assert that the battery can be
replaced through a fully assembled mouse without removing the other modules.
"""
import heapq,json,math,time
import numpy as np
from scipy.ndimage import binary_dilation
from scipy.signal import fftconvolve
from common import *
from assembly_paths import H,LO,N,voxelize,inside_points,dense

def transform(points,pivot,pose):
    a=math.radians(pose[3]);r=np.array([[math.cos(a),0,math.sin(a)],[0,1,0],[-math.sin(a),0,math.cos(a)]])
    return (points-pivot)@r.T+pivot+np.array(pose[:3])

def moved(shape,pivot,pose):
    return shape.rotate(tuple(pivot),tuple(pivot+np.array([0,1,0])),pose[3]).translate(tuple(pose[:3]))

def main():
    starttime=time.time();body=load('BODY');battery=load('BATTERY_CELL_EST',OUT/'reference')
    pivot=np.array(battery.Center().toTuple());pts=inside_points(battery)
    fixed={'BODY':body}
    for n in ['SF_RETAINER','SR_RETAINER']:fixed[n]=load(n)
    for n in ['SF_D2F_01F','SR_D2F_01F','SF_VERTICAL_PIN','SR_VERTICAL_PIN','SF_RETAINER_M2x5','SR_RETAINER_M2x5']:
        fixed[n]=load(n,OUT/'reference')
    base,grid=voxelize(body)
    for n,s in fixed.items():
        if n!='BODY':additional,_=voxelize(s);base|=additional
    occ=binary_dilation(base,np.ones((3,3,3),bool),iterations=2).astype(np.float32)
    # Translation0.5mm search, independently replayed at<=0.25mm afterwards.
    axes=[np.arange(-48,141,2),np.arange(-140,101,2),np.arange(-128,81,2)]
    angles=list(range(-90,91,5));shape=(len(angles),*[len(a) for a in axes]);blocked=np.zeros(shape,bool);maps=[]
    for j,angle in enumerate(angles):
        ps=transform(pts,pivot,[0,0,0,angle]);ix=np.floor((ps-LO)/H).astype(int)
        mn,mx=ix.min(0),ix.max(0);sz=mx-mn+1;kernel=np.zeros(sz,np.float32);kernel[tuple((ix-mn).T)]=1
        corr=fftconvolve(occ,kernel[::-1,::-1,::-1],mode='full')
        selected=[axis+mn[d]+sz[d]-1 for d,axis in enumerate(axes)]
        valid=[(q>=0)&(q<corr.shape[d]) for d,q in enumerate(selected)]
        clipped=[np.clip(q,0,corr.shape[d]-1) for d,q in enumerate(selected)]
        values=corr[np.ix_(*clipped)];error=float(np.max(np.abs(values-np.rint(values))));assert error<.25,error
        blocked[j]=values>.5
        for d in range(3):
            invalid=(axes[d]+mx[d]>=N[d])
            if d<2:invalid|=(axes[d]+mn[d]<0)
            # Entirely below the grid is intentionally free entry space.
            sl=[slice(None)]*3;sl[d]=invalid;blocked[j][tuple(sl)]=True
        maps.append(dict(rotation_y_deg=angle,roundoff=error));del corr,values,kernel
    sx,sy,sz=shape[1:];plane=sy*sz;orient=sx*plane
    def pack(q):a,x,y,z=q;return a*orient+x*plane+y*sz+z
    def unpack(i):a,r=divmod(i,orient);x,r=divmod(r,plane);y,z=divmod(r,sz);return a,x,y,z
    def encode(p):return (angles.index(round(p[3]/5)*5),*[round((p[d]/H-axes[d][0])/2) for d in range(3)])
    def decode(q):return [float(axes[d][q[d+1]]*H) for d in range(3)]+[float(angles[q[0]])]
    # Search outward from the constrained final bay. Searching inward first
    # exhausted millions of irrelevant free states below the mouse.
    start=encode([0.,0.,0.,0.]);assert not blocked[start],('Battery final pose blocked',bool(blocked[start]))
    def highest(q):
        p=decode(q);a=math.radians(p[3]);return pivot[2]+p[2]+9*abs(math.sin(a))+3*abs(math.cos(a))
    def heuristic(q):return max(0.,highest(q)-2.5)/.5
    sid=pack(start);gid=None;heap=[(1.1*heuristic(start),0,sid)];costs={sid:0};parent={};flat=blocked.ravel();expanded=0;found=False
    while heap:
        _,cost,node=heapq.heappop(heap)
        if cost!=costs[node]:continue
        q=unpack(node)
        if highest(q)<2.5:found=True;gid=node;break
        expanded+=1
        if expanded>4000000:break
        for dim in range(4):
            for sign in [-1,1]:
                v=list(q);v[dim]+=sign
                if not 0<=v[dim]<shape[dim]:continue
                ni=pack(v)
                if flat[ni]:continue
                nc=cost+(2 if dim==0 else 1)
                if nc>=costs.get(ni,10**12):continue
                costs[ni]=nc;parent[ni]=node;heapq.heappush(heap,(nc+1.1*heuristic(v),nc,ni))
    report=dict(found=found,expanded_states=expanded,pivot_mm=pivot.tolist(),rotation_axis='Y through battery centre',grid_mm=H,search_translation_mm=.5,search_rotation_deg=5,maps=maps,
        battery_estimated_size_mm=[18,22,6],retained_obstacles=list(fixed),
        service_sequence=['Disconnect battery plug and free flexible wiring','Remove main keys and removable wheel carrier assembly','Remove screwed H electronics stack if already installed','Move battery along the reversed verified route; side module and integral BODY remain in place'],
        limitation='Rigid estimated battery envelope only; adhesive release and actual cell/plug dimensions require physical verification.',passed=False)
    if not found:save('battery_service_path.json',report);raise RuntimeError('No battery route found within stated search domain; no service-access pass')
    nodes=[gid]
    while nodes[-1]!=sid:nodes.append(parent[nodes[-1]])
    # Reconstruct from the external endpoint into the final bay so this
    # remains an assembly route; reversal is the service extraction route.
    poses=[decode(unpack(i)) for i in nodes];route=[poses[0]]
    for a,b,c in zip(poses[:-2],poses[1:-1],poses[2:]):
        if not np.allclose(np.array(b)-a,np.array(c)-b,atol=1e-9):route.append(b)
    route.append(poses[-1]);replay=dense(route);bad=[]
    for j,p in enumerate(replay):
        pp=transform(pts,pivot,p);ix=np.floor((pp-LO)/H).astype(int);ok=np.all((ix>=0)&(ix<N),axis=1)
        hits=0 if not ok.any() else int(occ[tuple(ix[ok].T)].sum())
        invalid=(~ok)&((ix[:,2]>=0)|(ix[:,0]<0)|(ix[:,0]>=N[0])|(ix[:,1]<0)|(ix[:,1]>=N[1]))
        if hits or invalid.any():bad.append(dict(pose=j,offset=p,hits=hits,outside_invalid=int(invalid.sum())))
    exact=[]
    for j,p in enumerate(route):
        scene=scene_pairs(moved(battery,pivot,p),fixed,'BATTERY_CELL_EST',.5)
        exact.append(dict(waypoint=j,pose=p,**scene));print('BATTERY_TURN',j,len(route),scene['exact_global_minimum_mm'],scene['passed'],flush=True)
    report.update(route=route,replay_poses=len(replay),voxel_collisions=bad,exact_turnpoints=exact,passed=not bad and all(r['passed'] for r in exact),elapsed_s=time.time()-starttime)
    save('battery_service_path.json',report)
    # A real tool approach to the declared plug after removable modules are
    # removed. The two fingers stop at the plug side faces; no pin/contact
    # insertion dimensions are inferred from the estimated connector box.
    plug=load('BATTERY_PLUG_EST',OUT/'reference');pb=plug.BoundingBox();probes=[]
    for x in [pb.xmin-.55,pb.xmax+.55]:
        probe=box(x-.5,x+.5,pb.ymin+.5,pb.ymax-.5,pb.zmin,40)
        tests=scene_pairs(probe,fixed,'BATTERY_PLUG_ACCESS_FINGER',.05)
        probes.append(dict(bounds_mm=bounds(probe),**tests))
    save('battery_plug_access.json',dict(probes=probes,plug_bounds_mm=bounds(plug),passed=all(p['passed'] for p in probes),definition='Two1mm-thick straight tool fingers approaching from+Z after the explicitly removable modules are removed; no real connector latch/force claim.'))

if __name__=='__main__':main()
