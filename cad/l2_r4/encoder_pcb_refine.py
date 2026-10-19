"""Export only the revised estimated PCB; all other saved parts retained."""
from common import *
from wheel_clearance_finish import encoder_pcb
if __name__=='__main__':
    row=export(encoder_pcb(),'ENCODER_ADAPTER_PCB_EST',False)
    save('encoder_pcb_C16.json',dict(part=row,revision='C16 planar rearY34.55 and diagonal edge',actual_vendor_board=False))
