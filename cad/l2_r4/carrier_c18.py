"""Export only the changed carrier from its original parameterized operations."""
from common import *
from wheel_clearance_finish import carrier_geometry

def main():
    before=load('WHEEL_CARRIER')
    after=carrier_geometry()
    added=vol(after.cut(before))
    assert added<=.001, 'The relief may only remove material'
    removed=vol(before.cut(after))
    row=export(after,'WHEEL_CARRIER')
    save('carrier_C18.json',dict(part=row,removed_mm3=removed,added_mm3=added,
        failed_previous_pose_deg=4.4,failed_previous_gap_mm=.22742873385069018,
        underside_strip_y_mm=[34.2,36.2],floor_bottom_z_mm=10.6,floor_top_z_mm=12.2,
        nominal_floor_thickness_mm=1.6,body_changed=False,
        scope='Source generator refines only carrier underside; full affected checks and slicing remain mandatory.'))

if __name__=='__main__':main()
