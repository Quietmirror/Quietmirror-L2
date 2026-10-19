"""Combine six verified window jobs without reducing their sample domains."""
import json
from common import *
import evidence_identity as evidence
import window_checks

def main():
    rows=[];versions=[]
    for i in range(6):
        name=f'window_{i}.json';check=evidence.verify([name])[0];versions.append(check)
        assert check['passed'],check
        part=json.loads((RP/name).read_text());assert len(part)==1
        r=part[0]
        assert len(r['boundary'])==200 and len(r['full_prism'])==1000 and len(r['roof_shell_band'])==1000
        rows.append(r)
    assert len({r['window'] for r in rows})==6
    save('six_window_samples.json',rows);save('window_partition_identity.json',versions)

if __name__=='__main__':main()
