"""Compact STEP export and source BRep tessellation; saved outputs validated."""
from pathlib import Path
import cadquery as cq
import trimesh
from build_v03 import bounds
ROOT=Path(__file__).resolve().parents[1]

def export_step(shape,path,write_pcurves=True):
    return shape.exportStep(str(path),write_pcurves=write_pcurves)

def save_model(shape,stem,out):
    assert shape.isValid() and len(shape.Solids())==1
    export_step(shape,out/(stem+'.step'),write_pcurves=False)
    s=cq.importers.importStep(str(out/(stem+'.step'))).val()
    raw=ROOT/'.tools'/('raw_'+stem+'.stl')
    mesh_source=shape if stem=='BODY' else s
    if stem=='BODY':shape.exportBrep(str(ROOT/'.tools/v09_final_BODY.brep'))
    mesh_source.exportStl(str(raw),tolerance=.02,angularTolerance=.15,relative=False,parallel=False)
    m=trimesh.load_mesh(raw);raw_faces=len(m.faces)
    m.merge_vertices(digits_vertex=6);m.update_faces(m.nondegenerate_faces(height=1e-7))
    m.update_faces(m.unique_faces());m.remove_unreferenced_vertices()
    m.export(out/(stem+'.stl'))
    assert m.is_watertight and len(m.split(only_watertight=False))==1,stem
    bb=bounds(s)
    return dict(name=stem,dimensions_xyz_mm=[bb[i+3]-bb[i] for i in range(3)],bounds=[list(bb[:3]),list(bb[3:])],volume_mm3=s.Volume(tol=1e-3),volume_integration_tolerance=1e-3,cad_valid=s.isValid(),cad_solids=len(s.Solids()),mesh_cleanup=dict(source='source BRep' if stem=='BODY' else 'STEP reimport',raw_faces=raw_faces,final_faces=len(m.faces),weld_tolerance_mm=1e-6,holes_patched=0,components_discarded=0))
