"""Explicitly estimated electronic layouts; never supplier PCB dimensions."""
from pathlib import Path
import sys,json,ctypes
import cadquery as cq
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'cad/rebuild_r2'))
import build as exporter
from mechanics import box,cylinder,beam,join,check
from surfaces import make_surfaces
OUT=ROOT/'exports/rebuild_r3_1';RP=ROOT/'reports/rebuild_r3_1'

def make():
    p=json.loads((HERE/'electronics.json').read_text())
    objs={};reserves={};routes={}
    for row in p['custom']:
        s=box(*row['size'],(0,0,0))
        if row.get('rotation_y_deg'):s=s.rotate((0,0,0),(0,1,0),row['rotation_y_deg'])
        s=s.translate(row['center'])
        if row.get('holes_for_side_terminals'):
            for cy in (50.,65.):
                for dy in (-5.08,0,5.08):s=s.cut(box(4,2,1.2,(14.8,cy+2+dy,15.)))
        objs[row['name']]=check(s,row['name'])
    for row in p['reserves']:
        s=box(*row['size'],(0,0,0))
        if row.get('rotation_y_deg'):s=s.rotate((0,0,0),(0,1,0),row['rotation_y_deg'])
        reserves[row['name']]=s.translate(row['center'])
    for row in p['routes']:
        points=row['points'];r=row['radius']
        s=join(*[beam(a,b,r) for a,b in zip(points,points[1:])],
               *[cq.Solid.makeSphere(r,cq.Vector(*a)) for a in points])
        routes[row['name']]=check(s,row['name'])
    return p,objs,reserves,routes

def main():
    ctypes.windll.kernel32.SetPriorityClass(ctypes.c_void_p(-1),0x4000)
    p,objs,reserves,routes=make()
    for folder,shapes in [('electronics/custom',objs),('electronics/reserves',reserves),('electronics/routes',routes)]:
        dest=OUT/folder;dest.mkdir(parents=True,exist_ok=True)
        for n,s in shapes.items():
            cq.exporters.export(s,str(dest/f'{n}.step'))
            s.exportStl(str(dest/f'{n}.stl'),tolerance=.025,relative=False,parallel=False)
    donor=box(*p['donor']['size'],p['donor']['center'])
    (OUT/'electronics/donor_blocked').mkdir(parents=True,exist_ok=True)
    cq.exporters.export(donor,str(OUT/'electronics/donor_blocked/UNMEASURED_DONOR_SLAB.step'))
    donor.exportStl(str(OUT/'electronics/donor_blocked/UNMEASURED_DONOR_SLAB.stl'),tolerance=.025,relative=False)
    pp=json.loads((ROOT/'cad/rebuild_r2/parameters.json').read_text())
    outer,_,_=make_surfaces(pp)
    cq.exporters.export(outer,str(OUT/'gauges/MOTHER_OUTER_REFERENCE.step'))
    outer.exportStl(str(OUT/'gauges/MOTHER_OUTER_REFERENCE.stl'),tolerance=.025,relative=False,parallel=False)
    # One scene is an explicit failure diagnostic; do not offer it as a print.
    met=json.loads((RP/'cad_metrics.json').read_text())
    parts={n:cq.importers.importStep(str(OUT/f'assembly/{n}.step')).val() for n in met}
    def scene(filename,extra):
        assembly=cq.Assembly(name=filename)
        for n,s in {**parts,**extra}.items():
            color=(.19,.39,.43) if met.get(n,{}).get('printable') else (.72,.48,.2)
            if n in objs:color=(.15,.55,.4) if 'PCB' in n else (.4,.56,.76) if 'BATTERY_CELL' in n else (.4,.4,.43)
            if n in routes:color=(.9,.45,.13)
            if n.startswith('UNMEASURED'):color=(.86,.12,.12)
            assembly.add(s,name=n,color=cq.Color(*color))
        assembly.save(str(OUT/(filename+'.step')),exportType='STEP')
        back=cq.importers.importStep(str(OUT/(filename+'.step'))).val()
        assert back.isValid() and len(back.Solids())==len(parts)+len(extra),(filename,len(back.Solids()))
        return dict(file=filename+'.step',solids=len(back.Solids()),valid=back.isValid(),named_components=True)
    scenes=[scene('R3_1_MECHANICAL_FULL',{}),scene('R3_1_CUSTOM_ESTIMATED_LAYOUT',{**objs,**routes}),
            scene('R3_1_ATK_UNMEASURED_BLOCKED_DIAGNOSTIC',{'UNMEASURED_DONOR_SLAB_NONFIT':donor})]
    (RP/'scene_step_checks.json').write_text(json.dumps(scenes,indent=2),encoding='utf8')
    report={n:dict(size_mm=r['size'],center_mm=r['center'],kind=r['kind'],status='ESTIMATED NOT SUPPLIER DATA') for n,r in zip(objs,p['custom'])}
    (RP/'electronic_envelopes.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('R3_1 electronic envelope exports complete',len(objs),'physical estimates',len(reserves),'reserves',len(routes),'wire corridors',flush=True)
if __name__=='__main__':main()
