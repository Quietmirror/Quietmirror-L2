"""Replay the selected path against actual final independent STEP components."""
import json,math,time
import numpy as np
from common import *
from bounded_scene import scene_pairs
from battery_service_rrt import moved

def dense(a,b):
    count=max(1,int(math.ceil(np.linalg.norm(b[:3]-a[:3])/.25)),int(math.ceil(np.max(np.abs(b[3:]-a[3:]))/2.5)))
    return [a+(b-a)*t for t in np.linspace(0,1,count+1)]

def main():
    began=time.time();cfg=json.loads((HERE/'battery_selection.json').read_text())
    assert cfg['candidate_exact_path_passed']
    battery=load('BATTERY_CELL_EST',OUT/'reference');pivot=np.array(cfg['center_mm'])
    actual=bounds(battery);sizes=np.array(actual[3:])-np.array(actual[:3])
    assert np.max(np.abs(sizes-np.array(cfg['dimensions_mm'])))<1e-5
    assert np.linalg.norm(np.array(battery.Center().toTuple())-pivot)<1e-5
    fixed={n:load(n) for n in ['BODY','SF_RETAINER','SR_RETAINER','SIDE_FRONT_KEY','SIDE_REAR_KEY']}
    fixed.update({n:load(n,OUT/'reference') for n in ['SF_D2F_01F','SR_D2F_01F','SF_VERTICAL_PIN','SR_VERTICAL_PIN','SF_RETAINER_M2x5','SR_RETAINER_M2x5']})
    route=[np.array(p,float) for p in cfg['extraction_route']];assert np.max(np.abs(route[0]))<1e-8
    replay=[]
    for a,b in zip(route[:-1],route[1:]):replay.extend(dense(a,b))
    last=moved(battery,pivot,replay[-1]);external=last.BoundingBox().zmax<fixed['BODY'].BoundingBox().zmin-.5
    rows=[];report=dict(battery_estimated_size_mm=cfg['dimensions_mm'],pivot_mm=pivot.tolist(),retained_obstacles=list(fixed),
        route=[p.tolist() for p in route],route_direction='Final bay to exterior below; reverse for insertion',
        translation_step_mm=.25,maximum_Euler_component_step_deg=2.5,replay_poses=len(replay),external_endpoint=external,passed=False,
        service_sequence=['Disconnect the estimated battery connector using the checked front2mm tool profile',
            'Remove main keys and removable wheel carrier assembly',
            'Remove screwed H electronic modules and free flexible wires and actual battery retention',
            'Follow the saved rigid extraction path toward the bottom; retain the integral BODY and both side modules',
            'Reverse the route to insert the battery, then restore wiring, retention and removable modules'],
        scope='Exact BRep distances at every stated finite pose, not continuous swept-volume or physical handling proof. No cell bending permitted.')
    for i,p in enumerate(replay):
        result=scene_pairs(moved(battery,pivot,p),fixed,'BATTERY_CELL_EST',.5)
        rows.append(dict(pose_index=i,pose=p.tolist(),**result))
        print('FINAL_CELL_POSE',i,len(replay),result['exact_global_minimum_mm'],result['passed'],flush=True)
        if not result['passed']:break
    report.update(exact_all_poses=rows,minimum_exact_clearance_mm=min(r['exact_global_minimum_mm'] for r in rows),
        passed=external and len(rows)==len(replay) and all(r['passed'] for r in rows),elapsed_s=time.time()-began)
    save('battery_service_path.json',report)
    if not report['passed']:raise RuntimeError('Final current-cell service path failed exact0.5mm requirement')

if __name__=='__main__':main()
