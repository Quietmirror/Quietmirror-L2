"""Independent full-solid/point checks for a suspected distance discontinuity."""
import json,time
from common import *
from battery_service_rrt import moved
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.Extrema import Extrema_ExtAlgo_Tree,Extrema_ExtFlag_MIN

def main():
    body=load('BODY');center=np.array([-17.,57.,16.4]);cell=box(-24,-10,47,67,13.4,19.4);rows=[]
    for p in json.loads((WORK/'battery_distance_anomaly_poses.json').read_text()):
        actor=moved(cell,center,np.array(p['pose']));known=cq.Vertex.makeVertex(-15.5,59.3,12.8)
        default=BRepExtrema_DistShapeShape(actor.wrapped,body.wrapped)
        tree=BRepExtrema_DistShapeShape(actor.wrapped,body.wrapped,1e-7,Extrema_ExtFlag_MIN,Extrema_ExtAlgo_Tree)
        point=BRepExtrema_DistShapeShape(actor.wrapped,known.wrapped)
        row=dict(p,full_default=default.Value(),full_tree=tree.Value(),known_point_distance=point.Value(),common_pair=pair(actor,body,'CELL','BODY',.5),actor_bounds=bounds(actor))
        rows.append(row);print(json.dumps(row),flush=True)
    save('battery_distance_diagnostic.json',rows)

if __name__=='__main__':main()
