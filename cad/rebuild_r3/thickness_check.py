"""Finite wall-thickness and volume audit on the delivered files, not a global proof."""
from pathlib import Path
import ctypes, hashlib, json
import numpy as np
import trimesh
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps

ROOT=Path(__file__).resolve().parents[2]
RP=ROOT/'reports/rebuild_r3'
OUT=ROOT/'exports/rebuild_r3/assembly'

def main():
    try:ctypes.windll.kernel32.SetPriorityClass(ctypes.c_void_p(-1),0x4000)
    except Exception:pass
    metrics=json.loads((RP/'cad_metrics.json').read_text(encoding='utf8'))
    rows=[]
    for name,v in metrics.items():
        if not v['printable']:continue
        path=OUT/f'{name}.stl';mesh=trimesh.load_mesh(path)
        step=cq.importers.importStep(str(OUT/f'{name}.step')).val()
        prop=GProp_GProps()
        err=BRepGProp.VolumeProperties_s(step.wrapped,prop,1e-7,True,False)
        points,faces=trimesh.sample.sample_surface(mesh,5000 if name=='BODY' else 1000,seed=123)
        normals=mesh.face_normals[faces]
        # Shift inside the source triangle; take the first exit from that solid.
        locations,rayids,triids=mesh.ray.intersects_location(points-normals*1e-4,-normals,multiple_hits=False)
        lengths=np.linalg.norm(locations-points[rayids],axis=1)
        opposing=np.einsum('ij,ij->i',normals[rayids],mesh.face_normals[triids])<-.85
        good=np.where(opposing & (lengths>.01))[0]
        order=good[np.argsort(lengths[good])]
        samples=[dict(thickness_mm=float(lengths[k]),point=points[rayids[k]].tolist(),normal=normals[rayids[k]].tolist()) for k in order[:20]]
        row=dict(part=name,stl_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                 adaptive_cad_volume_mm3=prop.Mass(),adaptive_integrator_reported_error=err,
                 mesh_volume_mm3=float(mesh.volume),mesh_vs_adaptive_cad_relative_difference=abs(mesh.volume/prop.Mass()-1),
                 seed=123,sampled_surface_points=len(points),opposing_face_samples=len(good),
                 normal_chord_percentiles_mm={str(q):float(np.percentile(lengths[good],q)) for q in (0,1,5,50)},
                 twenty_shortest_opposing_chords=samples)
        rows.append(row)
        print(name,'CAD',round(prop.Mass(),3),'mesh',round(mesh.volume,3),'chords',row['normal_chord_percentiles_mm'],flush=True)
    result=dict(parts=rows,scope='Area-weighted reproducible STL inward-normal rays, opposite exit normal dot <-0.85. Finite samples include edge tapers, fillets, hole rims and intentional shaft flats; this is not a certified global minimum or a blanket 1.6 mm wall pass. Exact critical-feature dimensions are documented separately. Adaptive CAD quadrature is used because default volume integration differs on the trimmed BSpline body.',
                ordinary_wall_global_minimum_certified=False,
                total_adaptive_cad_volume_mm3=sum(r['adaptive_cad_volume_mm3'] for r in rows),
                total_mesh_volume_mm3=sum(r['mesh_volume_mm3'] for r in rows))
    (RP/'thickness_volume_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')

if __name__=='__main__':main()
