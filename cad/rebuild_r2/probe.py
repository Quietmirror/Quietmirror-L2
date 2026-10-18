"""Fast component diagnostics before the integrated boolean/export run."""
import json, time, ctypes
from pathlib import Path
import cadquery as cq
from surfaces import make_surfaces
from mechanics import build_mechanics
from interfaces import build_interfaces
from interface_check import conflict

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CACHE=ROOT.parent/'_support/work/fenrir_rebuild_r2/build'

def load_surfaces(p):
    CACHE.mkdir(parents=True,exist_ok=True)
    key=json.dumps(p['host'],sort_keys=True)
    f=CACHE/'surface_key.txt'
    if f.exists() and f.read_text()==key:
        return cq.importers.importStep(str(CACHE/'mother_outer.step')).val(),cq.importers.importStep(str(CACHE/'mother_inner.step')).val()
    outer,inner,meta=make_surfaces(p)
    for name,s in [('outer',outer),('inner',inner)]:cq.exporters.export(s,str(CACHE/f'mother_{name}.step'))
    f.write_text(key)
    return outer,inner

def main():
    ctypes.windll.kernel32.SetPriorityClass(ctypes.c_void_p(-1),0x4000)
    p=json.loads((HERE/'parameters.json').read_text(encoding='utf8'))
    start=time.time();outer,inner=load_surfaces(p)
    print('Surfaces ready',time.time()-start,flush=True)
    m=build_mechanics(p,outer,inner);print('Mechanics ready',time.time()-start,flush=True)
    q=build_interfaces(p,outer,m['parts'])
    m['body_additions']+=q['body_additions'];m['body_cuts']+=q['body_cuts'];m['hardware'].update(q['hardware'])
    failures=[]
    for n,s in m['parts'].items():
        for i,a in enumerate(m['body_additions']):
            r=conflict(s,a,part=n,support=i)
            if r:failures.append(r);print('PART SUPPORT',r,flush=True)
    for n,s in m['hardware'].items():
        for name,a in m['parts'].items():
            r=conflict(s,a,hardware=n,part=name)
            if r:failures.append(r);print('HARDWARE PART',r,flush=True)
    (CACHE/'probe.json').write_text(json.dumps(failures,indent=2),encoding='utf8')
    print('Probe complete',len(failures),'seconds',time.time()-start,flush=True)

if __name__=='__main__':main()
