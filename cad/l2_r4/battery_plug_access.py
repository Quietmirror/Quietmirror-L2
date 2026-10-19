"""Exact access volumes for the estimated battery connector after disassembly."""
from common import *

def main():
    fixed={n:load(n) for n in ['BODY','SF_RETAINER','SR_RETAINER','SIDE_FRONT_KEY','SIDE_REAR_KEY']}
    fixed.update({n:load(n,OUT/'reference') for n in ['SF_D2F_01F','SR_D2F_01F','SF_VERTICAL_PIN','SR_VERTICAL_PIN','SF_RETAINER_M2x5','SR_RETAINER_M2x5']})
    plug=load('BATTERY_PLUG_EST',OUT/'reference');pb=plug.BoundingBox();probes=[]
    for x in [pb.xmin-.55,pb.xmax+.55]:
        probe=box(x-.5,x+.5,pb.ymin+.5,pb.ymax-.5,pb.zmin,40)
        probes.append(dict(bounds_mm=bounds(probe),**scene_pairs(probe,fixed,'BATTERY_PLUG_ACCESS_FINGER',.05)))
    report=dict(probes=probes,plug_bounds_mm=bounds(plug),passed=all(p['passed'] for p in probes),
        definition='Two1mm straight tool fingers from+Z after removing main keys, wheel carrier and screwed H modules. Original integral BODY and side module retained. No physical latch force or vendor connector dimensions claimed.')
    save('battery_plug_access.json',report)

if __name__=='__main__':main()
