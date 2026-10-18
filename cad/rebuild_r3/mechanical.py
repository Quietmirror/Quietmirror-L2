"""R3 local, reproducible corrections to the archived R2 STEP assembly (mm).

R2 parametric source and exact base files remain in the repository. No geometry
is discarded, smoothed, remeshed, or repaired by closing mesh holes here.
"""
from pathlib import Path
import sys,json,copy,shutil,ctypes,math
import cadquery as cq
import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'cad/rebuild_r2'))
import build as exporter
from mechanics import box,cylinder,beam,join,check

OUT=ROOT/'exports/rebuild_r3';RP=ROOT/'reports/rebuild_r3'
BASE=ROOT/'exports/rebuild_r2';V=cq.Vector

def shape(n):return cq.importers.importStep(str(BASE/f'assembly/{n}.step')).val()
def dump(n,d):
    (RP/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
    ctypes.windll.kernel32.SetPriorityClass(ctypes.c_void_p(-1),0x4000)
    OUT.mkdir(parents=True,exist_ok=True);RP.mkdir(parents=True,exist_ok=True)
    p=json.loads((HERE/'parameters.json').read_text())
    for sub in ('assembly','print','gauges'):
        (OUT/sub).mkdir(exist_ok=True)
        for src in (BASE/sub).glob('*'):
            if src.is_file():shutil.copyfile(src,OUT/sub/src.name)
    met=json.loads((ROOT/'reports/rebuild_r2/cad_metrics.json').read_text())
    d=json.loads((ROOT/'reports/rebuild_r2/design_metadata.json').read_text())
    d['parameters']['version']='R3'
    d['parameters']['main']['travel_deg']=p['main_travel_deg']
    mods={};body=shape('BODY');carrier=shape('WHEEL_CARRIER')
    # Remove material only at the actual positive stops, above the protected
    # Z0..5 feet band; retain every outer key surface and hinge location.
    for m in d['mechanisms']['motions']:
        if m['part'] in ('LEFT_KEY','RIGHT_KEY'):
            m['end_deg']=p['main_travel_deg']
            key=shape(m['part']);ori=m['origin'];axis=[ori[0]+1,*ori[1:]]
            stop_mask=box(7,11,7,(m['actuation_point'][0]/18.3*23,11.5,10.5))
            cut=key.rotate(ori,axis,m['end_deg']).translate((0,0,-.04)).intersect(stop_mask)
            body=body.cut(cut).clean()
            m['stroke_method']='Plane/axis intersection, not vertical displacement; see mating_checks.json.'
        elif m['part']=='WHEEL_CARRIER':
            m['end_deg']=p['middle_travel_deg']
            ori=m['origin'];axis=[ori[0]+1,*ori[1:]]
            cut=carrier.rotate(ori,axis,m['end_deg']).translate((0,0,-.03)).intersect(box(2,5,8,(-4.35,41.5,14)))
            body=body.cut(cut).clean()
        elif m['part'].startswith('SIDE_'):
            m['assembly']='Install switch and removable clamp first; insert side cap from exterior, then capture pin from above.'
    # USB connector stays exactly where R2 put it. Only the hypothetical
    # adapter outline/holes and printed support posts move. M2 heads/washers
    # now clear the connector and the encoder daughterboard.
    pcb=box(20,10,1,(0,15,8.5))
    threads=[];hardware={}
    for label,x in [('L',7.8),('R',-7.8)]:
        cy=13.
        post=cylinder(2.8,2.4,(x,cy,5.6))
        bridge=beam((x,cy,6.8),(x,17.5,6.8),1.35)
        body=join(body,post,bridge).cut(cylinder(.85,3.2,(x,cy,5.4))).clean()
        pcb=pcb.cut(cylinder(1.2,2,(x,cy,7.5)))
        hardware[f'USB_M2x3_{label}']=join(cylinder(1.,3,(x,cy,6.3)),cylinder(1.9,1.6,(x,cy,9.3)))
        hardware[f'USB_WASHER_{label}']=cylinder(2.5,.3,(x,cy,9.)).cut(cylinder(1.1,.5,(x,cy,8.9)))
        threads.append(dict(screw=f'USB_M2x3_{label}',host='BODY',center=[x,cy,7.15],diameter_mm=2.02,height_mm=1.71,
            reason='Intended M2 engagement in the 1.7mm printed pilot; all other intersections remain failures.'))
    # Recut the level PCB seat after adding bridges; no base plane is added.
    body=body.cut(box(20.4,10.4,20,(0,15,18))).clean()
    mods['BODY']=check(body,'R3_BODY')
    mods['USB_ADAPTER_PCB_REFERENCE']=check(pcb,'USB_PCB')
    d['interfaces']['usb'].update(adapter_pcb_width_depth_thickness_mm=[20,10,1],adapter_holes_mm=[[7.8,13],[-7.8,13]],
        mount='R3 custom adapter only: M2x3 with 0.3mm washers; nominal 1.7mm pilot engagement. Purchased PCB must match or use a redesigned adapter.')
    # Encoder pins pass through the R2 cradle into a separate 1.2mm board.
    # PCB top=10.4; tips end at8.5, giving0.7mm below PCB for solder.
    # This is a proposed custom outline, never a machining instruction for
    # an existing populated donor board.
    epcb=box(12.2,15.1,1.2,(5.3,28.35,9.8))
    epcb=epcb.cut(box(3.0,8.5,3,(12.1,26.2,9.8)))
    epcb=epcb.cut(box(7.0,5.0,3,(1.4,37.3,9.8)))
    for yy in (25.5,28.,30.5):epcb=epcb.cut(cylinder(.625,3,(3.75,yy,8.5)))
    for yy in (22.6,33.4):epcb=epcb.cut(box(2.35,1.95,3,(5.75,yy,9.8)))
    for label,x,y in [('FRONT',8.5,26.1),('REAR',1.3,32.5)]:
        boss=cylinder(2.6,1.8,(x,y,10.4))
        carrier=join(carrier,boss).cut(cylinder(.85,2.5,(x,y,10.2))).clean()
        epcb=epcb.cut(cylinder(1.15,3,(x,y,8.5)))
        hardware[f'ENCODER_M2x3_{label}']=join(cylinder(1.,3.,(x,y,8.9)),cylinder(1.9,1.6,(x,y,7.3)))
        hardware[f'ENCODER_WASHER_{label}']=cylinder(2.1,.3,(x,y,8.9)).cut(cylinder(1.1,.5,(x,y,8.8)))
        threads.append(dict(screw=f'ENCODER_M2x3_{label}',host='WHEEL_CARRIER',center=[x,y,11.15],diameter_mm=2.02,height_mm=1.51,
            reason='Intended M2 engagement in printed pilot; the washer and PCB seat are not excluded.'))
    # Boss additions must not refill the encoder terminal passages.
    for yy in (25.5,28.,30.5):carrier=carrier.cut(cylinder(.625,5,(3.75,yy,8.5)))
    for yy in (22.6,33.4):carrier=carrier.cut(box(2.35,1.95,5,(5.75,yy,10.5)))
    mods['WHEEL_CARRIER']=check(carrier.clean(),'R3_CARRIER')
    hardware['ENCODER_ADAPTER_PCB_EST']=check(epcb,'ENCODER_PCB')
    mods.update(hardware)
    for m in d['mechanisms']['motions']:
        if m['part']=='WHEEL_CARRIER':
            m['moving_hardware'].extend([n for n in hardware if n.startswith('ENCODER_')])
        q=np.array(m['actuation_point']);gap=m['nominal_actuator_gap_mm']
        if m['kind']=='translate':
            normal=-np.array(m['end_vector'])/np.linalg.norm(m['end_vector']);mat=np.eye(4);mat[:3,3]=m['end_vector']
        else:
            a=math.radians(m.get('switch_tilt_deg',0));normal=np.array([0,-math.sin(a),math.cos(a)])
            mat=trimesh.transformations.rotation_matrix(math.radians(m['end_deg']),m['axis'],m['origin'])
        tip=q-gap*normal;qp=mat[:3,:3]@q+mat[:3,3];nn=mat[:3,:3]@normal
        m['calculated_contact_travel_mm']=float(np.dot(nn,tip-qp)/np.dot(nn,normal))
        m['travel_evidence']='Estimated free plunger height; exact moved actuator-plane/fixed-axis intersection. Actual PT/OP/OT still require measurement.'
    d['mechanisms']['main_hinges']=[copy.deepcopy(m) for m in d['mechanisms']['motions'] if m['part'] in ('LEFT_KEY','RIGHT_KEY')]
    d['mechanisms']['wheel']['encoder_board']=dict(outline_bbox_mm=[12.2,15.1,1.2],bottom_z_mm=9.2,top_z_mm=10.4,
        mount_centers_mm=[[8.5,26.1],[1.3,32.5]],solder_tail_below_board_mm=.7,
        source='Proposed custom adapter with edge relief; not a purchased PCB.')
    d['thread_engagements']=threads
    d['r3_scope']='Mechanical corrections + explicitly estimated electronic scenarios. No actual donor PCB fit or electrical function claim.'
    exporter.OUT=OUT;exporter.REPORT=RP;exporter.CACHE=ROOT.parent/'_support/work/fenrir_rebuild_r3/build'
    exporter.CACHE.mkdir(parents=True,exist_ok=True)
    for n,s in mods.items():
        printable=met[n]['printable'] if n in met else False
        exporter.export(n,s,printable,met);print('Exported',n,flush=True)
    comp=cq.Compound.makeCompound([cq.importers.importStep(str(OUT/f'assembly/{n}.step')).val() for n,v in met.items() if v['printable']])
    cq.exporters.export(comp,str(OUT/'FENRIR_MINISE_R3_MECHANICAL.step'))
    dump('cad_metrics.json',met);dump('design_metadata.json',d)
    dump('change_scope.json',dict(base='R2',modified=list(mods),unchanged_parts=[n for n in met if n not in mods],
        bottom_band_preserved='Check exact symmetric-difference below Z5; not inferred from parameters.',
        primary_keys='Touch surfaces, dimensions, hinges and caps are byte-identical R2 exports. Only their fixed stop relief is changed.'))
    print('R3 MECHANICAL COMPLETE',flush=True)

if __name__=='__main__':main()
