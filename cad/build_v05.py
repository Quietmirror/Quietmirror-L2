"""V0.5 original Fenrir-informed upper; frozen V0.3 bottom. Units: mm.

Requires the versioned V0.3 STEP already included in this repository.
Commercial reference photos inform proportions only, never copied geometry.
"""
from pathlib import Path
import argparse, copy, json, time
import cadquery as cq
import trimesh
from build_mouse import rounded_box, beam, envelope_defs
from build_v03 import bounds, yz_round, side_window, side_cap, make_surfaces as legacy_surfaces

from vent_layout_v05 import cells, cutter, manifest
ROOT=Path(__file__).resolve().parents[1]
V=cq.Vector

def save_model(shape,stem,out):
    assert shape.isValid() and len(shape.Solids())==1
    cq.exporters.export(shape,str(out/(stem+'.step')))
    s=cq.importers.importStep(str(out/(stem+'.step'))).val()
    raw=ROOT/'.tools'/('raw_'+stem+'.stl')
    s.exportStl(str(raw),tolerance=.02,angularTolerance=.15,relative=False,parallel=False)
    m=trimesh.load_mesh(raw);raw_faces=len(m.faces)
    m.merge_vertices(digits_vertex=6);m.update_faces(m.nondegenerate_faces(height=1e-7))
    m.update_faces(m.unique_faces());m.remove_unreferenced_vertices()
    m.export(out/(stem+'.stl'))
    assert m.is_watertight and len(m.split(only_watertight=False))==1,stem
    bb=bounds(s)
    return dict(name=stem,dimensions_xyz_mm=[bb[i+3]-bb[i] for i in range(3)],bounds=[list(bb[:3]),list(bb[3:])],volume_mm3=s.Volume(tol=1e-9),volume_integration_tolerance=1e-9,cad_valid=s.isValid(),cad_solids=len(s.Solids()),mesh_cleanup=dict(raw_faces=raw_faces,final_faces=len(m.faces),weld_tolerance_mm=1e-6,holes_patched=0,components_discarded=0))

def make_surfaces(p):
    # V0.3's loft generator expects a 30 mm reference crown with H-1 scaling.
    q=copy.deepcopy(p)
    q['height']=p['height']+1
    q['max_width']=p['max_width']-p['upper_width_reduction']
    q['shell_stations']=[[d,w,h*30/28] for d,w,h in p['shell_stations']]
    return legacy_surfaces(q)

def clip_above(z):
    return cq.Workplane('XY').box(240,300,100).val().translate((0,-50,z+50))

def create(p):
    basep=json.loads((ROOT/'cad/parameters_v03.json').read_text())
    # Changing these would violate this revision's frozen-bottom constraint.
    for key in ('length','max_width','grip_width','foot_diameter','foot_thickness','sensor','base_rib_width','base_rib_height'):
        assert p[key]==basep[key],f'{key} is frozen in V0.5; create a new base revision to change it'
    zlock=p['frozen_bottom']['through_z_mm']
    original=cq.importers.importStep(str(ROOT/p['frozen_bottom']['source_step'])).val()
    lower=cq.Workplane('XY').box(240,300,60).val().translate((0,-50,zlock-30))
    bottom=original.intersect(lower)
    above=clip_above(zlock)
    outer,inner=make_surfaces(p)
    skin=outer.cut(inner)
    assert skin.isValid() and len(skin.Solids())==1
    cq.exporters.export(skin,str(ROOT/'.tools/v05_uncut_shell.step'))
    skin=cq.importers.importStep(str(ROOT/'.tools/v05_uncut_shell.step')).val()
    # Outline slots cross only the new upper. Three bridges per key keep it fixed.
    for name in ('left_key','right_key'):
        k=p[name];w=p['key_outline_width']
        mask=rounded_box(k['width'],k['length'],55,4.5,(k['x'],-k['y'],27.5))
        hole=rounded_box(k['width']-2*w,k['length']-2*w,60,4.5-w,(k['x'],-k['y'],27.5))
        ring=mask.cut(hole)
        for dy in (-12,5,17):
            ring=ring.cut(cq.Workplane('XY').box(70,5,70).val().translate((0,-k['y']+dy,25)))
        # Stop on the upper face of the bottom lock, never alter the bottom.
        skin=skin.cut(ring.intersect(above))
    wheel=p['wheel'];wy=-wheel['y'];wz=p['height']+wheel['height_offset']-wheel['diameter']/2
    skin=skin.cut(rounded_box(wheel['opening_width'],wheel['opening_length'],60,2,(wheel['x'],wy,25)).intersect(above))
    unvented=skin.Volume(tol=1e-7);cuts=[]
    domain,layout=cells(p)
    layout_report=manifest(p,domain,layout)
    (ROOT/'reports/v05/vent_layout.json').write_text(json.dumps(layout_report,indent=2),encoding='utf8')
    cutters=[cutter(h).intersect(above) for h in layout]
    for h,tool in zip(layout,cutters):
        skin=skin.cut(tool.copy())
        cuts.append(dict(id=h['id'],seed_xd_mm=h['seed'],area_mm2=h['face'].Area()))
    cq.exporters.export(skin.intersect(above),str(ROOT/'.tools/v05_symmetric_crown.step'))
    vented=skin.Volume(tol=1e-7)
    caps=[];tacks=[];interfaces=[];g=p['grip_width']/2
    guide_checks=[]
    for i,b in enumerate(p['side_buttons']):
        q=p['side_interface']
        pad=yz_round(6,q['reinforcement_length'],q['reinforcement_height'],2.2,(-g+3,-b['y'],b['z'])).intersect(outer.copy())
        guide_checks.append(dict(side_button=i+1,cutters_overlap_mm3=sum(pad.copy().intersect(t.copy()).Volume(tol=1e-7) for t in cutters),minimum_cutter_distance_mm=min(pad.distance(t) for t in cutters)))
        assert guide_checks[-1]['cutters_overlap_mm3']<1e-5,guide_checks[-1]
        skin=skin.fuse(pad).cut(side_window(p,b))
        caps.append(side_cap(p,b))
        for sign in (-1,1):
            tacks.append(cq.Workplane('XY').box(1.2,1.6,4).val().translate((-g+6,-b['y']+sign*6.8,b['z'])))
        interfaces.append(dict(id=i+1,opening_yz_mm=[q['opening_length'],q['opening_height']],cap_yz_mm=[b['length'],q['cap_height']],axial_gap_mm=q['axial_gap']))
    # Exact lower geometry plus a short collar above it creates a volumetric
    # overlap, avoiding unreliable almost-tangent freeform face-only unions.
    skin=skin.intersect(clip_above(zlock))
    print('skin',bounds(skin),skin.Volume(),skin.isValid(),flush=True)
    cq.exporters.export(skin,str(ROOT/'.tools/v05_upper_join.step'))
    cq.exporters.export(bottom,str(ROOT/'.tools/v05_lower_join.step'))
    skin=cq.importers.importStep(str(ROOT/'.tools/v05_upper_join.step')).val()
    bottom=cq.importers.importStep(str(ROOT/'.tools/v05_lower_join.step')).val()
    section=cq.Workplane(obj=original).section(zlock).val()
    collars=[cq.Solid.extrudeLinear(f.outerWire(),f.innerWires(),V(0,0,p['transition_collar_height'])) for f in section.Faces()]
    joined_base=bottom.copy()
    for c in collars:joined_base=joined_base.fuse(c.copy())
    assert joined_base.isValid()
    parts={'frozen_bottom_and_upper_collar':joined_base,'upper_skin_with_guides':skin}
    ws=cq.Solid.makeCylinder(wheel['diameter']/2,wheel['width'],V(wheel['x']-wheel['width']/2,wy,wz),V(1,0,0))
    parts['fixed_wheel']=cq.Workplane(obj=ws).edges().fillet(1).val()
    parts['fixed_wheel_axle']=beam((wheel['x']-7,wy,wz),(wheel['x']+7,wy,wz),2.8)
    # Retain the old leg roots below the locked plane. Upper struts meet those
    # roots and the new, lower axle, instead of shifting any floor anchorage.
    old_wz=31-15/2;old_wy=-17;root_z=zlock-.8
    t=(root_z-2)/(old_wz-2)
    for side in (-1,1):
        root=(side*(12-5*t),-23+6*t,root_z)
        parts[f'wheel_upper_support_{side}']=beam(root,(wheel['x']+side*7,wy,wz),2.8).intersect(clip_above(zlock))
        parts[f'wheel_roof_tie_{side}']=beam((wheel['x']+side*7,wy,wz),(side*10,wy,p['wheel_roof_tie_z']),2.8)
    solid=joined_base.copy()
    for name,shape in list(parts.items())[1:]:
        solid=solid.fuse(shape.copy())
        assert solid.isValid(),name
        print('fused',name,bounds(solid),len(solid.Solids()),flush=True)
    # Freeze every point with Z <= zlock, not just foot-pad coordinates.
    # All new components were clipped at the lock plane before union.
    assert solid.Volume()>15000 and bounds(solid)[5]>25, 'Boolean lost upper volume'
    assert solid.isValid() and len(solid.Solids())==1,('shell',len(solid.Solids()))
    shell=solid.copy()
    for i,c in enumerate(caps):solid=solid.fuse(c.copy());parts[f'fixed_side_cap_{i+1}']=c
    for i,tack in enumerate(tacks):solid=solid.fuse(tack.copy());parts[f'fit_only_cap_tack_{i+1}']=tack
    if not solid.isValid() or len(solid.Solids())!=1:
        cq.exporters.export(solid,str(ROOT/'.tools/v05_debug.step'))
        print('Disconnected FIT:',[(bounds(s),s.Volume()) for s in solid.Solids()],flush=True)
    assert solid.isValid() and len(solid.Solids())==1,('fit',len(solid.Solids()))
    info=dict(vent_count=len(cuts),vents=cuts,vent_guide_checks=guide_checks,unvented_skin_volume_mm3=unvented,vented_skin_volume_mm3=vented,vent_removed_mm3=unvented-vented,side_interfaces=interfaces,frozen_bottom=p['frozen_bottom'])
    # Classifying collisions with the actual final shell avoids double counting
    # overlaps at the frozen-bottom union and strut connections.
    parts={'final_shell_without_side_caps':shell,**{k:s for k,s in parts.items() if k.startswith(('fixed_side_cap','fit_only_cap_tack'))}}
    feet=json.loads((ROOT/'reports/v03/cad_metrics.json').read_text())['feet']
    return solid,shell,caps,outer,parts,feet,info,bottom

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--params',default=str(ROOT/'cad/parameters_v05.json'));args=ap.parse_args()
    p=json.loads(Path(args.params).read_text(encoding='utf8'));start=time.time()
    (ROOT/'.tools').mkdir(exist_ok=True)
    out=ROOT/'exports/v05';out.mkdir(parents=True,exist_ok=True)
    report=ROOT/'reports/v05';report.mkdir(parents=True,exist_ok=True)
    solid,shell,caps,outer,parts,feet,info,bottom=create(p)
    models=[save_model(solid,'quietmirror_fingertip_V0.5_FIT',out),save_model(shell,'quietmirror_fingertip_V0.5_SHELL',out)]
    for i,c in enumerate(caps):
        flat=c.rotate((0,0,0),(0,1,0),90);bb=bounds(flat)
        flat=flat.translate((-(bb[0]+bb[3])/2,-(bb[1]+bb[4])/2,-bb[2]))
        models.append(save_model(flat,f'side_button_{i+1}_V0.5_PRINT',out))
        cq.exporters.export(c,str(ROOT/f'.tools/v05_cap_{i+1}_placed.step'))
        c.exportStl(str(ROOT/f'.tools/v05_cap_{i+1}_placed.stl'),tolerance=.02,angularTolerance=.15,relative=False)
        c.translate((-14,0,0)).exportStl(str(ROOT/f'.tools/v05_cap_{i+1}_exploded.stl'),tolerance=.02,angularTolerance=.15,relative=False)
    assy=cq.Assembly(shell.copy(),name='V0_5_shell',color=cq.Color(.44,.59,.64))
    for i,c in enumerate(caps):assy.add(c.copy(),name=f'side_cap_{i+1}_FIT_PROTOTYPE',color=cq.Color(.9,.57,.23))
    assy.save(str(out/'side_button_assembly_V0.5.step'))
    cq.exporters.export(outer,str(ROOT/'.tools/v05_outer.step'))
    bottom.exportStl(str(ROOT/'.tools/v05_frozen_bottom.stl'),tolerance=.02,angularTolerance=.15,relative=False)
    clearance=[dict(id=i+1,shell_intersection_mm3=shell.copy().intersect(c.copy()).Volume(tol=1e-7),minimum_shell_distance_mm=shell.distance(c)) for i,c in enumerate(caps)]
    assert all(a['shell_intersection_mm3']<1e-5 and a['minimum_shell_distance_mm']>.05 for a in clearance),clearance
    info['cap_to_cap_overlap_mm3']=caps[0].intersect(caps[1]).Volume(tol=1e-7);info['cap_to_cap_distance_mm']=caps[0].distance(caps[1])
    metrics=dict(version='0.5',units='mm',**models[0],models=models,design=info,side_cap_clearance=clearance,feet=feet,parameters=p,build_seconds=time.time()-start)
    (report/'cad_metrics.json').write_text(json.dumps(metrics,indent=2,ensure_ascii=False),encoding='utf8')
    envs=envelope_defs(p)
    # Follow the lower wheel with its independent encoder/middle-switch estimate.
    delta=p['height']+wheel_offset(p)-31
    for e in envs:
        if e['name'] in ('encoder_EST','middle_switch_EST'):
            e['center'][2]+=delta
    hits=[];assy=cq.Assembly(solid.copy(),name='V0_5_fixed_fit',color=cq.Color(.55,.65,.7,.2))
    for e in envs:
        box=cq.Workplane('XY').box(*e['size']).val().translate(e['center']);col=e['color'];rgb=[int(col[i:i+2],16)/255 for i in (1,3,5)]
        assy.add(box,name=e['name'],color=cq.Color(*rgb,.4));eh=[]
        for name,s in parts.items():
            vol=s.intersect(box).Volume(tol=1e-7)
            if vol>.05:eh.append(dict(part=name,overlap_mm3=round(vol,3)))
        hits.append(dict(envelope=e['name'],hits=eh))
    assy.save(str(out/'electronic_envelopes_V0.5_ESTIMATES.step'))
    (report/'envelope_interferences.json').write_text(json.dumps(dict(envelopes=envs,collisions=hits),indent=2,ensure_ascii=False),encoding='utf8')
    print(json.dumps({k:v for k,v in metrics.items() if k not in ('feet','parameters')},indent=2),flush=True)

def wheel_offset(p):return p['wheel']['height_offset']

if __name__=='__main__':main()
