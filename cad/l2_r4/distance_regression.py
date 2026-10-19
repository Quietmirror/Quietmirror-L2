"""Regression for lost-geometry Boolean crops, using original solid distances."""
import json
import numpy as np
from common import *
from exact_distance import pair
from bounded_scene import scene_pairs
from battery_service_rrt import moved
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.Extrema import Extrema_ExtAlgo_Tree,Extrema_ExtFlag_MIN

def main():
    body=load('BODY');center=np.array([-17.,57.,16.4]);cell=box(-24,-10,47,67,13.4,19.4);rows=[]
    for p in json.loads((HERE/'distance_regression_cases.json').read_text()):
        actor=moved(cell,center,np.array(p['pose']))
        a=pair(actor,body,'CELL','BODY',.5)
        b=scene_pairs(actor,{'BODY':body},'CELL',.5)
        tree=BRepExtrema_DistShapeShape(actor.wrapped,body.wrapped,1e-7,Extrema_ExtFlag_MIN,Extrema_ExtAlgo_Tree)
        deltas=[abs(a['gap_mm']-p['full_original_mm']),abs(a['gap_mm']-tree.Value()),abs(a['gap_mm']-b['exact_global_minimum_mm'])]
        rows.append(dict(p,result=a,independent_tree_mm=tree.Value(),scene_minimum_mm=b['exact_global_minimum_mm'],max_difference_mm=max(deltas),passed=max(deltas)<1e-6))
        print('FULL_DISTANCE_REGRESSION',a['gap_mm'],max(deltas),flush=True)
    save('distance_regression.json',dict(samples=rows,passed=all(r['passed'] for r in rows),scope='Five known lost-crop poses; original BODY supplied without Boolean cropping. The last pose must remain a clearance failure.'))
    assert all(r['passed'] for r in rows) and not rows[-1]['result']['pass_check']

if __name__=='__main__':main()
