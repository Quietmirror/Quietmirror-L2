"""One exact main-key pose, with checkpoints to locate slow CAD operations."""
import json,time,os,subprocess,sys
from common import *
from exact_distance import pair
from contact_audit import collar,rigid_housing

def main():
    progress=[]
    def mark(stage,**extra):
        progress.append(dict(stage=stage,**extra));save('main_motion_probe.json',progress)
        print('MOTION_PROBE',stage,extra,flush=True)
        if os.getenv('GITHUB_ACTIONS')=='true':subprocess.run([sys.executable,str(ROOT/'cad/l2_r4/ci_checkpoint.py')],check=True)
    inv=json.loads((RP/'assembly_inventory.json').read_text());meta=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text())
    parts={n:load(n) for n in inv['printable']};hw={n:load(n,OUT/'reference') for n in inv['H_hardware']}
    features={p.stem:cq.importers.importStep(str(p)).val() for p in (OUT/'validation_features').glob('*.step')}
    mo=next(m for m in meta['mechanisms']['motions'] if m['part']=='LEFT_KEY');n=mo['part']
    fixed={**{bn:b for bn,b in parts.items() if bn!=n},**{bn:b for bn,b in hw.items() if bn!=mo['switch']}}
    fixed[mo['switch']+'_RIGID_HOUSING']=rigid_housing(hw[mo['switch']],mo)
    mark('loaded',key_faces=len(parts[n].Faces()),body_faces=len(parts['BODY'].Faces()))
    started=time.time();named=unite(features[n+'_FIXED_BEARINGS'],features[n+'_PRESS_STOP']);mark('united_contacts',seconds=time.time()-started,solids=len(named.Solids()))
    started=time.time();nonfunctional=parts['BODY'].cut(collar(named,.30001));mark('body_cut',seconds=time.time()-started,valid=nonfunctional.isValid())
    ori=mo['origin'];actor=parts[n].rotate(ori,[ori[0]+1,*ori[1:]],-.5)
    aa=actor.BoundingBox();queue=[]
    for bn,b in fixed.items():
        bb=b.BoundingBox();delta=[max(0.,getattr(aa,c+'min')-getattr(bb,c+'max'),getattr(bb,c+'min')-getattr(aa,c+'max')) for c in 'xyz'];queue.append((float(np.linalg.norm(delta)),bn,b))
    queue.sort(key=lambda x:x[0]);best=float('inf')
    for lower,bn,b in queue:
        if lower>max(best,.3)+1e-6:continue
        mark('pair_begin',part=bn);started=time.time();r=pair(actor,b,n,bn,.3);best=min(best,r['gap_mm']);mark('pair_end',part=bn,seconds=time.time()-started,result=r)
        if bn=='BODY':
            mark('nonfunctional_begin');started=time.time();r=pair(actor,nonfunctional,n,'BODY',.3);mark('nonfunctional_end',seconds=time.time()-started,result=r)
    mark('completed')
if __name__=='__main__':main()
