"""Export only the revised estimated PCB; all other saved parts retained."""
from common import *
from wheel_clearance_finish import encoder_pcb
if __name__=='__main__':
    row=export(encoder_pcb(),'ENCODER_ADAPTER_PCB_EST',False)
    save('encoder_pcb_C17.json',dict(part=row,revision='C17 planar rearY34.55, tapered forward diagonal retaining rear lug land',actual_vendor_board=False))
