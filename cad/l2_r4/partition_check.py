"""Conservation check for explicit functional-contact Boolean partitions.

Unlike a performance crop, these masks define named contact exclusions.
Full original-solid overlap is still checked separately at every pose.
"""
from common import vol,bounds

def subtract(shape,mask,label):
    rest=shape.cut(mask);removed=shape.intersect(mask)
    before=vol(shape);kept=vol(rest);taken=vol(removed);error=abs(before-kept-taken)
    # Curved-surface integration can vary after face splitting even with
    # exactly empty geometric differences. Check material loss/addition
    # directly instead of mistaking an integration discrepancy for a gap.
    combined=rest.fuse(removed)
    lost=shape.cut(combined);added=combined.cut(shape)
    lost_volume=vol(lost);added_volume=vol(added)
    okay=rest.isValid() and removed.isValid() and combined.isValid() and lost_volume<=.001 and added_volume<=.001
    row=dict(feature=label,original_volume_mm3=before,remaining_volume_mm3=kept,removed_volume_mm3=taken,
        volume_partition_error_mm3=error,lost_material_mm3=lost_volume,added_material_mm3=added_volume,
        lost_solid_count=len(lost.Solids()),added_solid_count=len(added.Solids()),mask_bounds_mm=bounds(mask),passed=bool(okay),
        scope='BRep validity and direct geometric differences of recombined functional partitions; adaptive integration discrepancy retained separately. Full original overlap is required separately.')
    if not okay:raise RuntimeError('Functional Boolean partition failed: '+str(row))
    return rest,row
