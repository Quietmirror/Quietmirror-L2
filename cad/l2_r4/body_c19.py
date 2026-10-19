"""Source rebuild of the middle-seat clearance correction; no STEP patching."""
from common import *
from exact_distance import pair
import build_body
from contact_audit_final import mate

def difference_volume(a,b):
    # A genuinely empty low-band intersection has no volume and cannot be
    # passed as the left argument to OCCT's boolean cut. Do not catch failed
    # nonempty booleans or treat their errors as zero.
    if not a.Solids():return 0.
    if not b.Solids():return vol(a)
    return vol(a.cut(b))

def main():
    old=load('BODY_C18_BEFORE_C19',OUT/'analysis_reference')
    build_body.main()
    new=load('BODY')
    removed_shape=old.cut(new);added_shape=new.cut(old)
    removed=vol(removed_shape);added=vol(added_shape)
    change_solids=[*removed_shape.Solids(),*added_shape.Solids()]
    change_regions=[dict(bounds_mm=bounds(s),volume_mm3=vol(s)) for s in change_solids]
    # Prove the low band with complete-body difference regions as well;
    # an empty cropped intersection alone is not preservation evidence.
    low_region_clear=all(s.BoundingBox().zmin>=5.1-1e-7 for s in change_solids)
    low=box(-75,75,-31,119,-5,5.1)
    before=old.intersect(low);after=new.intersect(low)
    low_removed=difference_volume(before,after);low_added=difference_volume(after,before)
    switch=load('SWITCH_MIDDLE',OUT/'reference')
    check=pair(new,switch,'BODY','SWITCH_MIDDLE',.5)
    feature=load('SWITCH_MIDDLE_MOUNT',OUT/'validation_features')
    contact=mate(switch,new,feature,'SWITCH_MIDDLE','BODY',.5,'original middle micro seat and bolt holders',check)
    feet=[]
    metadata=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text())
    for f in metadata['mechanisms']['feet']:
        zone=cyl(4.05,15,(*f['center'],-5))
        a=old.intersect(zone);b=new.intersect(zone)
        changes=[pair(s,zone,'FULL_BODY_CHANGE_REGION','FOOT_REGION',0.) for s in change_solids]
        feet.append(dict(center=f['center'],removed_mm3=difference_volume(a,b),added_mm3=difference_volume(b,a),
                         complete_change_region_checks=changes))
    row=dict(valid=new.isValid(),solids=len(new.Solids()),volume_mm3=vol(new),removed_mm3=removed,added_mm3=added,
             comparison_reference='analysis_reference/BODY_C18_BEFORE_C19.step',
             unchanged_below_z_mm=5.1,lower_region_removed_mm3=low_removed,lower_region_added_mm3=low_added,
             low_band_old_solids=len(before.Solids()),low_band_new_solids=len(after.Solids()),
             complete_body_change_regions=change_regions,low_band_clear_of_complete_changes=low_region_clear,
             feet=feet,middle_raw=check,middle_functional_contact=contact,
             scope='Source rebuilt middle-seat tie leveling and terminal-clearance slots. Five foot regions and bottom low band compared explicitly. Full G1-G11 verification must follow.')
    save('BODY_C19.json',row);print(row,flush=True)
    assert row['valid'] and row['solids']==1 and added<=.001
    assert low_removed<=.001 and low_added<=.001 and low_region_clear and check['overlap_mm3']<=.001 and contact['passed']
    assert len(feet)==5 and all(f['removed_mm3']<=.001 and f['added_mm3']<=.001 and all(x['overlap_mm3']<=.001 for x in f['complete_change_region_checks']) for f in feet)

if __name__=='__main__':main()
