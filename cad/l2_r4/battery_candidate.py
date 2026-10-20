"""Build the explicitly selected, independently tested cell-envelope revision.

The larger inherited service reservation and the connector position are kept.
This does not select a purchasable cell or infer capacity from package volume.
"""
import json
import numpy as np
from common import *

def main():
    cfg=json.loads((HERE/'battery_selection.json').read_text())
    assert cfg['candidate_exact_path_passed'] and cfg['proposal_source_commit']
    c=np.array(cfg['center_mm']);h=np.array(cfg['dimensions_mm'])/2
    cell=box(c[0]-h[0],c[0]+h[0],c[1]-h[1],c[1]+h[1],c[2]-h[2],c[2]+h[2])
    row=export(cell,'BATTERY_CELL_EST',False)
    save('battery_envelope_revision.json',dict(selection=cfg,part=row,
        previous_dimensions_mm=[18,22,6],previous_volume_mm3=2376,
        volume_fraction=row['volume_mm3']/2376,
        unchanged=['BODY','printed parts','BATTERY_SERVICE_EST 19x23x7','BATTERY_PLUG_EST','existing wire routes'],
        limitation='Estimated envelope only. A supplier cell, lead exit, retention, capacity and12h endurance still require the specified hardware measurements. Final current-component service replay is mandatory.'))

if __name__=='__main__':main()
