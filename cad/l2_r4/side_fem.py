"""S7 3D solid checks: final BODY stop loads + clamp preload and retainers.

The declared preload is 20 N per screw, an engineering assumption rather than
a claimed torque conversion. The stop load is 5 N, applied over its actual
contact patch. Equivalent surface tractions represent contact forces; this is
linear FEM, not a nonlinear frictional contact/printed-material certification.
"""
import json,os,subprocess,sys
import numpy as np
from fem_stage import FC,L,ROOT,RP,WORK,mesh,solve
from side_module import RETAINER_MOUNTS
from surface_patch_load import rectangle_load,self_check

def percentile_region(m,r,d,mask):
    with np.load(d/'result_arrays.npz') as a:
        ei=np.searchsorted(m.eids,a['stress_element_ids']);ip=a['stress_integration_points']-1
        vm=a['von_mises_MPa'];weights=m.quadrature_volumes[ei,ip]
        centroids=m.xyz[m.conn[ei,:4]].mean(axis=1);ok=mask(centroids)
        assert ok.any()
        ix=np.argsort(vm[ok]);w=weights[ok][ix];v=vm[ok][ix];cum=np.cumsum(w)
        return dict(p95_MPa=float(np.interp(.95*cum[-1],cum,v)),maximum_MPa=float(v.max()),sampled_volume_mm3=float(cum[-1]))

def main():
    print('PATCH_INTEGRATION_CHECK',self_check(),flush=True)
    rows=[];RP.mkdir(parents=True,exist_ok=True)
    for h in [2.4,2.,1.6]:
        d=WORK/f'S7_BODY_h{h:g}';m=mesh(ROOT/'models/L2_r4/parts/BODY.step',d,h);cons,feet=L.foot_constraints(m)
        x,y,z=m.centers.T;nx,ny,nz=m.normals.T
        preload=np.zeros((len(m.ids),3));preload_descriptions=[]
        for mount in RETAINER_MOUNTS.values():
            sx,sy=mount['x'],mount['y'];radius=np.hypot(x-sx,y-sy)
            for plane,sg,label in [(12.1,1,'head'),(13.7,-1,'retainer')]:
                f,desc=FC.selected_load(m,(np.abs(z-plane)<.02)&(radius<1.8)&(radius>1.09)&(np.abs(nz)>.95),[0,0,sg],20.,f'preload_{sy}_{label}')
                preload+=f;preload_descriptions.append(desc)
        for name,sx,ya,yb in [('SF_stop',29.74,54.,55.2),('SR_stop',30.04,59.3,60.5)]:
            f,desc=rectangle_load(m,sx,ya,yb,15.9,16.4,5.,name)
            desc.update(screw_preload_N_each=20.,preload_surface_definitions=preload_descriptions,model='Equivalent contact tractions on actual final stop and clamp surfaces; ideal linear elastic supported BODY')
            r,u=solve(m,d/name,cons,f+preload,desc,feet)
            local=percentile_region(m,r,d/name,lambda c:(c[:,0]>15)&(c[:,1]>40)&(c[:,1]<73)&(c[:,2]>10)&(c[:,2]<21.5))
            rows.append(dict(part='BODY',size_mm=h,case=name,global_p95_MPa=r['p95_integration_point_vm_MPa'],side_frame_region=local,equilibrium_pass=r['equilibrium_pass'],passed=r['equilibrium_pass'] and max(local['p95_MPa'],r['p95_integration_point_vm_MPa'])<=10))
            (RP/'S7.json').write_text(json.dumps(dict(status='RUNNING',preload_assumption_N=20,rows=rows),indent=2))
            if os.getenv('GITHUB_ACTIONS')=='true':subprocess.run([sys.executable,str(ROOT/'cad/l2_r4/ci_checkpoint.py')],cwd=ROOT,check=True)
        del m
        for name,xface,ylo,yhi in [('SF_RETAINER',18.5,44.7,54.),('SR_RETAINER',19.,57.,68.)]:
            mount=RETAINER_MOUNTS[name[:2]];sx,sy,py=mount['x'],mount['y'],mount['pin_y']
            d=WORK/f'S7_{name}_h{h:g}';m=mesh(ROOT/'models/L2_r4/parts'/(name+'.step'),d,h)
            x,y,z=m.centers.T;nx,ny,nz=m.normals.T
            bottom=np.flatnonzero(np.abs(m.xyz[:,2]-13.7)<.02)
            assert len(bottom)>6
            a=int(bottom[np.argmin(np.linalg.norm(m.xyz[bottom,:2]-[sx,sy],axis=1))]);b=int(bottom[np.argmin(np.linalg.norm(m.xyz[bottom,:2]-[mount['pin_x'],py],axis=1))])
            cons=[(int(i),3) for i in bottom]+[(a,1),(a,2),(b,1)]
            radial=np.hypot(x-sx,y-sy)
            f,desc=FC.selected_load(m,(np.abs(radial-.85)<.10)&(z>13.8)&(z<16.),[0,0,-1],20.,'thread_preload')
            g,micro=FC.selected_load(m,(np.abs(x-xface)<.02)&(y>=ylo)&(y<=yhi)&(z>14)&(z<19)&(nx>.95),[-1,0,0],.74,'switch_reaction')
            desc.update(name=name+'_preload_and_switch',switch_force_N=.74,screw_preload_N=20.,switch_surface=micro,model='Retainer seated on planar floor with pin/screw lateral anchors; equivalent thread traction, no thread stripping prediction')
            r,u=solve(m,d/'clamp',cons,f+g,desc,None)
            rows.append(dict(part=name,size_mm=h,case=desc['name'],global_p95_MPa=r['p95_integration_point_vm_MPa'],equilibrium_pass=r['equilibrium_pass'],passed=r['equilibrium_pass'] and r['p95_integration_point_vm_MPa']<=10))
            (RP/'S7.json').write_text(json.dumps(dict(status='RUNNING',preload_assumption_N=20,rows=rows),indent=2));del m
            if os.getenv('GITHUB_ACTIONS')=='true':subprocess.run([sys.executable,str(ROOT/'cad/l2_r4/ci_checkpoint.py')],cwd=ROOT,check=True)
    (RP/'S7.json').write_text(json.dumps(dict(status='COMPLETED' if len(rows)==12 and all(r['passed'] for r in rows) else 'FAILED',preload_assumption_N=20,rows=rows),indent=2))

if __name__=='__main__':main()
