"""Fast diagnostic on current parametric estimates. Final validation is separate."""
from pathlib import Path
import sys,json,itertools,ctypes
import cadquery as cq
ROOT=Path(__file__).resolve().parents[2]
from electronics import make
from validate import loadmesh,tomesh,intersection,sphere

def main():
    ctypes.windll.kernel32.SetPriorityClass(ctypes.c_void_p(-1),0x4000)
    met=json.loads((ROOT/'reports/rebuild_r3/cad_metrics.json').read_text())
    mods={n:loadmesh(ROOT/f'exports/rebuild_r3/assembly/{n}.stl') for n in met}
    p,objs,reserves,routes=make();extra={n:tomesh(s,'probe_'+n) for n,s in {**objs,**routes}.items()}
    allm={**mods,**extra};allow={}
    for r in p['routes']:
        for pt,name in zip([r['points'][0],r['points'][-1]],r['end_contacts']):allow[frozenset([r['name'],name])]=sphere(r['radius']+.02,pt)
    rows=[]
    for a,b in itertools.combinations(allm,2):
        if a not in extra and b not in extra:continue
        v=intersection(allm[a],allm[b])
        if v>.01:
            z=allow.get(frozenset([a,b]));v=((allm[a]^allm[b])-z).volume() if z is not None else v
            if v>.01:rows.append([a,b,round(v,5)])
    print('STATIC EXTRA',json.dumps(rows),flush=True)
    for r in p['reserves']:
        m=tomesh(reserves[r['name']],'probe_'+r['name'])
        rows=[[n,round(v,5)] for n,b in allm.items() if n not in r['allowed'] and (v:=intersection(m,b))>.01]
        print(r['name'],json.dumps(rows),flush=True)
    if '--battery-search' in sys.argv:
        import manifold3d as md
        best=[]
        for x in [-16.5,-16.,-15.5,-15.]:
          for y in [57.,58.,59.,60.]:
            for z in [16.4,16.6,16.8,17.]:
                m=md.Manifold.cube([21,25,7],True).translate([x,y,z]);hit={}
                for n,q in allm.items():
                    if n=='BATTERY_CELL_EST':continue
                    v=intersection(m,q)
                    if v>.01:hit[n]=v
                best.append(dict(center=[x,y,z],volume=sum(hit.values()),hits=hit))
        best.sort(key=lambda r:r['volume']);print('BATTERY SEARCH',json.dumps(best[:8]),flush=True)
if __name__=='__main__':main()
