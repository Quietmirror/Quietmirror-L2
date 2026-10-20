"""Actual inherited main-key and complete wheel-group motion, exact distances."""
import json,os,subprocess,sys
import numpy as np
from common import *
from exact_distance import pair
from bounded_scene import scene_pairs
from contact_audit import collar,rigid_housing

def main():
    inv=json.loads((RP/'assembly_inventory.json').read_text());meta=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text())
    parts={n:load(n) for n in inv['printable']};hw={n:load(n,OUT/'reference') for n in inv['H_hardware']}
    features={p.stem:cq.importers.importStep(str(p)).val() for p in (OUT/'validation_features').glob('*.step')}
    rows=[]
    for mo in meta['mechanisms']['motions']:
        n=mo['part']
        if n not in ['LEFT_KEY','RIGHT_KEY','WHEEL_CARRIER']:continue
        group=[n,*mo.get('moving_children',[]),*mo.get('moving_hardware',[])]
        actors={g:parts[g] if g in parts else hw[g] for g in group}
        fixed={bn:b for bn,b in parts.items() if bn not in group}
        # Fixed electronic packages, cables, pins and fasteners are also
        # obstacles. Bearing/seat contacts remain raw for local classification.
        fixed.update({bn:b for bn,b in hw.items() if bn not in group and bn!=mo['switch']})
        # Strip the compressible plunger only; the fixed rigid housing remains
        # an obstacle at every pose. Original switch-body frame is retained.
        housing=rigid_housing(hw[mo['switch']],mo)
        fixed[mo['switch']+'_RIGID_HOUSING']=housing
        named=unite(features[n+'_FIXED_BEARINGS'],features[n+'_PRESS_STOP'])
        nonfunctional_body=parts['BODY'].cut(collar(named,.30001))
        ori=mo['origin'];axis=[ori[0]+1,*ori[1:]];angles=np.array([-4.4,4.1,4.4]) if n=='WHEEL_CARRIER' else np.array([-.5,2.8,3.1])
        samples=[]
        for a in angles:
            pairs=[];scene=[];classified=[]
            for an,actor in actors.items():
                moved=actor.rotate(ori,axis,float(a))
                result=scene_pairs(moved,fixed,an,.3)
                pairs.extend(result['measured_pairs'])
                # Save the pruning proof separately; AABB bounds are never
                # relabelled as nearest BRep distances.
                result['actor']=an
                scene.append(result)
                for r in result['measured_pairs']:
                    c=dict(a=an,b=r['b'],passed=r['pass_check'],classification='ordinary clearance')
                    if not c['passed'] and an==n and r['b']=='BODY':
                        other=pair(moved,nonfunctional_body,an,'BODY',.3)
                        c.update(classification='source-defined fixed hinge and press stop; full common volume retained',nonfunctional=other,
                                 passed=r['overlap_mm3']<=.001 and other['pass_check'])
                    elif not c['passed'] and an==n and r['b']==n+'_STEEL_PIN':
                        c.update(classification='coaxial diameter2.00 pin / diameter2.35 bore',radial_clearance_mm=r['gap_mm'],
                                 passed=r['overlap_mm3']<=.001 and abs(r['gap_mm']-.175)<.01)
                    classified.append(c)
            samples.append(dict(angle_deg=float(a),pairs=pairs,scenes=scene,functional_classification=classified,passed=all(c['passed'] for c in classified)));scene=[]
            print('G5_RAW',n,round(float(a),4),'overlaps',[(r['a'],r['b'],round(r['overlap_mm3'],5)) for r in pairs if r['overlap_mm3']>.001],flush=True)
            if len(samples)%5==0:
                save('motion_endpoint_progress.json',dict(status='PARTIAL_NOT_ACCEPTANCE',group=n,completed_poses=len(samples),expected_poses=len(angles),last_angle_deg=float(a),failures=[dict(angle=s['angle_deg'],items=[c for c in s['functional_classification'] if not c['passed']]) for s in samples if not s['passed']]))
                if os.getenv('GITHUB_ACTIONS')=='true':subprocess.run([sys.executable,str(HERE/'ci_checkpoint.py')],cwd=ROOT,check=True)
        rows.append(dict(group=n,members=group,origin_mm=ori,axis=axis,samples=samples,passed=all(s['passed'] for s in samples),
                         scope='Exact at listed poses; rigid housing and complete wheel children. Functional stops and journals still require local contact classification.'))
        save('motion_endpoint_probe.json',rows)

if __name__=='__main__':main()
