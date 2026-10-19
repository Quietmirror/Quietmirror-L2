"""Reproduce author's V2 control to identify final-geometry stiffness changes.

The control is diagnostic only. The printable BODY is still built from source.
Only a matched-material/load/mesh control that reproduces the author's result
within3% can resolve an otherwise unexplained final-author difference.
"""
import json,os,subprocess,sys,hashlib
import numpy as np
from common import load,vol,bounds,valid,cyl,cq,ROOT as ROOT_CAD,OUT
from fem_stage import ROOT,RP,WORK,mesh,solve,L,AUTHOR

def main():
    final=load('BODY');released=load('BODY',ROOT/'models/L2_r3/parts')
    outer=load('MOTHER_OUTER_FROM_R32_SURFACE',ROOT/'exports/l2_r2_diagnostic/support_reference')
    frame=load('R4_SIDE_FRAME_ONLY',ROOT/'cad/l2_fem_author/variants')
    control=released.fuse(frame)
    for s in [cyl(1.,80,(-40,56,8.6),(1,0,0)).intersect(outer),cyl(1.2,4.6,(9.9,40.8,7.4)),cyl(1.2,4.6,(-9.9,40.8,7.4)),cyl(1.5,80,(-40,67.5,23),(1,0,0)).intersect(outer)]:control=control.fuse(s)
    control=valid(control.clean(),'AUTHOR_V2_DIAGNOSTIC_CONTROL')
    folder=OUT/'analysis_reference';folder.mkdir(exist_ok=True);step=folder/'AUTHOR_V2_DIAGNOSTIC_CONTROL.step';cq.exporters.export(control,str(step))
    removed=control.cut(final);added=final.cut(control)
    differences=dict(author_control_volume_mm3=vol(control),final_volume_mm3=vol(final),removed_mm3=vol(removed),added_mm3=vol(added),removed_regions=[dict(volume_mm3=vol(s),bounds_mm=bounds(s)) for s in removed.Solids()],added_regions=[dict(volume_mm3=vol(s),bounds_mm=bounds(s)) for s in added.Solids()])
    gate=json.loads((RP/'G8.json').read_text());pending=[r for r in gate['rows'] if r['author_difference_requires_investigation']]
    # Root interval discrepancies have their own same-mesh investigation.
    assert all(r['case']=='LC3_squeeze_2x2N' for r in pending),[(r['case'],r['size_mm']) for r in pending]
    report=dict(status='RUNNING',cause='Combined source geometry corrections after author V2: D7 concealed hinges/aperture back relief, relocated retainer pilots and locating sockets, explicit driver access and final stop reliefs. Same loads/material/solver settings; individual feature shares are not inferred.',
        geometry_difference=differences,final_BODY_sha256=hashlib.sha256((OUT/'parts/BODY.step').read_bytes()).hexdigest(),rows=[])
    for h in [2.4,2.,1.6]:
        d=WORK/f'AUTHOR_V2_CONTROL_h{h:g}';m=mesh(step,d,h);cons,feet=L.foot_constraints(m)
        loads,desc=next((f,d) for f,d in L.cases(m) if d['name']=='LC3_squeeze_2x2N')
        r,u=solve(m,d/desc['name'],cons,loads,desc,feet);k=16./float(np.sum(loads*u))
        finalrow=next(x for x in gate['rows'] if x['case']==desc['name'] and x['size_mm']==h);ref=AUTHOR[desc['name']][[2.4,2.,1.6].index(h)]
        row=dict(size_mm=h,case=desc['name'],control_stiffness_N_per_mm=k,author_stiffness_N_per_mm=ref,control_author_difference_fraction=k/ref-1,final_stiffness_N_per_mm=finalrow['stiffness_N_per_mm'],final_geometry_effect_fraction=finalrow['stiffness_N_per_mm']/k-1,equilibrium_pass=r['equilibrium_pass'],resolved=abs(k/ref-1)<=.03 and r['equilibrium_pass'])
        report['rows'].append(row);(RP/'AUTHOR_GEOMETRY_DIFFERENCE.json').write_text(json.dumps(report,indent=2));print('GEOMETRY_CONTROL',row,flush=True)
        if os.getenv('GITHUB_ACTIONS')=='true':subprocess.run([sys.executable,str(ROOT/'cad/l2_r4/ci_checkpoint.py')],cwd=ROOT,check=True)
        del m
    report['status']='COMPLETED' if all(x['resolved'] for x in report['rows']) else 'REVIEW_REQUIRED'
    (RP/'AUTHOR_GEOMETRY_DIFFERENCE.json').write_text(json.dumps(report,indent=2))
    if report['status']=='COMPLETED':
        (RP/'G8_before_geometry_investigation.json').write_text(json.dumps(gate,indent=2))
        for row in gate['rows']:
            if not row['author_difference_requires_investigation']:continue
            evidence=next(x for x in report['rows'] if x['case']==row['case'] and x['size_mm']==row['size_mm'])
            row['geometry_difference_investigation']=evidence
            row['author_difference_requires_investigation']=not evidence['resolved']
        gate['status']='COMPLETED' if len(gate['rows'])==18 and all(x['passed'] and not x['author_difference_requires_investigation'] for x in gate['rows']) else 'REVIEW_REQUIRED'
        gate['geometry_investigation']='AUTHOR_GEOMETRY_DIFFERENCE.json; all original final-BODY values and reference ratios retained'
        (RP/'G8.json').write_text(json.dumps(gate,indent=2))

if __name__=='__main__':main()
