"""Two explicitly ESTIMATED electronics assemblies; not measured donor CAD.

Every size/placement is in the JSON. No inferred mounting hole coordinates.
The STEP assemblies contain multiple named solids; transparent reservations
are optional in a separate CLEARANCES STEP and are not printable components.
"""
from pathlib import Path
import json,itertools,argparse,subprocess,sys
import cadquery as cq
import trimesh
from build_mouse import rounded_box,soft_box,beam
from build_v03 import bounds
ROOT=Path(__file__).resolve().parents[1]
COLORS={'pcb':(.14,.48,.35),'chip':(.14,.17,.20),'battery':(.81,.70,.35),'connector':(.65,.72,.77),'wheel':(.20,.25,.30),'switch':(.80,.41,.24),'wire':(.67,.22,.19),'lens':(.25,.66,.78),'reserve':(.68,.33,.75)}

def geometry(e):
    s=e['size'];r=min(.6,min(s)/4)
    result=soft_box(*s,r,e['center']) if e['kind']=='battery' else rounded_box(*s,r,e['center'])
    for c in e.get('cutouts',[]):result=result.cut(rounded_box(*c['size'],1,c['center']))
    return result

def write_mesh(shape,path):
    shape.exportStl(str(path),tolerance=.025,angularTolerance=.15,relative=False,parallel=False)
    m=trimesh.load_mesh(path);m.merge_vertices(digits_vertex=6);m.update_faces(m.nondegenerate_faces(height=1e-7));m.update_faces(m.unique_faces());m.remove_unreferenced_vertices();m.export(path)
    assert m.is_watertight and m.is_winding_consistent and len(m.split(only_watertight=False))==1,path

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--variant',choices=['ATK_A1_PLUS','PAW3950_CUSTOM']);args=ap.parse_args()
    # Release native CAD allocations between assemblies instead of retaining
    # two detailed STEP scenes in a single long-lived kernel process.
    if not args.variant:
        for name in ('ATK_A1_PLUS','PAW3950_CUSTOM'):
            subprocess.run([sys.executable,__file__,'--variant',name],check=True)
        return
    specfile=ROOT/'cad/electronics_v06.json'
    spec=json.loads(specfile.read_text());out=ROOT/'exports/v06';rp=ROOT/'reports/v06'
    shell=cq.importers.importStep(str(out/'quietmirror_fingertip_V0.6_SHELL.step')).val()
    caps=[cq.importers.importStep(str(ROOT/f'.tools/v06_cap_{i}_placed.step')).val() for i in (1,2)]
    p=json.loads((ROOT/'cad/parameters_v06.json').read_text());wz=p['height']+p['wheel']['height_offset']-p['wheel']['diameter']/2
    allreports=[]
    for variant,entries in spec['options'].items():
        if args.variant and args.variant!=variant:continue
        print('Building',variant,flush=True)
        folder=out/variant;folder.mkdir(exist_ok=True)
        shapes={e['name']:geometry(e) for e in entries};meta={e['name']:e for e in entries}
        shapes['wheel_EST']=cq.Workplane(obj=cq.Solid.makeCylinder(7.5,5.2,cq.Vector(-2.6,-17,wz),cq.Vector(1,0,0))).edges().fillet(1).val()
        shapes['wheel_axle_EST']=cq.Solid.makeCylinder(.7,11.5,cq.Vector(-8.5,-17,wz),cq.Vector(1,0,0))
        # The paths are wire centreline illustrations with realistic 1.2 mm
        # envelope; endpoint lead-ins are schematic rather than pin assignments.
        wirepaths={'USB_harness_EST':[(7,-8,7),(10,-12,7),(13,-20,7)],'battery_harness_EST':[(12,-48,14),(13.8,-48,13.4)],'side_harness_EST':[(-15.5,-40,13.8),(-12,-40,10.2)]}
        if variant=='PAW3950_CUSTOM':wirepaths['RF_harness_EST']=[(12,-42,7),(14,-55,7),(9,-63,7)]
        for n,pts in wirepaths.items():
            s=beam(pts[0],pts[1],1.2)
            for a,b in zip(pts[1:],pts[2:]):s=s.fuse(beam(a,b,1.2))
            shapes[n]=s
        for n in shapes:
            if n not in meta:meta[n]=dict(name=n,kind='wire' if 'harness' in n else 'wheel',basis='Estimated shape/path; final mechanical and electrical interface unknown.')
        assembly=cq.Assembly(shell,name='SHELL_fixed_mainkeys_EST',color=cq.Color(.50,.64,.68))
        for i,c in enumerate(caps):assembly.add(c,name=f'left_side_cap_{i+1}',color=cq.Color(.88,.53,.25))
        physical=[]
        for name,shape in shapes.items():
            assert shape.isValid() and len(shape.Solids())==1,name
            color=COLORS[meta[name]['kind']]
            assembly.add(shape,name=name,color=cq.Color(*color));write_mesh(shape,folder/(name+'.stl'))
            bb=bounds(shape);physical.append(dict(**meta[name],file=f'exports/v06/{variant}/{name}.stl',color=color,dimensions_xyz_mm=[bb[i+3]-bb[i] for i in range(3)],shell_overlap_mm3=shell.intersect(shape).Volume(tol=1e-7),shell_min_distance_mm=shell.distance(shape),caps_overlap_mm3=sum(c.intersect(shape).Volume(tol=1e-7) for c in caps)))
        print(variant,'physical geometry checked',flush=True)
        stem=f'quietmirror_V0.6_{variant}_ESTIMATED'
        assembly.save(str(out/(stem+'.step')))
        # Multi-part 3MF is an inspection scene, explicitly not a print plate.
        scene=trimesh.Scene();scene.add_geometry(trimesh.load_mesh(out/'quietmirror_fingertip_V0.6_SHELL.stl'),node_name='SHELL')
        for i in (1,2):scene.add_geometry(trimesh.load_mesh(ROOT/f'.tools/v06_cap_{i}_placed.stl'),node_name=f'cap{i}')
        for a in physical:
            m=trimesh.load_mesh(ROOT/a['file']);m.visual.face_colors=[int(x*255) for x in a['color']]+[255];scene.add_geometry(m,node_name=a['name'])
        scene.units='mm';(out/(stem+'_VIEW_ONLY.3mf')).write_bytes(trimesh.exchange.threemf.export_3MF(scene))
        print(variant,'STEP and 3MF saved',flush=True)
        checks=[]
        allowed={frozenset(('wheel_EST','wheel_axle_EST')),frozenset(('encoder_EST','wheel_axle_EST')),frozenset(('power_switch_body_EST','power_switch_tab_EST')),frozenset(('battery_500mAh_TARGET','battery_harness_EST'))}
        for (an,a),(bn,b) in itertools.combinations(shapes.items(),2):
            # Coarse AABB filter avoids hundreds of irrelevant CAD booleans.
            ba,bb=bounds(a),bounds(b)
            if any(min(ba[i+3],bb[i+3])-max(ba[i],bb[i])<=1e-5 for i in range(3)):continue
            vol=a.intersect(b).Volume(tol=1e-7)
            if vol>.01:checks.append(dict(a=an,b=bn,overlap_mm3=vol,intended_interface=frozenset((an,bn)) in allowed))
        reservations=[]
        clear=cq.Assembly(name=variant+'_CLEARANCES_NOT_PARTS')
        for e in spec['reserves']:
            print(variant,'reservation',e['name'],flush=True)
            s=geometry(e);clear.add(s,name=e['name'],color=cq.Color(*COLORS['reserve'],.2))
            write_mesh(s,folder/(e['name']+'.stl'))
            hits=[dict(part=n,volume_mm3=v) for n,a in shapes.items() if (v:=s.intersect(a).Volume(tol=1e-7))>.01]
            reservations.append(dict(**e,hits=hits,shell_overlap_mm3=shell.intersect(s).Volume(tol=1e-7)))
        clear.save(str(out/(stem+'_CLEARANCES.step')))
        rep=dict(variant=variant,all_dimensions_estimated=True,physical=physical,component_overlaps=checks,reservations=reservations,wire_paths=wirepaths,unresolved='Actual donor outline/holes, functional key/scroll mechanisms, attachment scheme, optical Z stack, antenna tuning, firmware and runtime test remain open. No fitted board claim.')
        (rp/(variant+'_layout.json')).write_text(json.dumps(rep,indent=2),encoding='utf8');allreports.append(rep)
        print(variant,'physical',len(physical),'shell collisions',[(a['name'],round(a['shell_overlap_mm3'],2)) for a in physical if a['shell_overlap_mm3']>.01],'component overlaps',checks,flush=True)
    (rp/'power_budget.json').write_text(json.dumps(spec['power'],indent=2),encoding='utf8')

if __name__=='__main__':main()
