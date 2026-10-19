"""Collect all31 physical side-key poses plus both explicit stop diagnostics."""
import json
import numpy as np
from common import *
from side_module import KEYS
import evidence_identity as evidence
import side_functional_checks

def main():
    rows=[];versions=[]
    for k,short in zip(KEYS,['sf','sr']):
        physical=[];diagnostics=[];first=None
        for i in range(5):
            name=f'side_{short}_{i}.json';check=evidence.verify([name])[0];versions.append(check);assert check['passed'],check
            data=json.loads((RP/name).read_text());assert len(data)==1 and data[0]['part']==k['name']
            r=data[0];first=first or r;assert r['outward_stop_pass']
            physical.extend(r['samples'][:-2]);diagnostics.append(r['samples'][-2:])
        expected=np.linspace(0,k['angle'],31);physical.sort(key=lambda s:s['angle_deg']*k['sign'])
        assert len(physical)==31 and np.allclose([s['angle_deg'] for s in physical],expected,rtol=0,atol=1e-12)
        assert all(len(d)==2 and all(s['passed'] for s in d) for d in diagnostics)
        for d in diagnostics:
            assert np.allclose([s['angle_deg'] for s in d],[-k['sign']*.5,k['angle']+k['sign']*.3],rtol=0,atol=1e-12)
        samples=physical+diagnostics[0]
        rows.append(dict(first,samples=samples,passed=all(s['passed'] for s in samples) and first['outward_stop_pass'],partition_definition='31 distinct physical poses and two hard-stop diagnostic poses; duplicated diagnostics in all five source jobs also required to pass'))
    save('side_functional_motion.json',rows);save('side_partition_identity.json',versions)

if __name__=='__main__':main()
