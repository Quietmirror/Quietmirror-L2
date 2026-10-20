"""Local contact decomposition of the final D7 lever, never blanket BODY exclusion.

Full-solid common volume is required over the physical travel. Diagnostic
poses beyond a hard stop must intersect only the named stop surfaces. The
remaining moving/fixed geometry retains the 0.30 mm requirement.
"""
import math,json,os
import numpy as np
from common import *
from exact_distance import pair
from bounded_scene import scene_pairs
from partition_check import subtract
from side_module import KEYS,fixed_features,key,UPPER_LUG_TOP,EAR_RADIUS,EAR_TOP,BRIDGE_BOTTOM

def main(selected_key=None,angle_indices=None,report_name=None):
    development=os.environ.get('R4_SIDE_LOCAL_PROBE')=='1'
    body=load('BODY');outer=load('MOTHER_OUTER_FROM_R32_SURFACE',ROOT/'exports/l2_r2_diagnostic/support_reference')
    params=json.loads((RP/'parameters_implemented.json').read_text())['side_keys'];rows=[]
    inventory=json.loads((RP/'assembly_inventory.json').read_text())
    parts={n:load(n) for n in inventory['printable'] if n!='BODY'}
    hardware={n:load(n,OUT/'reference') for n in inventory['H_hardware']}
    for k,p in zip(KEYS,params):
        if selected_key is not None and k['name']!=selected_key:continue
        cap=load(k['name']);y=k['hinge_y'];sg=k['sign'];hx=k['hinge_x'];ori=(hx,y,0);axis=(hx,y,1)
        # Masks are the exact source-defined functional features, trimmed to
        # the exported final solids. No nearby non-functional skin is removed.
        ear_mask=box(hx-EAR_RADIUS,hx,y-.4,y+.4,BRIDGE_BOTTOM,EAR_TOP)
        ear=cap.intersect(ear_mask)
        rib=cap.intersect(box(p['stop_rib_inner_x'],34,*k['stop_y'],15.9,16.4))
        # At a continuous solid's functional-feature seam, the distance
        # tends to zero. Keep a declared 0.30mm collar for clearance only;
        # overlap is still classified using the exact unexpanded features.
        def collar(s):
            b=s.BoundingBox();d=.30001
            return box(b.xmin-d,b.xmax+d,b.ymin-d,b.ymax+d,b.zmin-d,b.zmax+d)
        rest,pe=subtract(cap,collar(ear),k['name']+' ear collar')
        rest,pr=subtract(rest,collar(rib),k['name']+' rib collar')
        ya,yb=(y+.4,y+1.4) if sg>0 else (y-1.4,y-.4)
        outward=body.intersect(unite(box(hx-1.5,hx-.7,ya,yb,18.6,UPPER_LUG_TOP),box(hx-1.5,hx+.7,ya,yb,19.8,UPPER_LUG_TOP)))
        px0,py0,py1=(25.5,53.6,55.4) if sg>0 else (26.,59.1,61.1)
        post=body.intersect(box(px0,k['stop_x'],py0,py1,15.7,16.4))
        without_outward,po=subtract(body,collar(outward),k['name']+' BODY outward stop')
        without_post,pp=subtract(body,collar(post),k['name']+' BODY inward post')
        others={n:s for n,s in {**parts,**hardware}.items() if n not in [k['name'],k['short']+'_VERTICAL_PIN',k['short']+'_TUNING_SHIM_0p33',k['short']+'_D2F_01F']}
        shim=hardware[k['short']+'_TUNING_SHIM_0p33']
        tests=[]
        physical=np.linspace(0,k['angle'],7 if development else 31)
        if angle_indices is not None:physical=physical[np.asarray(angle_indices,dtype=int)]
        for angle in list(physical)+[-sg*.5,k['angle']+sg*.3]:
            angle=float(angle);normal=0<=angle*sg<=abs(k['angle'])+1e-8
            rotated=lambda s:s.rotate(ori,axis,angle)
            full=pair(rotated(cap),body,k['name'],'BODY',0.)
            nonfunctional=[pair(rotated(rest),body,k['name']+'_NONCONTACT','BODY',.3),
                           pair(rotated(ear),without_outward,k['name']+'_EAR','BODY',.3),
                           pair(rotated(rib),without_post,k['name']+'_PRESS_RIB','BODY',.3)]
            allowed=vol(rotated(ear).intersect(outward))+vol(rotated(rib).intersect(post))
            residual=max(0,full['overlap_mm3']-allowed)
            scene=scene_pairs(cq.Compound.makeCompound([rotated(cap),rotated(shim)]),others,k['name']+'+PET',.3) if not development else dict(passed=True,scope='Skipped for development-only local clearance probe; not G5 evidence')
            tests.append(dict(angle_deg=angle,within_physical_travel=normal,full=full,nonfunctional=nonfunctional,
                other_components=scene,named_stop_overlap_mm3=allowed,unexplained_overlap_mm3=residual,
                passed=residual<=.001 and (not normal or full['overlap_mm3']<=.001) and all(q['pass_check'] for q in nonfunctional) and scene['passed']))
            print('SIDE_LOCAL',k['short'],angle,'full',full['overlap_mm3'],'residual',residual,'min_nonfunctional',min(q['gap_mm'] for q in nonfunctional),flush=True)
        rest_contact=pair(ear,outward,'EAR','OUTWARD_STOP',0.)
        # The physical rest pose must touch the outward stop with no solid
        # overlap; its -0.5-degree diagnostic pose must be blocked there.
        outward_sample=tests[-2]
        outpass=rest_contact['gap_mm']<=.001 and rest_contact['overlap_mm3']<=.001 and outward_sample['named_stop_overlap_mm3']>.001 and outward_sample['unexplained_overlap_mm3']<=.001
        r=dict(part=k['name'],samples=tests,functional_partitions=[pe,pr,po,pp],outward_stop_angle_deg=0.,outward_rest_contact=rest_contact,
               outward_stop_pass=outpass,passed=all(t['passed'] for t in tests) and outpass,
               method='Independent exact BRep full common + source-feature contact decomposition; forced poses beyond hard stop are diagnostic only, not usable travel.')
        rows.append(r);save(report_name or ('side_clearance_probe.json' if development else 'side_functional_motion.json'),rows)

if __name__=='__main__':main()
