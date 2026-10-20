"""Reproduce author's V2 control to identify final-geometry stiffness changes.

The control is diagnostic only. The printable BODY is still built from source.
Only a matched-material/load/mesh control that reproduces the author's result
within3% can resolve an otherwise unexplained final-author difference.
"""
import json,os,subprocess,sys,hashlib
import numpy as np
from common import load,vol,bounds,valid,cyl,cq,ROOT as ROOT_CAD,OUT
from fem_stage import ROOT,RP,WORK,mesh,solve,L,AUTHOR
import evidence_identity as evidence

def main():
    primary_identity=evidence.verify(['fem/stiffness.json'])[0]
    assert primary_identity['passed'], primary_identity
    gate=json.loads((RP/'G8.json').read_text())
    primary=json.loads((RP/'stiffness.json').read_text())
    assert len(primary)==18 and gate['rows']==primary, 'Diagnostic input differs from the verified primary solves'
    final=load('BODY');released=load('BODY',ROOT/'models/L2_r3/parts')
    outer=load('MOTHER_OUTER_FROM_R32_SURFACE',ROOT/'exports/l2_r2_diagnostic/support_reference')
    frame=load('R4_SIDE_FRAME_ONLY',ROOT/'cad/l2_fem_author/variants')
    control=released.fuse(frame)
    for s in [cyl(1.,80,(-40,56,8.6),(1,0,0)).intersect(outer),cyl(1.2,4.6,(9.9,40.8,7.4)),cyl(1.2,4.6,(-9.9,40.8,7.4)),cyl(1.5,80,(-40,67.5,23),(1,0,0)).intersect(outer)]:control=control.fuse(s)
    control=valid(control.clean(),'AUTHOR_V2_DIAGNOSTIC_CONTROL')
    folder=OUT/'analysis_reference';folder.mkdir(exist_ok=True);step=folder/'AUTHOR_V2_DIAGNOSTIC_CONTROL.step';cq.exporters.export(control,str(step))
    # Complete nearly-coincident BODY booleans proved unreliable in the C19
    # boundary audit. Do not publish their added/removed solids as evidence.
    # This controlled FEM comparison uses two complete, valid input solids.
    differences=dict(author_control_volume_mm3=vol(control),final_volume_mm3=vol(final),
        net_volume_change_mm3=vol(final)-vol(control),
        method='Whole valid-solid adaptive volumes and documented source changes; no unreliable coincident whole-BODY Boolean difference is interpreted.',
        limitation='The controlled difference includes geometry-induced remeshing; individual feature stiffness shares are not inferred.')
    pending=[r for r in gate['rows'] if r['author_difference_requires_investigation']]
    # Root interval discrepancies have their own same-mesh investigation.
    allowed={'LC3_squeeze_2x2N','press_A_d16_x14_y60','press_B_d16_x-14_y72','palm_down_20N'}
    assert all(r['case'] in allowed for r in pending),[(r['case'],r['size_mm']) for r in pending]
    assert pending, 'No unresolved non-root case requires this diagnostic'
    requested={(r['case'],r['size_mm']) for r in pending}
    report=dict(status='RUNNING',cause='Combined source geometry corrections after author V2: D7 concealed hinges/aperture back relief, relocated retainer pilots and locating sockets, explicit driver access and final stop reliefs. Same loads/material/solver settings; comparison includes geometry-induced remeshing. Individual feature shares are not inferred.',
        primary_input_identity=primary_identity,primary_stiffness_sha256=hashlib.sha256((RP/'stiffness.json').read_bytes()).hexdigest(),geometry_difference=differences,final_BODY_sha256=hashlib.sha256((OUT/'parts/BODY.step').read_bytes()).hexdigest(),rows=[])
    for h in [2.4,2.,1.6]:
        d=WORK/f'AUTHOR_V2_CONTROL_h{h:g}';m=mesh(step,d,h);cons,feet=L.foot_constraints(m)
        for loads,desc in L.cases(m):
            if (desc['name'],h) not in requested:continue
            r,u=solve(m,d/desc['name'],cons,loads,desc,feet)
            k=desc['magnitude_N']**2/float(np.sum(loads*u))
            finalrow=next(x for x in gate['rows'] if x['case']==desc['name'] and x['size_mm']==h)
            ref=AUTHOR[desc['name']][[2.4,2.,1.6].index(h)]
            row=dict(size_mm=h,case=desc['name'],control_stiffness_N_per_mm=k,author_stiffness_N_per_mm=ref,control_author_difference_fraction=k/ref-1,final_stiffness_N_per_mm=finalrow['stiffness_N_per_mm'],final_geometry_effect_fraction=finalrow['stiffness_N_per_mm']/k-1,equilibrium_pass=r['equilibrium_pass'],resolved=abs(k/ref-1)<=.03 and r['equilibrium_pass'])
            report['rows'].append(row);(RP/'AUTHOR_GEOMETRY_DIFFERENCE.json').write_text(json.dumps(report,indent=2));print('GEOMETRY_CONTROL',row,flush=True)
            if os.getenv('GITHUB_ACTIONS')=='true':subprocess.run([sys.executable,str(ROOT/'cad/l2_r4/ci_checkpoint.py')],cwd=ROOT,check=True)
        del m
    assert {(x['case'],x['size_mm']) for x in report['rows']}==requested
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
