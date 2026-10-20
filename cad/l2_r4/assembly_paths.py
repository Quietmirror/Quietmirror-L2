"""Replay author waypoints against final BReps, including integral locating pins.

Voxel grid is 0.25 mm; BODY and installed loose parts are dilated by one axial
voxel. Odd ray-parity columns are resolved by exact solid classification rather
than silently discarding a hit. Exact BRep checks cover every waypoint and the
final seating segment, which the author routes leave implicit.
"""
import json,math,time
import numpy as np
from scipy.ndimage import binary_dilation,generate_binary_structure
from common import *
from exact_distance import pair
H=.25;LO=np.array([-40.,-5.,3.]);HI=np.array([40.,95.,35.]);N=np.ceil((HI-LO)/H).astype(int)

def inside_points(s):
    b=s.BoundingBox();xs=np.arange(b.xmin+H/2,b.xmax,H);ys=np.arange(b.ymin+H/2,b.ymax,H);zs=np.arange(b.zmin+H/2,b.zmax,H)
    ps=np.array(np.meshgrid(xs,ys,zs,indexing='ij')).reshape(3,-1).T
    return ps[np.array([s.isInside(V(*p),1e-7) for p in ps])]

def pivot_from_author(boxes):
    ps=[]
    for x0,x1,y0,y1,z0,z1 in boxes:
        ps.append(np.mgrid[x0+H/2:x1:H,y0+H/2:y1:H,z0+H/2:z1:H].reshape(3,-1).T)
    return np.unique(np.round(np.vstack(ps),4),axis=0).mean(0)

def voxelize(s):
    vertices,faces=s.tessellate(.03,.2);v=np.array([p.toTuple() for p in vertices]);tri=v[np.array(faces)]
    hits=[[] for _ in range(N[0]*N[1])];zs=LO[2]+(np.arange(N[2])+.5)*H
    for a,b,c in tri:
        low=np.maximum(0,np.ceil((np.minimum(np.minimum(a,b),c)[:2]-LO[:2])/H-.5).astype(int))
        high=np.minimum(N[:2]-1,np.floor((np.maximum(np.maximum(a,b),c)[:2]-LO[:2])/H-.5).astype(int))
        if np.any(high<low):continue
        den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-12:continue
        ij=np.array(np.meshgrid(np.arange(low[0],high[0]+1),np.arange(low[1],high[1]+1),indexing='ij')).reshape(2,-1).T
        xy=LO[:2]+(ij+.5)*H
        l1=((b[1]-c[1])*(xy[:,0]-c[0])+(c[0]-b[0])*(xy[:,1]-c[1]))/den
        l2=((c[1]-a[1])*(xy[:,0]-c[0])+(a[0]-c[0])*(xy[:,1]-c[1]))/den;l3=1-l1-l2
        ok=(l1>=-1e-10)&(l2>=-1e-10)&(l3>=-1e-10)
        z=l1*a[2]+l2*b[2]+l3*c[2]
        for (i,j),zz in zip(ij[ok],z[ok]):hits[i*N[1]+j].append(float(zz))
    occ=np.zeros(tuple(N),dtype=bool);odd=0
    for ix,zl in enumerate(hits):
        if not zl:continue
        z=np.unique(np.round(zl,5));i,j=divmod(ix,N[1])
        if len(z)%2:
            odd+=1
            for k,zz in enumerate(zs):occ[i,j,k]=s.isInside(V(LO[0]+(i+.5)*H,LO[1]+(j+.5)*H,zz),1e-7)
        else:
            for a,b in zip(z[::2],z[1::2]):occ[i,j,(zs>=a)&(zs<=b)]=True
    print('VOXELS',int(occ.sum()),'exact odd columns',odd,flush=True)
    return occ,dict(grid_mm=H,origin=LO.tolist(),shape=N.tolist(),odd_columns_resolved_by_BRep=odd,triangles=len(tri))

def transformed(ps,c,pose):
    a=math.radians(pose[3]);R=np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]])
    return (ps-c)@R.T+c+np.array(pose[:3])

def moved(s,c,p):return s.rotate(tuple(c),tuple(c+np.array([0,0,1])),p[3]).translate(tuple(p[:3]))

def dense(route):
    out=[]
    for a,b in zip(route[:-1],route[1:]):
        da,db=np.array(a,float),np.array(b,float)
        count=max(1,int(math.ceil(np.linalg.norm(db[:3]-da[:3])/.25)),int(math.ceil(abs(db[3]-da[3])/5)))
        out.extend((da+(db-da)*t).tolist() for t in np.linspace(0,1,count+1))
    return out

def main():
    author=ROOT/'cad/l2_r4_author';routes=json.loads((author/'guided_routes.json').read_text(encoding='utf-8-sig'));specs=json.loads((author/'loose_parts.json').read_text(encoding='utf-8-sig'))
    body=load('BODY');base,grid=voxelize(body)
    installed={};result=[]
    names={'SR_switch':'SR_D2F_01F','SF_switch':'SF_D2F_01F','SR_retainer':'SR_RETAINER','SF_retainer':'SF_RETAINER'}
    for step in routes['sequence']:
        old=step['part'];name=names[old];s=load(name,OUT/('reference' if old.endswith('switch') else 'parts'))
        ps=inside_points(s);c=pivot_from_author(specs[old]['boxes']);occ=binary_dilation(base,generate_binary_structure(3,1))
        original_way=step['route'];way=[list(p) for p in original_way]
        if old=='SF_switch' and (RP/'SF_route_planning.json').exists():
            planned=json.loads((RP/'SF_route_planning.json').read_text())
            if planned.get('found'):way=planned['route']
        if old.endswith('retainer'):
            for p in way:
                if abs(p[2]-.3)<1e-8:p[2]=.55
        samples=dense(way);bad=[]
        for j,p in enumerate(samples):
            pp=transformed(ps,c,p);idx=np.floor((pp-LO)/H).astype(int);ok=np.all((idx>=0)&(idx<N),axis=1)
            outside_bad=(~ok)&((idx[:,2]>=0)|(idx[:,0]<0)|(idx[:,0]>=N[0])|(idx[:,1]<0)|(idx[:,1]>=N[1]))
            hits=0 if not ok.any() else int(occ[tuple(idx[ok].T)].sum())
            if outside_bad.any() or hits:bad.append(dict(sample=j,pose=p,hits=hits,outside_invalid=int(outside_bad.sum())))
        exact=[]
        for j,p in enumerate(way):
            actor=moved(s,c,p);pairs=[pair(actor,body,name,'BODY',.25)]
            pairs.extend(pair(actor,b,name,n,.25) for n,b in installed.items())
            exact.append(dict(waypoint=j,pose=p,pairs=pairs))
        seating=[]
        seating_way=[way[-1],[0.,0.,.55,0.],[0.,0.,0.,0.]] if old.endswith('retainer') else [way[-1],[0.,0.,0.,0.]]
        for p in dense(seating_way):
            actor=moved(s,c,p);pairs=[pair(actor,body,name,'BODY',0.)]
            pairs.extend(pair(actor,b,name,n,0.) for n,b in installed.items())
            seating.append(dict(pose=p,pairs=pairs))
        r=dict(part=name,source_waypoints=original_way,executed_waypoints=way,pivot=c.tolist(),point_count=len(ps),voxel_poses=len(samples),
               starts_below_rim=float(transformed(ps,c,way[0])[:,2].max())<4.8,voxel_collisions=bad,
               exact_turnpoints=exact,exact_final_seating=seating,
               note='Final seating permits only explicitly designed contacts. Raw contact records retained; not an automatic functional exception.')
        r['raw_pass']=r['starts_below_rim'] and not bad and all(p['pass_check'] for x in exact+seating for p in x['pairs'])
        result.append(r);save('assembly_routes_final.json',dict(grid=grid,sequence=result));print('ROUTE',name,'voxel_bad',len(bad),'raw_pass',r['raw_pass'],flush=True)
        # Always include physically seated earlier parts to avoid a cascade of
        # optimistic checks after a failed route. That failure remains recorded.
        installed[name]=s;add,_=voxelize(s);base|=add

if __name__=='__main__':main()
