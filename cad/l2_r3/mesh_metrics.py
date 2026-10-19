"""Mesh units, signed volume and CAD-volume agreement; not physical tests."""
import json
import trimesh
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];RP=ROOT/'reports/l2_r3';rows=[]
for r in json.loads((RP/'solids.json').read_text()):
    m=trimesh.load_mesh(ROOT/'models/L2_r3/parts'/(r['name']+'.stl'))
    rows.append(dict(part=r['name'],positive_mesh_volume=bool(m.volume>0),mesh_volume_mm3=float(m.volume),adaptive_CAD_volume_mm3=r['volume_mm3'],difference_percent=100*(float(m.volume)/r['volume_mm3']-1),size_mm=m.extents.tolist(),unit='mm from generator; STL has no intrinsic unit metadata',closed=bool(m.is_watertight),components=len(m.split())))
(RP/'mesh_units_and_volume.json').write_text(json.dumps(rows,indent=2));print(rows)
