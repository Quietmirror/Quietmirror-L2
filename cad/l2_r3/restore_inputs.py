"""FreeCADCmd: restore missing named R3.2 inputs without altering history."""
from pathlib import Path
import os,json
import FreeCAD as App
ROOT=Path(os.environ.get('QUIETMIRROR_ROOT',Path(__file__).resolve().parents[2]))
source=ROOT/'models/L2_r3/inputs/R32_BASELINE.FCStd'
target=ROOT/'exports/rebuild_r3_2/assembly';target.mkdir(parents=True,exist_ok=True)
doc=App.openDocument(str(source));rows=[]
for obj in doc.Objects:
    if not hasattr(obj,'Shape') or obj.Shape.isNull():continue
    path=target/(obj.Name+'.step')
    if not path.exists():obj.Shape.exportStep(str(path))
    rows.append(dict(part=obj.Name,valid=obj.Shape.isValid(),solids=len(obj.Shape.Solids),output=str(path.relative_to(ROOT))))
App.closeDocument(doc.Name)
print('Restoration checked',len(rows),'components; existing inputs left unchanged')
