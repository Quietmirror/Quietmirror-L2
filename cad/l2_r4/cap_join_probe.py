"""Exact final cap/PET boundary, source roundtrip and BRep interference check."""
from common import *
from exact_distance import pair
from side_module import KEYS,key
from OCP.BRepAlgoAPI import BRepAlgoAPI_Check

def main():
    outer=load('MOTHER_OUTER_FROM_R32_SURFACE',ROOT/'exports/l2_r2_diagnostic/support_reference');rows=[]
    for k in KEYS:
        old,_=key(outer,k);new=load(k['name']);shim=load(k['short']+'_TUNING_SHIM_0p33',OUT/'reference')
        match=pair(new,shim,k['name'],k['short']+'_TUNING_SHIM_0p33',0.)
        row=dict(part=k['name'],shim=match,added_material_mm3=vol(new.cut(old)),removed_material_mm3=vol(old.cut(new)),valid=new.isValid(),solids=len(new.Solids()))
        row['brep_self_interference_check']=bool(BRepAlgoAPI_Check(new.wrapped,True,True).IsValid())
        row['passed']=match['pass_check'] and row['added_material_mm3']<=.001 and row['removed_material_mm3']<=.001 and row['solids']==1 and row['valid'] and row['brep_self_interference_check'];rows.append(row);print('CAP_FINISH',row,flush=True)
    save('cap_pad_join_finish.json',dict(rows=rows,passed=all(r['passed'] for r in rows),definition='Current source construction compared with STEP roundtrip, exact cap/PET intersection and additional BRepAlgoAPI self-interference check.'))
    assert all(r['passed'] for r in rows),'Cap/PET join remains unresolved'

if __name__=='__main__':main()
