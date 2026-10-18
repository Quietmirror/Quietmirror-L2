"""Independent r2 diagnostic BRep checks; never imports baseline builders.

Underdetermined bridge and PCB seat positions are exposed as diagnostic
assumptions. This is not a final production or electronics-fit release.
"""
from pathlib import Path
import json, math
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/l2_r2';EXP=ROOT/'exports/l2_r2_diagnostic'
V=cq.Vector
def save(n,d):(OUT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
def box(x0,x1,y0,y1,z0,z1):
    assert min(x1-x0,y1-y0,z1-z0)>0
    return cq.Solid.makeBox(x1-x0,y1-y0,z1-z0,V(x0,y0,z0))
def vol(s):
    if not s.Solids():return 0.
    p=GProp_GProps();BRepGProp.VolumeProperties_s(s.wrapped,p,1e-8,True,False);return p.Mass()
def bounds(s):
    b=s.BoundingBox();return [b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]
def load(n):return cq.importers.importStep(str(ROOT/f'exports/rebuild_r3_2/assembly/{n}.step')).val()
def reference(n):
    p=EXP/'support_reference'/n
    if not p.exists():p=ROOT/'_support/work/independent'/n
    return cq.importers.importStep(str(p)).val()
def capsule(p,q,r):
    p=V(*p);q=V(*q);d=q-p
    return cq.Solid.makeCylinder(r,d.Length,p,d.normalized()).fuse(cq.Solid.makeSphere(r,p),cq.Solid.makeSphere(r,q))
def checkpair(a,b,an,bn,minimum=.5,kind='clearance'):
    d=a.distance(b);intersection=vol(a.intersect(b))
    return dict(pair=[an,bn],distance_mm=d,intersection_mm3=intersection,
                minimum_mm=minimum,kind=kind,passed=(intersection<=.001 and d>=minimum-1e-6) if kind=='clearance' else None)
def export(s,name):
    path=EXP/(name+'.step');cq.exporters.export(s,str(path));r=cq.importers.importStep(str(path)).val()
    row=dict(name=name,valid=r.isValid(),solids=len(r.Solids()),volume_mm3=vol(r))
    assert row['valid'];return row

def carrier_geometry():
    floor=box(17.3,25.5,41,71.2,12.1,13.7).cut(box(25.2,26,40,41.6,11,15))
    wall=box(17.3,18.5,41,71.2,12.1,19.5)
    divider=box(17.3,25.5,54.95,55.75,13.7,19.5)
    stops=[box(25.5,29.74,53.8,55.6,13.4,16.4),box(26,30.04,58,60,13.4,16.4)]
    extensions=[box(25.2,26.8,53.8,55.6,12.1,13.7),box(25.2,26.8,58,60,12.1,13.7)]
    legs=[];bridges=[];collars=[]
    for x,y,z,limit in ((27.331,43,10.8,29),(28.604,66.8,10.525,30.1)):
        clip=box(10,limit,35,75,9,15)
        legs.append(cq.Solid.makeCylinder(2,12.1-z,V(x,y,z)).intersect(clip))
        bridges.append(box(24.5,limit,y-2,y+2,12.1,13.7))
        collars.append(cq.Solid.makeCylinder(2,.6,V(x,y,11.8)).intersect(clip))
    # Diagnostic choice: two 2x1.6 seats at PCB ends; terminal geometry unknown.
    seats=[box(16.2,17.5,y-1,y+1,14.1,15.7) for y in (45,69)]
    base=floor.fuse(wall,divider,*stops,*legs).clean()
    assembled=base.fuse(*extensions,*bridges,*collars,*seats).clean()
    before_drill=assembled
    for x,y in ((27.331,43),(28.604,66.8)):
        assembled=assembled.cut(cq.Solid.makeCylinder(1.2,6,V(x,y,9)))
    assembled=assembled.clean()
    return dict(carrier=assembled,base=base,undrilled=before_drill,floor=floor,wall=wall,
                divider=divider,stops=stops,extensions=extensions,legs=legs,
                bridges=bridges,collars=collars,seats=seats)

def layout(body,meta):
    c=carrier_geometry();front=box(18.5,25,41.85,54.65,13.7,19.5)
    rear=box(19,25.5,56.05,68.85,13.7,19.5);pcb=box(15.2,16.2,44,70,13.3,18.8)
    main_hinge=body.intersect(box(25.2,30,36,43.3,11,22))
    sensor_tab=body.intersect(box(9.4,15.6,50.6,59.4,10.3,12.9))
    foot=next(f for f in meta['feet'] if abs(f['center'][0]-24.84)<.01 and abs(f['center'][1]-62.64)<.01)
    strut=capsule((24.84,62.64,7.4),foot['upper_connection'],1.7).intersect(body)
    inner=reference('MOTHER_INNER_FROM_R32_SURFACE.step')
    outer=reference('MOTHER_OUTER_FROM_R32_SURFACE.step')
    # Unperforated mother skin is conservative for the low bridge/leg region.
    skin=outer.cut(inner).intersect(box(10,40,35,75,9,14.5))
    pairs=[checkpair(c['stops'][0],front,'SF_stop','SF_switch'),checkpair(c['stops'][1],rear,'SR_stop','SR_switch'),
           checkpair(front,main_hinge,'SF_switch','main_outer_hinge'),checkpair(pcb,sensor_tab,'SIDE_IO_PCB','sensor_tab'),
           checkpair(c['legs'][1],strut,'rear_leg','rear_foot_strut'),
           checkpair(c['bridges'][0],main_hinge,'front_bridge','main_outer_hinge'),
           checkpair(c['carrier'],front,'carrier','SF_switch',0,'intentional seat and wall contacts'),
           checkpair(c['carrier'],rear,'carrier','SR_switch',0,'intentional seat contact; back wall gap to check'),
           checkpair(c['carrier'],pcb,'carrier','SIDE_IO_PCB',0,'intended PCB seat contact')]
    for i in (0,1):
        for key in ('legs','bridges'):
            pairs.append(checkpair(c[key][i],skin,('front' if i==0 else 'rear')+'_'+key,'low_mother_skin'))
        pairs.append(checkpair(c['extensions'][i],[front,rear][i],f'extension_{i+1}',f'switch_{i+1}'))
    connections=[]
    for i in (0,1):
        for an,a,bn,b in [('stop',c['stops'][i],'extension',c['extensions'][i]),
                          ('bridge',c['bridges'][i],'floor',c['floor']),
                          ('collar',c['collars'][i],'leg',c['legs'][i]),
                          ('collar',c['collars'][i],'bridge',c['bridges'][i])]:
            v=vol(a.intersect(b));connections.append(dict(index=i+1,pair=[an,bn],positive_overlap_mm3=v,passed=v>1e-6))
    for i,s in enumerate(c['seats']):
        connections.append(dict(index=i+1,pair=['PCB_seat','wall'],positive_overlap_mm3=vol(s.intersect(c['wall'])),passed=vol(s.intersect(c['wall']))>1e-6))
    raw_context=[checkpair(c['carrier'],body,'new_carrier','unchanged_R32_BODY',0,'context contains obsolete side sockets; not final L2 collision result'),
                 checkpair(pcb,body,'SIDE_IO_PCB','unchanged_R32_BODY',0,'context contains obsolete side sockets; not final L2 collision result')]
    rows=[export(c['carrier'],'R2_CARRIER_DIAGNOSTIC'),export(front,'SF_SWITCH_ENVELOPE'),export(rear,'SR_SWITCH_ENVELOPE'),export(pcb,'SIDE_IO_PCB_ENVELOPE')]
    export(cq.Compound.makeCompound([c['carrier'],front,rear,pcb]),'R2_SIDE_LAYOUT_DIAGNOSTIC')
    export(skin,'LOW_MOTHER_SKIN_REFERENCE');export(main_hinge,'MAIN_OUTER_HINGE_REFERENCE');export(strut,'REAR_FOOT_STRUT_REFERENCE')
    report=dict(status='DIAGNOSTIC_ONLY_NOT_PRINTABLE_RELEASE',parts=rows,pairs=pairs,connections=connections,
                raw_R32_context=raw_context,carrier_solid_count=len(c['carrier'].Solids()),carrier_valid=c['carrier'].isValid(),
                added_connection_volume_mm3=vol(c['undrilled'])-vol(c['base']),
                rear_switch_to_back_wall_mm=rear.distance(c['wall']),
                assumptions=['t_H=0 for diagnostic carrier. Actual adapter thickness remains a parameter.',
                             'Bridges centered at leg Y, width 4; collar overlaps leg top and bridge by 0.3 each.',
                             'PCB seats X16.2..17.5, Y44..46 and 68..70, Z14.1..15.7.',
                             'M2 clearance holes are nominal diameter 2.4 from baseline parameters.',
                             'Terminal slots, two 4x8 windows, PCB retention features and fillets lack full placement dimensions and are omitted.',
                             'No old BODY material was hard-cut to make a fit. Final rebuilt BODY and insertion remain unverified.'],
                release_gate=all(r['passed'] for r in pairs if r['kind']=='clearance'))
    save('K9_r2_layout.json',report)
    print('K9 carrier solids',report['carrier_solid_count'],'clearance gate',report['release_gate'],flush=True)
    for r in pairs:print(r['pair'],r['distance_mm'],r['intersection_mm3'],flush=True)

def datum(body):
    faces=[]
    for f in body.Faces():
        if f.geomType()!='PLANE':continue
        b=f.BoundingBox()
        if b.zmax-b.zmin<1e-5 and abs((b.zmax+b.zmin)/2-5)<1e-5 and f.normalAt().z<-.9:
            faces.append(dict(area_mm2=f.Area(),bounds=bounds(f)))
    # Probe annuli exclude the existing screw bores; enumerate actual top faces.
    ears=[]
    for x,y,target in ((27.331,43,10.8),(28.604,66.8,10.525)):
        found=[]
        for f in body.Faces():
            if f.geomType()!='PLANE':continue
            b=f.BoundingBox()
            if b.zmax-b.zmin>1e-5 or not 9<b.zmin<12 or f.normalAt().z<.9:continue
            hit=f.intersect(cq.Solid.makeCylinder(1.9,4,V(x,y,9)))
            if hit.Area()>1e-6:found.append(dict(z=(b.zmin+b.zmax)/2,area_in_probe_mm2=hit.Area()))
        ears.append(dict(center=[x,y],document_top_z=target,candidate_top_faces=found,
                         no_adapter_leg_height=12.1-target,positive_height_requires_tH_less_than=12.1-target,
                         conditional_examples=[dict(tH=t,leg_height_mm=12.1-target-t,positive_height=12.1-target-t>0) for t in (0,.5,1,1.3,1.6)]))
    save('DATUM_and_stack.json',dict(edge_down_faces=faces,total_edge_area_mm2=sum(f['area_mm2'] for f in faces),
                                   foot_bond_plane=5.2,default_skate_thickness=.8,mat_plane_z=4.4,edge_clearance_mm=.6,
                                   edge_clearance_formula='skate_thickness - 0.2; minimum 0.5 requires thickness >=0.7',ears=ears))

def arithmetic():
    rows=[]
    for name,y0,y1,h,py in [('SF',44.2,56.3,45,50.25),('SR',58.1,70.8,70,64.45)]:
        L=y1-y0;arm=abs(py-h);far=max(abs(y0-h),abs(y1-h));edge=y0+L/4 if name=='SF' else y1-L/4
        rows.append(dict(name=name,length_mm=L,arm_mm=arm,hinge_quarter_force_ratio=arm/(L/4),
                         edge_quarter_force_ratio=arm/abs(edge-h),center_force_ratio=1.,far_force_ratio=arm/far,
                         pure_Y_stop_deg=math.degrees(math.asin(.6/arm)),far_end_travel_mm=far*.6/arm,
                         eccentricity_y_mm=0.,eccentricity_z_mm=-.9,
                         angular_sensitivity=[dict(plunger_minus_pivot_x_mm=dx,delta_x_at_nominal_angle_mm=dx*(1-math.cos(math.asin(.6/arm)))+.6) for dx in (-3,-1,0,1,3)],
                         status='Arithmetic checked; full rigid-body trigger/stop requires pivot X, switch FP/OP/TTP and compliance'))
    delta=sum([-227,-49.5,-970,-385.8,640,77,-48,45,-136,-261,-109,45,60,65])
    save('K8_K10_r2_arithmetic.json',dict(keys=rows,budget_delta_mm3=delta,budget_mm3=18506.67821844789+delta,
                                       budget_pa12_g=(18506.67821844789+delta)*.00101,final_mass_measured=False))

def groups(body,meta):
    inner=reference('MOTHER_INNER_FROM_R32_SURFACE.step')
    region=body.intersect(inner).clean();ss=sorted(region.Solids(),key=vol,reverse=True)
    names=['lower_chassis_and_old_side_seats','Y54_arms_and_wheel_hub','Y67_5_cross_tie',
           'positive_X_inner_main_hinge','negative_X_inner_main_hinge','rear_negative_X_mount_bridge',
           'positive_X_outer_main_hinge','negative_X_outer_main_hinge',
           'rear_center_support_segment_A','rear_foot_segment_B','rear_foot_segment_C','rear_center_support_segment_D']
    actions=['MIXED: retain feet/struts/USB/sensor interfaces; remove only source-defined old side seats',
             'MIXED: remove Y54 outer arms only; retain central wheel hub and pin path',
             'KEEP: rear cross-tie and its shell load path']+['KEEP']*9
    f=meta['feet'][4];tube=capsule((0,f['center'][1],6.81),f['upper_connection'],1.8)
    pad=cq.Solid.makeCylinder(4,1.6,V(0,f['center'][1],5.2));rear_ref=tube.fuse(pad)
    rows=[]
    for i,s in enumerate(ss):
        v=vol(s);hit=vol(s.intersect(rear_ref))
        rows.append(dict(id=i+1,name=names[i] if i<len(names) else 'UNCLASSIFIED',volume_mm3=v,bounds=bounds(s),
                         action=actions[i] if i<len(actions) else 'REVIEW',rear_foot_reference_overlap_mm3=hit,
                         rear_foot_reference_fraction=hit/v,valid=s.isValid()))
    assert len(rows)==12,'Baseline decomposition changed: inspect before assigning labels'
    save('K5_r2_disposition.json',dict(method='Independent BRep cavity intersection; groups are geometric regions, not detached printed parts',
                                     parts=rows,source_files=['cad/rebuild_r2/mechanics.py','cad/rebuild_r3_2/build.py'],
                                     disposition_is_not_final_rebuild_validation=True))
    inherited=json.loads((ROOT/'reports/l2_r1/K6_source_openings.json').read_text(encoding='utf8'))
    save('K6_r2_crosscheck.json',dict(prior_evidence='../l2_r1/K6_source_openings.json',
                                   result='r2 coordinates/actions agree with independent r1 evidence; BODY not modified',
                                   openings=inherited['openings'],source_method='Remove obsolete cutter generation at source; retain six window boundary and wheel pin access',
                                   unresolved_text='Section 3.1 item 3 mentions expanded patches, while 2.1 specifies source-level removal. Prefer source-level reconstruction; do not fill finished BODY blindly.'))

def main():
    OUT.mkdir(exist_ok=True);EXP.mkdir(exist_ok=True)
    b=load('BODY');m=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text(encoding='utf8'))['mechanisms']
    arithmetic();datum(b);print('datum complete',flush=True)
    groups(b,m);print('groups complete',flush=True)
    layout(b,m)

if __name__=='__main__':main()
