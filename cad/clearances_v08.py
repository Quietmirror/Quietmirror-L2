"""Separate, non-printable service/optical/RF/wiring reservations."""
from pathlib import Path
import json
import cadquery as cq
from electronics_v06 import geometry,write_mesh
from validate_v08 import overlap
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'exports/v08';RP=ROOT/'reports/v08'
for variant in ('ATK_A1_PLUS','PAW3950_CUSTOM'):
    physical=json.loads((RP/(variant+'_layout.json')).read_text())['physical']
    shapes={e['name']:cq.importers.importStep(str(OUT/variant/(e['name']+'.step'))).val() for e in physical}
    entries=[
      dict(name='battery_service_EST',kind='reserve',size=[21,25,7],center=[5,-55,15.5]),
      dict(name='antenna_clearance_EST',kind='reserve',size=[18,10,4.5],center=[0,-62,9.25] if variant=='ATK_A1_PLUS' else [0,-72,10.35]),
      dict(name='optical_path_EST',kind='reserve',size=[7,10,7],center=[0,-48,2.8]),
      dict(name='USB_plug_EST',kind='reserve',size=[12,20,5.6],center=[0,8,7.1]),
      dict(name='left_wire_corridor_EST',kind='reserve',size=[2.4,30,2],center=[-22,-43,6.5]),
      dict(name='right_wire_corridor_EST',kind='reserve',size=[2.4,30,2],center=[22,-43,6.5]),
    ]
    assy=cq.Assembly(name=variant+'_RESERVATIONS_NOT_PRINT_PARTS');rows=[]
    for e in entries:
        s=geometry(e);assy.add(s,name=e['name'],color=cq.Color(.65,.35,.75,.3));write_mesh(s,OUT/variant/(e['name']+'.stl'))
        hits=[dict(part=n,volume_mm3=v) for n,a in shapes.items() if (v:=overlap(s,a))>.01]
        rows.append(dict(**e,component_hits=hits))
    assy.save(str(OUT/f'quietmirror_V0.8_{variant}_CLEARANCES.step'))
    (RP/(variant+'_clearances.json')).write_text(json.dumps(dict(variant=variant,reservations=rows,note='All estimated. Battery service volume intentionally contains the battery; optical volume may contain lens. Wire boxes are unvalidated routing corridors, not actual cables. Antenna volumes are conceptual non-metal space, not RF validation. Real parts, final mounting and routing must be measured. Moving-part vs electronics checks are in the corresponding layout.json.'),indent=2),encoding='utf8')
