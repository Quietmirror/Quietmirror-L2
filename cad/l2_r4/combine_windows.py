"""Combine six verified window jobs without reducing their sample domains."""
import json
from common import *
import evidence_identity as evidence
import window_checks

def main():
    rows=[];versions=[]
    mount=load('SWITCH_MIDDLE_MOUNT',OUT/'validation_features')
    body=load('BODY');original=baseline('BODY')
    for i in range(6):
        name=f'window_{i}.json';check=evidence.verify([name])[0];versions.append(check)
        assert check['passed'],check
        part=json.loads((RP/name).read_text());assert len(part)==1
        r=part[0]
        assert len(r['boundary'])==200 and len(r['full_prism'])==1000 and len(r['roof_shell_band'])==1000
        # Full BODY classification exposed three points in ROOT_TRI_R that
        # belong to the original middle-switch bolt holders (belowZ13.35).
        # The same material exists in R3.2. Classify only points proved in
        # that named source feature, in BOTH complete bodies, below the roof.
        # Preserve every raw occupied flag and the original classification.
        supplement=[]
        for sample in r['full_prism']:
            if sample['classified_pass']:continue
            q=V(*sample['point_mm'])
            confirmed=sample['baseline_inside'] and window_checks.contains(body,q) and window_checks.contains(original,q) and window_checks.contains(mount,q) and q.z<=13.350001
            if confirmed:
                sample['original_classified_pass']=False
                sample['declared_regions'].append('retained_original_middle_switch_mount_below_roof')
                sample['classified_pass']=True
                supplement.append(dict(point_mm=q.toTuple(),source='models/L2_r4/validation_features/SWITCH_MIDDLE_MOUNT.step',baseline_inside=True,final_inside=True,named_source_feature_inside=True))
        if supplement:r['declared_structural_exceptions']['retained_original_middle_switch_mount_below_roof']=bounds(mount)
        r['supplementary_source_classifications']=supplement
        r['classified_pass']=all(p['classified_pass'] for p in r['boundary']+r['full_prism']+r['roof_shell_band'])
        rows.append(r)
    assert len({r['window'] for r in rows})==6
    save('six_window_samples.json',rows);save('window_partition_identity.json',versions)

if __name__=='__main__':main()
