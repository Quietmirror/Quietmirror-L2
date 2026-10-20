"""Exact checks of the actual candidate; failures are data, never a release pass.

The gate aggregation runs only after any reported exceptions have been resolved.
This intentionally keeps the full-body distances, including functional contacts,
visible rather than silently treating every BODY/lever pair as an exception.
"""
import itertools,json,math,time
import numpy as np
import trimesh
from common import *
from exact_distance import pair
from side_module import KEYS,RETAINER_MOUNTS,UPPER_LUG_TOP

def main():
    parts={p.stem:load(p.stem) for p in sorted((OUT/'parts').glob('*.step'))}
    body=parts['BODY'];rows=[]
    for n,s in parts.items():
        from OCP.BRepAlgoAPI import BRepAlgoAPI_Check
        m=trimesh.load_mesh(OUT/'parts'/(n+'.stl'))
        rows.append(dict(name=n,valid=s.isValid(),solids=len(s.Solids()),
            volume_mm3=vol(s),bounds_mm=bounds(s),closed_mesh=bool(m.is_watertight),
            consistent_winding=bool(m.is_winding_consistent),mesh_components=len(trimesh.graph.connected_components(m.face_adjacency,nodes=np.arange(len(m.faces)),engine='scipy',min_len=1)),
            brep_self_interference_check=bool(BRepAlgoAPI_Check(s.wrapped,True,True).IsValid())))
        print('SOLID',rows[-1],flush=True);save('solids.json',rows)
    feet=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text())['mechanisms']['feet']
    footrows=[]
    for f in feet:
        x,y=f['center'];area=0.;zs=[]
        for face in body.Faces():
            if face.geomType()!='PLANE':continue
            bb=face.BoundingBox()
            if bb.zlen<1e-5 and abs(bb.zmin-5.2)<1e-5 and face.normalAt().z<-.9:
                hit=face.intersect(cyl(4.01,.2,(x,y,5.1)))
                if hit.Area()>1e-7:area+=hit.Area();zs.append(bb.zmin)
        footrows.append(dict(x=x,y=y,z=zs,contact_area_mm2=area,passed=area>40 and all(abs(z-5.2)<1e-5 for z in zs)))
    save('foot_planes.json',dict(feet=footrows,coplanar=all(r['passed'] for r in footrows),glue_z=5.2,skates_mm=.8,ground_z=4.4))

if __name__=='__main__':main()
