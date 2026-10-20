"""Audit the source-rebuilt C19 BODY; build_body runs before this stage."""
from common import *
from exact_distance import pair
from contact_audit_final import mate
from boundary_preservation import compare, regression

def main():
    old=load('BODY_C18_BEFORE_C19',OUT/'analysis_reference')
    new=load('BODY')
    controls=regression()
    comparison,removed_shape,added_shape=compare(old,new,(-3.5,.65,37.,50.,5.1,9.3),WORK/'C19_boundary')
    removed=comparison['removed_mm3'];added=comparison['added_mm3']
    change_solids=[*removed_shape.Solids(),*added_shape.Solids()]
    change_regions=[dict(bounds_mm=bounds(s),volume_mm3=vol(s)) for s in change_solids]
    # All exterior boundary faces were compared; local BODY crops are used
    # only for change volume, never as a replacement in clearance checks.
    low_region_clear=all(s.BoundingBox().zmin>=5.1-1e-7 for s in change_solids)
    switch=load('SWITCH_MIDDLE',OUT/'reference')
    check=pair(new,switch,'BODY','SWITCH_MIDDLE',.5)
    feature=load('SWITCH_MIDDLE_MOUNT',OUT/'validation_features')
    contact=mate(switch,new,feature,'SWITCH_MIDDLE','BODY',.5,'original middle micro seat and bolt holders',check)
    feet=[]
    metadata=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text())
    for f in metadata['mechanisms']['feet']:
        zone=cyl(4.05,15,(*f['center'],-5))
        changes=[pair(s,zone,'FULL_BODY_CHANGE_REGION','FOOT_REGION',0.) for s in change_solids]
        feet.append(dict(center=f['center'],boundary_preserved_outside_correction_box=comparison['passed'],
                         complete_change_region_checks=changes))
    row=dict(valid=new.isValid(),solids=len(new.Solids()),volume_mm3=vol(new),removed_mm3=removed,added_mm3=added,
             comparison_reference='analysis_reference/BODY_C18_BEFORE_C19.step',
             unchanged_below_z_mm=5.1,boundary_comparison=comparison,regression_controls=controls,
             complete_body_change_regions=change_regions,low_band_clear_of_complete_changes=low_region_clear,
             feet=feet,middle_raw=check,middle_functional_contact=contact,
             scope='Source rebuilt middle-seat tie leveling and terminal-clearance slots. All exterior boundary faces compared outside the declared correction box; local differences and independent whole-solid volume balance checked. Direct full-coincident-solid Boolean failure retained in candidate history. Full G1-G11 verification must follow.')
    save('BODY_C19.json',row);print(row,flush=True)
    assert row['valid'] and row['solids']==1 and added<=.001
    assert comparison['passed'] and low_region_clear and check['overlap_mm3']<=.001 and contact['passed']
    assert len(feet)==5 and all(all(x['overlap_mm3']<=.001 for x in f['complete_change_region_checks']) for f in feet)

if __name__=='__main__':main()
