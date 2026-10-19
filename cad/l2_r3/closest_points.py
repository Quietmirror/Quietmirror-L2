from common import *
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
def main():
    body=load('BODY');rows=[]
    for n in ['LEFT_KEY','RIGHT_KEY','WHEEL_CARRIER']:
        actor=load(n);bb=actor.BoundingBox();local=body.intersect(box(bb.xmin-.7,bb.xmax+.7,bb.ymin-.7,bb.ymax+.7,bb.zmin-.7,bb.zmax+.7))
        algo=BRepExtrema_DistShapeShape(local.wrapped,actor.wrapped);algo.Perform()
        p=algo.PointOnShape1(1);q=algo.PointOnShape2(1)
        rows.append(dict(part=n,distance=algo.Value(),body_point=[p.X(),p.Y(),p.Z()],actor_point=[q.X(),q.Y(),q.Z()]))
    save('nearest_clearance_locations.json',rows);print(rows,flush=True)
if __name__=='__main__':main()
