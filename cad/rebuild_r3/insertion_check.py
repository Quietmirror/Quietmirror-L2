"""Finite, ordered insertion routes on delivered meshes; no physical-fit claim."""
from pathlib import Path
import ctypes,json,hashlib,math
import numpy as np
import trimesh
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'cad/rebuild_r2'))
from mesh_motion import from_mesh,intersection

ROOT=Path(__file__).resolve().parents[2];RP=ROOT/'reports/rebuild_r3';OUT=ROOT/'exports/rebuild_r3/assembly'

def main():
    ctypes.windll.kernel32.SetPriorityClass(ctypes.c_void_p(-1),0x4000)
    metrics=json.loads((RP/'cad_metrics.json').read_text())
    design=json.loads((RP/'design_metadata.json').read_text())
    models={n:from_mesh(trimesh.load_mesh(OUT/f'{n}.stl')) for n in metrics}
    fixed=['BODY'];results=[]
    def path(label,names,waypoints,rotation=None):
        samples=[]
        for a,b in zip(waypoints,waypoints[1:]):
            for t in np.linspace(0,1,31):
                state=np.array(a)*(1-t)+np.array(b)*t
                mat=np.eye(4)
                if rotation:
                    mat=trimesh.transformations.rotation_matrix(math.radians(state[3]),[1,0,0],rotation)
                mat[:3,3]+=state[:3]
                hits=[]
                for n in names:
                    m=models[n].transform(mat[:3,:])
                    for f in fixed:
                        v=intersection(m,models[f])
                        if v>.01:hits.append(dict(moving=n,fixed=f,overlap_mm3=v))
                samples.append(dict(state=state.tolist(),conflicts=hits))
        row=dict(label=label,parts=names,fixed=list(fixed),waypoints=waypoints,
                 poses=len(samples),conflicts=[s for s in samples if s['conflicts']],pass_check=not any(s['conflicts'] for s in samples))
        results.append(row);fixed.extend(names)
        print(label,row['pass_check'],len(row['conflicts']),row['conflicts'][:1],flush=True)
    # Reverse the extraction route: enter through the open nose, lower below
    # the high cross-ties, slide to the socket, then lower onto its bottom rail.
    for suffix,cy in [('REAR',65.),('FRONT',50.)]:
        n='SWITCH_SIDE_'+suffix
        entry_x=21.2-(metrics[n]['max'][0]-.6)
        path(n,[n],[[entry_x,-cy-15,4.2],[entry_x,43.5-cy,4.2],[entry_x,43.5-cy,2.2],[entry_x,0,2.2],[0,0,2.2],[0,0,0]])
        clamp='SIDE_'+suffix+'_KEY_SWITCH_CLAMP'
        path(clamp,[clamp],[[0,-cy-20,0],[0,0,0]])
    path('SWITCH_MIDDLE',['SWITCH_MIDDLE'],[[0,-65,4.],[0,0,4.],[0,0,0]])
    for n in ('SWITCH_LEFT','SWITCH_RIGHT'):
        path(n,[n],[[0,-30*math.sin(math.pi/10),30*math.cos(math.pi/10)],[0,0,0]])
    path('WHEEL_SUBASSEMBLY',['WHEEL_CARRIER','WHEEL','ENCODER_EC10E_HOUSING','ENCODER_EC10E_ROTOR','ENCODER_ADAPTER_PCB_EST'],[[0,-60,.4],[0,0,.4],[0,0,0]])
    path('USB_SUBASSEMBLY',['USB_ADAPTER_PCB_REFERENCE','USB_C_REFERENCE'],[[0,-35,0],[0,0,0]])
    for m in design['mechanisms']['main_hinges']:
        path(m['part'],[m['part']],[[0,-3,30],[0,-3,5],[0,0,0]])
    for suffix in ('FRONT','REAR'):
        n='SIDE_'+suffix+'_KEY'
        path(n,[n],[[20,0,0],[0,0,0]])
        path(n+'_CAPTURE_PIN',[n+'_CAPTURE_PIN'],[[0,0,35],[0,0,0]])
    for n,v in [('LEFT_KEY_STEEL_PIN',[50,0,0]),('RIGHT_KEY_STEEL_PIN',[-50,0,0]),('WHEEL_CARRIER_STEEL_PIN',[-50,0,0])]:
        path(n,[n],[v,[0,0,0]])
    result=dict(stages=results,pass_check=all(r['pass_check'] for r in results),samples_per_segment=31,
                scope='Finite ordered polyhedral insertion paths against BODY and previously placed parts. Full threaded fastener insertion and tool handles are not included; encoder PCB is inserted with the wheel group, its screws afterwards. USB PCB+connector entry is included; static hardware and driver-access geometry are checked separately. No claim of continuous swept clearance, assembly force, tool-handle access or printed tolerance.',
                inputs={n:hashlib.sha256((OUT/f'{n}.stl').read_bytes()).hexdigest() for n in metrics})
    (RP/'insertion_checks.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    if not result['pass_check']:raise SystemExit(1)

if __name__=='__main__':main()
