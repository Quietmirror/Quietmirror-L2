"""Exact final cap/PET boundary and source subset certificate."""
from common import *
from side_module import KEYS,key

def main():
    outer=load('MOTHER_OUTER_FROM_R32_SURFACE',ROOT/'exports/l2_r2_diagnostic/support_reference');rows=[]
    for k in KEYS:
        old,_=key(outer,k);new=load(k['name']);shim=load(k['short']+'_TUNING_SHIM_0p33',OUT/'reference')
        match=pair(new,shim,k['name'],k['short']+'_TUNING_SHIM_0p33',0.)
        row=dict(part=k['name'],shim=match,added_material_mm3=vol(new.cut(old)),removed_material_mm3=vol(old.cut(new)),valid=new.isValid(),solids=len(new.Solids()))
        row['passed']=match['pass_check'] and row['added_material_mm3']<=.001 and row['solids']==1 and row['valid'];rows.append(row);print('CAP_FINISH',row,flush=True)
    save('cap_pad_join_finish.json',dict(rows=rows,passed=all(r['passed'] for r in rows),definition='C9 source cap minus the rod crescent outside the backing sphere; exact STEP roundtrip inspected.'))
    assert all(r['passed'] for r in rows),'Cap/PET join remains unresolved'

if __name__=='__main__':main()
