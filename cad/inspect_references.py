"""Read upstream meshes/SCAD/KiCad, record dimensions without reusing geometry."""
from pathlib import Path
import json,re,subprocess
import numpy as np
import trimesh
ROOT=Path(__file__).resolve().parents[1]
def sexp(text):
    tokens=re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',text)
    stack=[];root=None
    for t in tokens:
        if t=='(':
            x=[]
            if stack:stack[-1].append(x)
            else:root=x
            stack.append(x)
        elif t==')':stack.pop()
        else:stack[-1].append(t.strip('"'))
    return root
def child(x,name):return next((i for i in x[1:] if isinstance(i,list) and i and i[0]==name),None)
files=['olliebella/STLs/base.stl','olliebella/STLs/shell.stl','olliebella/STLs/shell (thumb rest).stl','olliebella/STLs/shell (pinky rest).stl','olliebella/STLs/m1.stl','olliebella/STLs/m2.stl','olliebella/STLs/wheel.stl','olliebella/STLs/lens U mount.stl','olliebella/STLs/rear skake.stl','Kotinos/STL/Kotinos.stl','Kotinos/STL/IndexPaddle.stl','Kotinos/STL/MiddlePaddle.stl']
data=[]
for f in files:
    m=trimesh.load_mesh(ROOT/'.reference'/f)
    data.append(dict(file=f,dimensions_mm=m.extents.tolist(),bounds_mm=m.bounds.tolist(),vertices=len(m.vertices),faces=len(m.faces),watertight=bool(m.is_watertight)))
pcb=sexp((ROOT/'.reference/paw3395-pcb/paw3395.kicad_pcb').read_text())
edges=[]; footprints=[]
for element in pcb[1:]:
    if not isinstance(element,list):continue
    lay=child(element,'layer')
    if element[0].startswith('gr_') and lay and lay[1]=='Edge.Cuts':edges.append(element)
    if element[0]=='footprint':
        ref=next((i[2] for i in element if isinstance(i,list) and len(i)>2 and i[0]=='property' and i[1]=='Reference'),'?')
        if 'PAW' in element[1] or ref=='U2':footprints.append(dict(name=element[1],reference=ref,at=child(element,'at')))
out=dict(meshes=data,pcb_edge_cuts=edges,sensor_footprints=footprints)
(ROOT/'reports/reference_geometry.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps(out,indent=2))
