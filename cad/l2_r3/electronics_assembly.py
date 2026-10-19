"""Estimated H/D electronic packages and individually named assembly components."""
import json
from common import *
def cb(size,center):
    d=size;c=center;return box(c[0]-d[0]/2,c[0]+d[0]/2,c[1]-d[1]/2,c[1]+d[1]/2,c[2]-d[2]/2,c[2]+d[2]/2)
def main():
    data=json.loads((ROOT/'cad/rebuild_r3_2/electronics.json').read_text())
    refs={};envelopes=[]
    skip={'SIDE_IO_PCB_EST','SIDE_HEADER_EST'}
    for row in data['custom']:
        if row['name'] in skip:continue
        refs[row['name']]=cb(row['size'],row['center']);envelopes.append(dict(row,status='ESTIMATED_PACKAGE_NOT_VENDOR_GEOMETRY'))
    # The unchanged original USB adapter STEP is superseded by this enlarged
    # R3-compatible custom board, using actual proposed interface hole centers.
    refs['USB_ADAPTER_PCB_REFERENCE']=cb([20,10,1],[0,15,8.5])
    for x in [-7.8,7.8]:refs['USB_ADAPTER_PCB_REFERENCE']=refs['USB_ADAPTER_PCB_REFERENCE'].cut(cyl(1.2,3,(x,13,7)))
    # Retain the inherited encoder terminals and fastener holes. A tiny
    # nonfunctional corner of this proposed PCB outline hit BODY at 4.1 deg.
    # Trim only the local clash box plus 0.30 clearance, in board coordinates.
    original=baseline('ENCODER_ADAPTER_PCB_EST');origin=(0,50,19);axis=(1,50,19)
    moved=original.rotate(origin,axis,4.1);hit=moved.intersect(load('BODY'))
    encoder_correction=dict(original_end_pose_overlap_mm3=vol(hit),outline_trim_applied=False)
    if hit.Solids():
        b=hit.BoundingBox();tool=box(b.xmin-.3,b.xmax+.3,b.ymin-.3,b.ymax+.3,b.zmin-.3,b.zmax+.3).rotate(origin,axis,-4.1)
        refs['ENCODER_ADAPTER_PCB_EST']=valid(original.cut(tool).clean(),'ENCODER_ADAPTER_PCB_EST')
        encoder_correction.update(outline_trim_applied=True,collision_bounds=bounds(hit),remaining_volume_mm3=vol(refs['ENCODER_ADAPTER_PCB_EST']),description='Local clearance notch in hypothetical custom board; no real donor PCB cutting instruction')
    else:refs['ENCODER_ADAPTER_PCB_EST']=original
    save('encoder_outline_correction.json',encoder_correction)
    # Existing estimated power switch/actuator package is retained in custom.
    from mechanics import beam
    for row in data.get('routes',[]):
        if row['name']=='SIDE_ROUTE_EST':
            points=[(15.2,64,18.8),(13.8,64,20.4),(11,57,20.4)]
        else:points=row['points']
        refs[row['name']]=unite(*[beam(a,b,row['radius']) for a,b in zip(points[:-1],points[1:])])
    for row in data.get('reserves',[]):
        cq.exporters.export(cb(row['size'],row['center']),str(OUT/'reference'/(row['name']+'.step')))
    feet=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text())['mechanisms']['feet']
    for i,f in enumerate(feet,1):refs[f'SKATE_{i}_0p8']=cyl(3.7,.8,(*f['center'],4.4))
    for n,s in refs.items():export(s,n,False)
    allparts={p.stem:load(p.stem,p.parent) for p in (OUT/'parts').glob('*.step')}
    reserve_names={r['name'] for r in data.get('reserves',[])}
    hardware={p.stem:load(p.stem,p.parent) for p in (OUT/'reference').glob('*.step') if 'F2_TRIAL' not in p.name and p.stem not in reserve_names and not p.stem.startswith('ATK_')}
    assy=cq.Assembly(name='Quietmirror_L2_r3_H_INCOMPLETE')
    for n,s in {**allparts,**hardware}.items():
        color=(.76,.8,.84) if n in allparts else (.2,.6,.4)
        if n.startswith('SIDE_') and n.endswith('_KEY'):color=(.9,.54,.25)
        assy.add(s,name=n,color=cq.Color(*color))
    assy.save(str(OUT/'FULL_ASSEMBLY_H.step'))
    # The donor outline is explicitly an estimated keepout, no invented holes.
    donor=data.get('donor',[])
    if isinstance(donor,dict):donor=[donor] if 'size' in donor else donor.get('components',[])
    drefs={}
    for row in donor:
        if 'size' in row and 'center' in row:drefs[row['name']]=cb(row['size'],row['center'])
    if not drefs:drefs['ATK_A1_PLUS_UNCONFIRMED_BOARD_ENVELOPE']=cb([42,44,1.2],[0,53,14.8])
    das=cq.Assembly(name='Quietmirror_L2_r3_D_PLACEHOLDER')
    for n,s in {**allparts,**drefs}.items():das.add(s,name=n)
    das.save(str(OUT/'FULL_ASSEMBLY_D_PLACEHOLDER.step'))
    for n,s in drefs.items():cq.exporters.export(s,str(OUT/'reference'/(n+'.step')))
    save('electronic_envelopes.json',dict(H=envelopes,D_status='DONOR_ID_PENDING_USER_CONFIRMATION / PCB_GEOMETRY_UNVERIFIED / FIT_NOT_CERTIFIED',donor_user_name='ATK A1 Plus',H_component_count=len(hardware),coordinates='mm; @ interpreted as geometric center',functional_status={k:'UNVERIFIED' for k in ['400-6400DPI','1000Hz wireless','no sync technologies','macros','adjustable LOD','low latency','charging','12h full power endurance']},battery_requirement='Capacity >= 12*h average_current_mA / usable_fraction; no measured current or capacity supplied',optics='Lens height and focal datum require real package and lens; global Z axis points normal to pad'))
    save('assembly_inventory.json',dict(printable=list(allparts),H_hardware=list(hardware),D_reference=list(drefs)))
    print('H and D component assemblies exported',flush=True)
if __name__=='__main__':main()
