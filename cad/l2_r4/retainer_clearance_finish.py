"""Regenerate only the two retainers after exact static clearance findings."""
from common import *
from side_module import retainer
def main():
    rows=[export(retainer(n),n+'_RETAINER') for n in ['SF','SR']]
    save('retainer_clearance_changes.json',dict(parts=rows,terminal_slot_y_halfwidth_mm=.97,terminal_slot_z_mm=[15.6,17.35],sr_front_lip_xmax_mm=18.65,sr_front_lip_ymax_mm=56.05,body_changed=False,scope='Source corrections; G1/G2/G5/G6/S7 and final slices must be rechecked.'))
if __name__=='__main__':main()
