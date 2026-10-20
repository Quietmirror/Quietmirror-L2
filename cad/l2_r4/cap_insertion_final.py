"""Final G6 cap/PET insertion against the complete original saved BODY.

No bounded-region clipping is used. Every 0.25 mm pose retains its full
Boolean common volume; physical side-motion checks remain a separate gate.
"""
from common import *
from side_module import KEYS

def main():
    body=load('BODY');rows=[]
    assert body.isValid() and len(body.Solids())==1
    for k in KEYS:
        cap=load(k['name'])
        shim=load(k['short']+'_TUNING_SHIM_0p33',OUT/'reference')
        actor=cq.Compound.makeCompound([cap,shim]);poses=[]
        for dx in np.arange(10.,-.001,-.25):
            common=actor.translate((float(dx),0,0)).intersect(body)
            overlap=vol(common)
            poses.append(dict(a=k['name']+' + PET',b='BODY',dx_mm=float(dx),
                overlap_mm3=overlap,gap_mm=None,pass_check=overlap<=.001,
                nearest_points_mm=[],method='Exact common volume of complete saved BODY and complete cap+PET; no clipping'))
            print('CAP_INSERT_FULL',k['short'],float(dx),overlap,flush=True)
        rows.append(dict(part=k['name'],method='Exact complete-solid -X translation at 0.25 mm intervals',
            samples=poses,passed=all(p['pass_check'] for p in poses)))
        save('key_insertion_exact.json',rows)
    assert len(rows)==2 and all(r['passed'] for r in rows), 'Complete BODY cap insertion failed'

if __name__=='__main__':main()
