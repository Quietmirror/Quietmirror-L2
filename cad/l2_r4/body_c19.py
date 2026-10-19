"""Source rebuild of the middle-seat clearance correction; no STEP patching."""
from common import *
from exact_distance import pair
import build_body
from contact_audit_final import mate

def main():
    old=load('BODY')
    build_body.main()
    new=load('BODY')
    removed=vol(old.cut(new));added=vol(new.cut(old))
    low=box(-75,75,-31,119,-5,5.1)
    before=old.intersect(low);after=new.intersect(low)
    low_removed=vol(before.cut(after));low_added=vol(after.cut(before))
    switch=load('SWITCH_MIDDLE',OUT/'reference')
    check=pair(new,switch,'BODY','SWITCH_MIDDLE',.5)
    feature=load('SWITCH_MIDDLE_MOUNT',OUT/'validation_features')
    contact=mate(switch,new,feature,'SWITCH_MIDDLE','BODY',.5,'original middle micro seat and bolt holders',check)
    feet=[]
    metadata=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text())
    for f in metadata['mechanisms']['feet']:
        zone=cyl(4.05,15,(*f['center'],-5))
        a=old.intersect(zone);b=new.intersect(zone)
        feet.append(dict(center=f['center'],removed_mm3=vol(a.cut(b)),added_mm3=vol(b.cut(a))))
    row=dict(valid=new.isValid(),solids=len(new.Solids()),volume_mm3=vol(new),removed_mm3=removed,added_mm3=added,
             unchanged_below_z_mm=5.1,lower_region_removed_mm3=low_removed,lower_region_added_mm3=low_added,
             feet=feet,middle_raw=check,middle_functional_contact=contact,
             scope='Source rebuilt middle-seat tie leveling and terminal-clearance slots. Five foot regions and bottom low band compared explicitly. Full G1-G11 verification must follow.')
    save('BODY_C19.json',row);print(row,flush=True)
    assert row['valid'] and row['solids']==1 and added<=.001
    assert low_removed<=.001 and low_added<=.001 and check['overlap_mm3']<=.001 and contact['passed']
    assert len(feet)==5 and all(f['removed_mm3']<=.001 and f['added_mm3']<=.001 for f in feet)

if __name__=='__main__':main()
