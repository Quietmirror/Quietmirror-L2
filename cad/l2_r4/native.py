"""Save and reopen a native FreeCAD component assembly (no GUI, no solved joints)."""
from pathlib import Path
import json,os
import FreeCAD as App
import Part
ROOT=Path(os.environ['QUIETMIRROR_ROOT']);OUT=ROOT/'models/L2_r4';RP=ROOT/'reports/l2_r4'
inventory=json.loads((RP/'assembly_inventory.json').read_text())
doc=App.newDocument('Quietmirror_L2_r4_H')
printed=doc.addObject('App::DocumentObjectGroup','PrintedParts')
hardware=doc.addObject('App::DocumentObjectGroup','ReferenceHardware')
for group,names,folder in [(printed,inventory['printable'],'parts'),(hardware,inventory['H_hardware'],'reference')]:
    for name in names:
        shape=Part.Shape();shape.read(str(OUT/folder/(name+'.step')))
        obj=doc.addObject('Part::Feature',name);obj.Label=name;obj.Shape=shape
        obj.addProperty('App::PropertyString','EvidenceStatus');obj.EvidenceStatus='Printable geometry' if group==printed else 'Reference envelope; real component fit unverified'
        group.addObject(obj)
info=doc.addObject('App::FeaturePython','DesignStatus')
for key,value in {'ReleaseStatus':'CAD status: see handoff/l2_r4/GATES.md; physical tests HARDWARE_PENDING','Source':'cad/l2_r4/*.py and reports/l2_r4/parameters_implemented.json','Units':'mm','Editing':'Named imported B-reps; editable generator source supplied separately; no solved Assembly joints.','Donor':'ATK A1 Plus unconfirmed; H electronics are estimated packages.'}.items():
    info.addProperty('App::PropertyString',key);setattr(info,key,value)
doc.recompute();path=OUT/'FULL_ASSEMBLY_H.FCStd';doc.saveAs(str(path));App.closeDocument(doc.Name)
re=App.openDocument(str(path));rows=[]
for obj in re.Objects:
    if obj.isDerivedFrom('Part::Feature') and hasattr(obj,'Shape') and not obj.Shape.isNull():rows.append(dict(name=obj.Name,valid=obj.Shape.isValid(),solids=len(obj.Shape.Solids)))
App.closeDocument(re.Name)
full=Part.Shape();full.read(str(OUT/'FULL_ASSEMBLY_H.step'))
stepcheck=dict(solids=len(full.Solids),valid=full.isValid(),expected_components=inventory['independent_components'])
assert len(rows)==inventory['independent_components']>=89
assert stepcheck['valid'] and stepcheck['solids']==len(rows)
assert all(x['valid'] and x['solids']==1 for x in rows)
(RP/'native_roundtrip.json').write_text(json.dumps(dict(application='FreeCAD '+'.'.join(App.Version()[:3]),parts=rows,all_valid=all(x['valid'] and x['solids']==1 for x in rows),full_step_roundtrip=stepcheck,scope='Saved/reopened imported components, not constrained feature history'),indent=2))
print('Native assembly reopened',len(rows),'components',flush=True)
