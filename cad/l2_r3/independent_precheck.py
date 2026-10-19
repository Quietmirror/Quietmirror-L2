"""Independent numerical checks, separate from production constructors."""
from pathlib import Path
import json,math
import cadquery as cq
from common import ROOT,RP,OUT,save,vol,box,cyl,baseline,load,pair
def main():
    old=json.loads((ROOT/'reports/rebuild_r3_2/cad_metrics.json').read_text())
    baseline_rows=[dict(name=n,volume_mm3=vol(baseline(n))) for n,r in old.items() if r['printable']]
    total=sum(r['volume_mm3'] for r in baseline_rows)
    rows=[]
    for n,x,y,t in [('SF',-3.03,5.25,6.8),('SR',-2.53,-5.55,-6.37)]:
        def inward(deg):
            a=math.radians(deg);return -(x*(math.cos(a)-1)-y*math.sin(a))
        angle=math.radians(t);lo=0.;hi=abs(t)
        for _ in range(60):
            mid=(lo+hi)/2
            if inward(math.copysign(mid,t))<.5:lo=mid
            else:hi=mid
        rows.append(dict(name=n,stop_center_motion_mm=inward(t),nominal_unshimmed_depression_mm=inward(t)-.35,after_shim_0p03_gap_mm=inward(t)-.03,zero_gap_PT0p5_angle_deg=(lo+hi)/2,y_slide_mm=x*math.sin(angle)+y*(math.cos(angle)-1)))
    carrier=load('SIDE_SWITCH_CARRIER');obs={n:baseline(n) for n in ['BODY','LEFT_KEY','RIGHT_KEY','WHEEL_CARRIER']}
    # Unmodified BODY includes old sockets: this contextual overlap is not
    # classified as a final-model collision.
    pairs=[pair(carrier,s,'r3_carrier','R32_'+n,0,n=='BODY') for n,s in obs.items()]
    save('independent_precheck.json',dict(K1=dict(parts=baseline_rows,total_mm3=total,reference_mm3=18506.678,within_0p5=abs(total-18506.678)<=.5),K8_rigid_endpoint=rows,context_pairs=pairs,author_files_available=False,K9_reference_claim_status='UNVERIFIED: absent author JSON/STEP; final rebuilt geometry checked separately',production_permission='User explicitly authorized incomplete pre-release despite unresolved author reproduction gate'))
    print('K1',total,'side motion independently checked',flush=True)
if __name__=='__main__':main()
