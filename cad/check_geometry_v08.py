"""Mesh mirror, normal-wall samples and planar feature audit; no FEA claim."""
from pathlib import Path
import json
import numpy as np
import cadquery as cq
import trimesh
from shapely.geometry import Polygon,Point,box
from validate_mouse import ray_distances
ROOT=Path(__file__).resolve().parents[1];RP=ROOT/'reports/v08';out=ROOT/'exports/v08/placed'
def main():
    p=json.loads((ROOT/'cad/parameters_v08.json').read_text(encoding='utf8'));l=json.loads((RP/'vent_layout.json').read_text());m=trimesh.load_mesh(out/'BODY.stl')
    outer=cq.importers.importStep(str(ROOT/'.tools/v08_outer.step')).val();outer.exportStl(str(ROOT/'.tools/v08_outer.stl'),tolerance=.02,angularTolerance=.15,relative=False);om=trimesh.load_mesh(ROOT/'.tools/v08_outer.stl')
    pts,idx=trimesh.sample.sample_surface(om,6500,seed=7015);nn=om.face_normals[idx]
    vents=[Polygon([(x,-d) for x,d in h['rounded_xd_mm']]) for h in l['holes']]+[Polygon([(x,-d) for x,d in h['xd_mm']]) for h in l['front_holes']]
    exclusions=[a.buffer(2.4) for a in vents]+[box(-10,-44,10,-4)]
    for n in ('left_key','right_key'):
        k=p[n];exclusions.append(box(k['x']-k['width']/2,-k['y']-k['length']/2,k['x']+k['width']/2,-k['y']+k['length']/2).buffer(2.4))
    keep=(pts[:,2]>8)&(pts[:,1]<-4)&(pts[:,1]>-80)
    for i,pt in enumerate(pts):
        if any(q.contains(Point(pt[0],pt[1])) for q in exclusions):keep[i]=False
        if pt[0]<-18 and -64<pt[1]<-30 and pt[2]>10:keep[i]=False
    pts=pts[keep];nn=nn[keep];hits=ray_distances(m,pts+nn*.1,-nn);samples=[]
    for point,n,hh in zip(pts,nn,hits):
        if len(hh)>=2 and .02<hh[0]<.2:samples.append(dict(point_mm=point.tolist(),normal=n.tolist(),thickness_mm=hh[1]-hh[0]))
    values=[a['thickness_mm'] for a in samples]
    pp,_=trimesh.sample.sample_surface(m,8000,seed=7016);mask=~((np.abs(pp[:,0])>7)&(pp[:,1]<-27)&(pp[:,1]>-61)&(pp[:,2]>5.4));pp=pp[mask];mir=pp.copy();mir[:,0]*=-1
    _,dd,_=trimesh.proximity.closest_point(m,mir)
    left=trimesh.load_mesh(out/'left_KEY.stl');right=trimesh.load_mesh(out/'right_KEY.stl');kp,_=trimesh.sample.sample_surface(left,2000,seed=7017);kp[:,0]*=-1;_,kd,_=trimesh.proximity.closest_point(right,kp)
    result=dict(version='0.8',normal_wall=dict(count=len(samples),minimum_mm=min(values),percentiles_mm=np.percentile(values,[1,5,50,95,99]).tolist(),samples=samples,method='Original outer-surface facet-normal chords on final BODY; omit openings plus 2.4 mm neighbourhood, end rims and side-button transitions. Finite samples, not a global minimum wall proof.'),symmetry=dict(body_samples=len(dd),body_max_mirror_distance_mm=float(dd.max()),main_key_samples=len(kd),main_key_max_mirror_distance_mm=float(kd.max()),excluded_region='Side keys and their internal guide/fastening region: |X|>7, D29..64, Z>5.4 mm. Both sides excluded only for comparison.'),feature_dimensions=dict(skin_nominal_mm=1.8,tray_floor_and_retainer_mm=1.6,main_stem_xy_mm=[5.6,7.6],side_stem_xy_mm=[3.2,7.6],wheel_fork_diameter_mm=2.4,load_beams_mm=2.8,replaceable_leaf_mm=.8,axle_mm=3,main_face_plan_corner_mm=3,main_face_edge_fillet_mm=.4,side_face_edge_fillet_mm=.4),holes=dict(rear_profiles=len(l['holes']),front_profiles=len(l['front_holes']),separate_carrier_install_opening_xy_mm=[14.2,34],count_note='Counts are cutter profiles, not a claim that all openings remain disconnected; the carrier opening joins the wheel/key installation apertures. Functional mounting regions have wider members.'),limits='No stress, fatigue, bending or physical fit verification. Thin intentional spring and countersink features excluded from ordinary shell-wall statistic.')
    result['symmetry']['excluded_region']='Side keys and their internal guide roots: |X|>7, D27..61, Z>5.4 mm; both sides excluded for comparison.'
    result['feature_dimensions'].update(main_face_plan_corner_mm=2.5,main_face_edge_fillet_mm=.45,side_face_edge_fillet_mm=.3,side_face_protrusion_mm=.35,axle_pilot_radial_wall_mm=.65,washer_radial_wall_mm=.8,retainer_countersink_local_remainder_mm=.55,detent_default_gap_mm=.05)
    (RP/'geometry_checks.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print('Wall samples/min',len(values),min(values),'body mirror max',dd.max(),'key mirror max',kd.max(),flush=True)
    assert len(values)>250 and min(values)>1.58 and dd.max()<.06 and kd.max()<.06
if __name__=='__main__':main()
