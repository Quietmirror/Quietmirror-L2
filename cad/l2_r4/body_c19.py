"""Source rebuild of the middle-seat clearance correction; no STEP patching."""
from common import *
from exact_distance import pair
import build_body

def main():
    old=load('BODY')
    build_body.main()
    new=load('BODY')
    removed=vol(old.cut(new));added=vol(new.cut(old))
    low=box(-75,75,-31,119,-5,9.0)
    before=old.intersect(low);after=new.intersect(low)
    low_removed=vol(before.cut(after));low_added=vol(after.cut(before))
    check=pair(new,load('SWITCH_MIDDLE',OUT/'reference'),'BODY','SWITCH_MIDDLE',.5)
    row=dict(valid=new.isValid(),solids=len(new.Solids()),volume_mm3=vol(new),removed_mm3=removed,added_mm3=added,
             unchanged_below_z_mm=9.0,lower_region_removed_mm3=low_removed,lower_region_added_mm3=low_added,
             middle_raw=check,scope='Rebuild from mother surfaces; only the middle-tray tie inner cap is leveled to its original seat plane. Full G1-G11 verification must follow.')
    save('BODY_C19.json',row);print(row,flush=True)
    assert row['valid'] and row['solids']==1 and added<=.001
    assert low_removed<=.001 and low_added<=.001 and check['overlap_mm3']<=.001

if __name__=='__main__':main()
