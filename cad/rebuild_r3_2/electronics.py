"""Explicitly estimated electronic layouts; never supplier PCB dimensions."""
from pathlib import Path
import sys,json,ctypes
import cadquery as cq
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'cad/rebuild_r2'))
import build as exporter
from mechanics import box,cylinder,beam,join,check
from surfaces import make_surfaces
OUT=ROOT/'exports/rebuild_r3_2';RP=ROOT/'reports/rebuild_r3_2'

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
    # The electrical layouts are unchanged. Assemble the exact STEP files
    # copied by build.py rather than regenerating already validated inputs.
    p=json.loads((HERE/'electronics.json').read_text())
    assert p==json.loads((ROOT/'cad/rebuild_r3_1/electronics.json').read_text())
    def archived(rows,folder):
        return {row['name']:cq.importers.importStep(str(OUT/f"electronics/{folder}/{row['name']}.step")).val() for row in rows}
    objs=archived(p['custom'],'custom');reserves=archived(p['reserves'],'reserves');routes=archived(p['routes'],'routes')
    donor=cq.importers.importStep(str(OUT/'electronics/donor_blocked/UNMEASURED_DONOR_SLAB.step')).val()
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
    scenes=[scene('R3_2_MECHANICAL_FULL',{}),scene('R3_2_CUSTOM_ESTIMATED_LAYOUT',{**objs,**routes}),
            scene('R3_2_ATK_UNMEASURED_BLOCKED_DIAGNOSTIC',{'UNMEASURED_DONOR_SLAB_NONFIT':donor})]
    (RP/'scene_step_checks.json').write_text(json.dumps(scenes,indent=2),encoding='utf8')
    report={n:dict(size_mm=r['size'],center_mm=r['center'],kind=r['kind'],status='ESTIMATED NOT SUPPLIER DATA') for n,r in zip(objs,p['custom'])}
    (RP/'electronic_envelopes.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('R3_2 electronic envelope exports complete',len(objs),'physical estimates',len(reserves),'reserves',len(routes),'wire corridors',flush=True)
if __name__=='__main__':main()
