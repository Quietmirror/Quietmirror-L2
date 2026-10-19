from common import *
def main():
    body=load('BODY');rows=[]
    for n in ['SIDE_FRONT_KEY','SIDE_REAR_KEY']:
        hit=body.intersect(load(n));r=dict(part=n,overlap_mm3=vol(hit),pieces=[dict(volume_mm3=vol(s),bounds_mm=bounds(s)) for s in hit.Solids()]);rows.append(r)
        cq.exporters.export(hit,str(WORK/(n+'_BODY_overlap.step')));print(r,flush=True)
    save('pre_correction_overlap.json',rows)
if __name__=='__main__':main()
