"""Electronic space studies with the actual V0.7 mechanical test assembly.

Not fitted donor CAD or a fabricated PCB; collisions are reported, not hidden.
"""
from pathlib import Path
import json,itertools,argparse,subprocess,sys
import cadquery as cq
import trimesh
from electronics_v06 import geometry,write_mesh,COLORS
from build_v03 import bounds
from validate_v07 import overlap
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'exports/v07';RP=ROOT/'reports/v07'
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--variant',choices=['ATK_A1_PLUS','PAW3950_CUSTOM']);args=ap.parse_args()
    if not args.variant:
        for v in ('ATK_A1_PLUS','PAW3950_CUSTOM'):subprocess.run([sys.executable,__file__,'--variant',v],check=True)
        return
    v=args.variant;spec=json.loads((ROOT/'cad/electronics_v07.json').read_text(encoding='utf8'));info=json.loads((RP/'cad_metrics.json').read_text(encoding='utf8'));folder=OUT/v;folder.mkdir(exist_ok=True)
    mech={a['name']:cq.importers.importStep(str(OUT/'placed'/(a['name']+'.step'))).val() for a in info['parts']}
    assy=cq.Assembly(name=v+'_ESTIMATED_SPACE_STUDY');scene=trimesh.Scene();record=[]
    for a in info['parts']:
        n=a['name'];assy.add(mech[n],name=n,color=cq.Color(*a['color']));scene.add_geometry(trimesh.load_mesh(ROOT/a['file']),node_name=n)
    for module in ('left','right','middle','thumb_front','thumb_rear'):
        n=module+'_SWITCH_EXAMPLE';mech[n]=cq.importers.importStep(str(OUT/'placed'/(n+'.step'))).val();assy.add(mech[n],name=n,color=cq.Color(.76,.31,.21))
        mesh=trimesh.load_mesh(OUT/'placed'/(n+'.stl'));mesh.visual.face_colors=[194,79,54,255];scene.add_geometry(mesh,node_name=n)
    shapes={e['name']:geometry(e) for e in spec['options'][v]}
    for e in spec['options'][v]:
        n=e['name'];s=shapes[n];hits=[]
        for mn,m in mech.items():
            if mn=='BODY':
                bb=bounds(s);region=cq.Workplane('XY').box(*[bb[i+3]-bb[i]+.2 for i in range(3)]).val().translate([(bb[i]+bb[i+3])/2 for i in range(3)]);m=m.intersect(region)
            vol=overlap(m,s)
            if vol>.01:hits.append(dict(part=mn,overlap_mm3=vol))
        color=[.85,.22,.19] if hits else list(COLORS[e['kind']]);write_mesh(s,folder/(n+'.stl'));cq.exporters.export(s,str(folder/(n+'.step')))
        assy.add(s,name=n,color=cq.Color(*color));mesh=trimesh.load_mesh(folder/(n+'.stl'));mesh.visual.face_colors=[int(c*255) for c in color]+[255];scene.add_geometry(mesh,node_name=n)
        record.append(dict(**e,file=f'exports/v07/{v}/{n}.stl',color=color,mechanical_hits=hits));print(v,n,hits,flush=True)
    pairs=[]
    for (an,a),(bn,b) in itertools.combinations(shapes.items(),2):
        vol=overlap(a,b)
        if vol>.01:pairs.append(dict(a=an,b=bn,overlap_mm3=vol,intentional={an,bn}=={'power_switch_body_EST','power_switch_tab_EST'}))
    assy.save(str(OUT/f'quietmirror_V0.7_{v}_ESTIMATED.step'));scene.units='mm';(OUT/f'quietmirror_V0.7_{v}_VIEW_ONLY.3mf').write_bytes(trimesh.exchange.threemf.export_3MF(scene))
    report=dict(variant=v,all_dimensions_estimated=True,physical=record,component_intersections=pairs,status=spec['status'],switches=spec['prototype_switches'],power=spec['power'],optical_stack='Not solved: sensor axis vertical, lens-to-pad distance depends on real parts and skate stack.',wiring='V0.6 lead routes and antenna reservations are historical references, not validated routes for the new mechanisms. New wiring must clear moving parts throughout their stroke.',assembly_mounting='Test switches have printable trays. PCB screw holes and encoder coupling are deliberately not inferred from estimated boxes.')
    (RP/(v+'_layout.json')).write_text(json.dumps(report,indent=2),encoding='utf8')
if __name__=='__main__':main()
