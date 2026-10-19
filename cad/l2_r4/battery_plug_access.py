"""Exact access volumes for the estimated battery connector after disassembly."""
from common import *

def main():
    fixed={n:load(n) for n in ['BODY','SF_RETAINER','SR_RETAINER','SIDE_FRONT_KEY','SIDE_REAR_KEY']}
    fixed.update({n:load(n,OUT/'reference') for n in ['SF_D2F_01F','SR_D2F_01F','SF_VERTICAL_PIN','SR_VERTICAL_PIN','SF_RETAINER_M2x5','SR_RETAINER_M2x5']})
    plug=load('BATTERY_PLUG_EST',OUT/'reference');pb=plug.BoundingBox();trials=[]
    for label,y0,y1 in [('full_side',pb.ymin+.5,pb.ymax-.5),('front2mm',pb.ymin+.5,pb.ymin+2.5),('rear2mm',pb.ymax-2.5,pb.ymax-.5)]:
        probes=[]
        for x in [pb.xmin-.55,pb.xmax+.55]:
            probe=box(x-.5,x+.5,y0,y1,pb.zmin,40)
            probes.append(dict(bounds_mm=bounds(probe),**scene_pairs(probe,fixed,'BATTERY_PLUG_ACCESS_FINGER',.05)))
        trials.append(dict(profile=label,probes=probes,passed=all(p['passed'] for p in probes)))
    accepted=next((t for t in trials if t['passed']),None)
    report=dict(trials=trials,probes=accepted['probes'] if accepted else trials[0]['probes'],chosen_profile=accepted['profile'] if accepted else None,plug_bounds_mm=bounds(plug),passed=accepted is not None,
        definition='Two1mm-thick straight tool fingers from+Z. Front/rear profiles contact2mm of the6mm estimated connector side. Remove main keys, wheel carrier and screwed H modules; retain BODY and side module. These are explicit tool-shape proposals, not a physical latch/force test.')
    save('battery_plug_access.json',report)

if __name__=='__main__':main()
