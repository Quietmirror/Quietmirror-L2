"""Combine independently produced complete angular partitions, never omit poses."""
import json
import numpy as np
from common import *
import evidence_identity as evidence
import main_motion_checks  # Bind aggregation to the actual current verifier.

def main():
    result=[];identity=[]
    for short,part in [('left','LEFT_KEY'),('right','RIGHT_KEY'),('wheel','WHEEL_CARRIER')]:
        expected=np.linspace(-4.4,4.4,23) if short=='wheel' else np.linspace(-.5,3.1,25)
        samples=[];first=None
        for i in range(5):
            name=f'motion_{short}_{i}.json';check=evidence.verify([name])[0];identity.append(check)
            assert check['passed'],check
            rows=json.loads((RP/name).read_text());assert len(rows)==1 and rows[0]['group']==part
            row=rows[0];first=first or row
            assert row['members']==first['members'] and row['origin_mm']==first['origin_mm'] and row['axis']==first['axis']
            samples.extend(row['samples'])
        samples.sort(key=lambda s:s['angle_deg'])
        assert len(samples)==len(expected),(part,len(samples),len(expected))
        assert np.allclose([s['angle_deg'] for s in samples],expected,rtol=0,atol=1e-12),part
        result.append(dict(first,samples=samples,passed=all(s['passed'] for s in samples),partition_definition='Five disjoint angular-index sets; all25 main-key or23 wheel-group poses present exactly once'))
    save('main_and_wheel_motion_raw.json',result)
    save('motion_partition_identity.json',identity)

if __name__=='__main__':main()
