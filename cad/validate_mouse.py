"""Independent saved-file QA. Geometry checks do not replace a physical print."""
from pathlib import Path
import json, math
import numpy as np
import trimesh, pymeshlab, cadquery as cq
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box
ROOT=Path(__file__).resolve().parents[1]

def ray_distances(mesh,origins,directions):
    loc,idx,_=mesh.ray.intersects_location(np.asarray(origins),np.asarray(directions),multiple_hits=True)
    result=[]
    for i,(o,d) in enumerate(zip(origins,directions)):
        ts=np.dot(loc[idx==i]-o,d)
        ts=np.unique(np.round(ts[ts>1e-5],6)); result.append(ts.tolist())
    return result

def main():
    p=json.loads((ROOT/'cad/parameters.json').read_text())
    m=trimesh.load_mesh(ROOT/'exports/quietmirror_fingertip_V0.1.stl')
    s=cq.importers.importStep(str(ROOT/'exports/quietmirror_fingertip_V0.1.step')).val()
    b=Bnd_Box();BRepBndLib.AddOptimal_s(s.wrapped,b,False,False);bounds=np.array(b.Get()).reshape(2,3)
    ms=pymeshlab.MeshSet();ms.load_new_mesh(str(ROOT/'exports/quietmirror_fingertip_V0.1.stl'))
    ms.compute_selection_by_self_intersections_per_face()
    self_count=ms.current_mesh().selected_face_number(); topo=ms.get_topological_measures()
    # Contact fields: rays follow the analytic normals from outside to inside.
    origins=[]; directions=[]; labels=[]
    for name in ('left_key','right_key'):
        k=p[name];r=k['curvature_radius'];z=p['height']+k['height_offset']
        for dx in (-5,0,5):
            for dy in (-10,-5,0,5,10):
                q=math.sqrt(r*r-dx*dx-dy*dy)
                normal=np.array([dx,dy,q])/r; pt=np.array([k['x']+dx,k['y']+dy,z-r+q])
                origins.append(pt+normal*.05);directions.append(-normal);labels.append(name)
    for side,name in ((-1,'thumb_contact'),(1,'right_contact')):
        k=p[name];r=k['curvature_radius']
        for dy in (-10,-5,0,5,10):
            for dz in (-3,0,3):
                q=math.sqrt(r*r-dy*dy-dz*dz)
                normal=np.array([-side*q,dy,dz])/r
                pt=np.array([side*(p['grip_width']/2+r-q),k['y']+dy,k['z']+dz])
                origins.append(pt-normal*.05);directions.append(normal);labels.append(name)
    # JSON y counts rearward from the nose; exported CAD Y points forward.
    origins=np.asarray(origins)*[1,-1,1];directions=np.asarray(directions)*[1,-1,1]
    depths=ray_distances(m,origins,directions);wall=[]
    for label,o,ts in zip(labels,origins,depths):
        wall.append(dict(field=label,origin_mm=list(o),thickness_mm=round(ts[1]-ts[0],5) if len(ts)>1 else None))
    # Test a center and 8 points on each usable adhesive disk (r=3.7 < 3.75).
    cad_metrics=json.loads((ROOT/'reports/cad_metrics.json').read_text())
    foot_checks=[]
    for foot in cad_metrics['feet']:
        pts=[(foot['x'],foot['y'])]+[(foot['x']+3.7*math.cos(t),foot['y']+3.7*math.sin(t)) for t in np.linspace(0,2*math.pi,8,endpoint=False)]
        hits=ray_distances(m,[[x,y,-1] for x,y in pts],[[0,0,1]]*len(pts))
        zs=[h[0]-1 for h in hits if h]
        foot_checks.append(dict(id=foot['id'],center_xy_mm=[foot['x'],foot['y']],sample_count=len(zs),bottom_z_range_mm=[min(zs),max(zs)]))
    # Bottom open fraction in a horizontal layer just above the adhesive plane.
    section=m.section(plane_origin=[0,0,.2],plane_normal=[0,0,1])
    planar,_=section.to_2D();filled_area=sum(poly.area for poly in planar.polygons_full)
    from shapely.geometry import MultiPoint
    hull_area=MultiPoint(m.vertices[:,:2]).convex_hull.area
    # Enumerate bounding-box envelope interactions separately from shell hits.
    er=json.loads((ROOT/'reports/envelope_interferences.json').read_text())
    pairs=[]
    for i,a in enumerate(er['envelopes']):
        ac=np.array(a['center']);ad=np.array(a['size'])/2
        for b in er['envelopes'][i+1:]:
            bc=np.array(b['center']);bd=np.array(b['size'])/2
            overlap=np.minimum(ac+ad,bc+bd)-np.maximum(ac-ad,bc-bd)
            if np.all(overlap>1e-6):pairs.append(dict(a=a['name'],b=b['name'],overlap_mm3=round(float(np.prod(overlap)),3)))
    values=[v['thickness_mm'] for v in wall if v['thickness_mm'] is not None]
    result=dict(units='mm',step=dict(valid=s.isValid(),solids=len(s.Solids()),dimensions_xyz_mm=(bounds[1]-bounds[0]).tolist(),volume_mm3=s.Volume()),mesh=dict(dimensions_xyz_mm=m.extents.tolist(),faces=len(m.faces),vertices=len(m.vertices),watertight=m.is_watertight,winding_consistent=m.is_winding_consistent,connected_components=len(m.split(only_watertight=False)),self_intersecting_faces=self_count,volume_mm3=m.volume,topology=topo),wall_check=dict(method='60 normal-ray samples across four contact fields; analytic field wall is 1.8 mm; not a continuous global medial-axis proof',nominal_field_mm=p['wall'],rounded_rim_mm=p['contact_rim_thickness'],samples=wall,min_mm=min(values),max_mm=max(values)),feet=foot_checks,base_section=dict(z_mm=.2,solid_section_area_mm2=filled_area,xy_convex_hull_area_mm2=hull_area,open_area_fraction=1-filled_area/hull_area),envelope_pairs=pairs)
    (ROOT/'reports/validation.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf8')
    assert s.isValid() and len(s.Solids())==1
    assert m.is_watertight and m.is_winding_consistent and self_count==0 and topo['connected_components_number']==1
    assert len(values)==60 and min(values)>1.72
    assert all(f['sample_count']==9 and max(abs(z) for z in f['bottom_z_range_mm'])<.01 for f in foot_checks)
    print(json.dumps({k:v for k,v in result.items() if k not in ('wall_check','envelope_pairs')},indent=2))
    print('Contact normal thickness range',min(values),max(values),'from',len(values),'samples')
    print('Envelope pairs',pairs)

if __name__=='__main__':main()
