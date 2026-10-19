"""Local functional contact accounting over measured final-component pairs.

This does not turn a whole BODY/part pair into an exception. Raw common volume
is retained; named construction features and their declared clearance collars
are separated from the remaining fixed material. Unrecognized failures fail.
"""
import itertools,json
from common import *
from side_module import KEYS,RETAINER_MOUNTS

def collar(feature,d):
    boxes=[]
    for solid in feature.Solids():
        b=solid.BoundingBox()
        boxes.append(box(b.xmin-d,b.xmax+d,b.ymin-d,b.ymax+d,b.zmin-d,b.zmax+d))
    if not boxes:raise RuntimeError('Empty functional construction feature')
    return unite(*boxes)

def mate(actor,fixed,feature,actor_name,fixed_name,required,label,raw):
    mask=collar(feature,required+.00001)
    rest=fixed.cut(mask)
    check=pair(actor,rest,actor_name,fixed_name,required)
    return dict(classification=label,source_feature_bounds_mm=[bounds(s) for s in feature.Solids()],
        seam_collar_mm=required,nonfunctional=check,
        passed=raw['overlap_mm3']<=.001 and check['pass_check'],
        note='Collar accounts only for continuous geometry next to the named mating feature; full-solid overlap must still pass.')

def rigid_housing(shape,mo):
    pt=mo['actuation_point'];axis=[pt[0]+1,*pt[1:]];tilt=mo.get('switch_tilt_deg',0)
    return shape.rotate(pt,axis,-tilt).intersect(box(-50,50,0,90,0,pt[2]-1.03)).rotate(pt,axis,tilt)

def main():
    inv=json.loads((RP/'assembly_inventory.json').read_text());parts={n:load(n) for n in inv['printable']}
    hw={n:load(n,OUT/'reference') for n in inv['H_hardware']};allparts={**parts,**hw}
    body=parts['BODY'];features={p.stem:cq.importers.importStep(str(p)).val() for p in (OUT/'validation_features').glob('*.step')}
    motion=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text())['mechanisms']['motions']
    motions={m['part']:m for m in motion if m['part'] in ['LEFT_KEY','RIGHT_KEY','WHEEL_CARRIER']}
    raw=json.loads((RP/'static_pairs.json').read_text())+json.loads((RP/'component_pairs.json').read_text())
    rows=[]
    for r in raw:
        an,bn=r['a'],r['b'];a,b=allparts[an],allparts[bn];audit=dict(raw=r,passed=r['pass_check'],classification='ordinary clearance')
        if r['pass_check']:rows.append(audit);continue
        required=r['required_mm']
        if an=='BODY' and bn in ['SIDE_FRONT_KEY','SIDE_REAR_KEY']:
            audit.update(classification='D7 outward stop; independently decomposed in side_functional_motion.json',passed=False,dependent_gate='side_functional_motion')
        elif an=='BODY' and bn in ['SF_RETAINER','SR_RETAINER']:
            short=bn[:2];m=RETAINER_MOUNTS[short]
            ya,yb=(41.8,55.) if short=='SF' else (55.3,71.2)
            foot=body.intersect(unite(box(14.3,19.5,ya-.1,yb+.1,12.1,13.7),cyl(1.5,1.6,(m['pin_x'],m['pin_y'],12.1)),cyl(2.05,1.6,(m['x'],m['y'],12.1))))
            audit.update(mate(b,a,foot,bn,an,.3,'retainer floor seat and integral locating-pin socket',r))
        elif an=='BODY' and bn=='WHEEL_CARRIER':
            f=features['WHEEL_CARRIER_FIXED_BEARINGS'];audit.update(mate(b,a,f,bn,an,.3,'wheel click hinge axial endplay',r))
            audit['axial_endplay_mm']=r['gap_mm'];audit['passed'] &= .20-1e-5<=r['gap_mm']<=.35+1e-5
        elif an=='WHEEL' and bn=='WHEEL_CARRIER':
            f=b.intersect(cyl(2.81,2.42,(-6.71,28.,19.),(1,0,0)))
            audit.update(mate(a,b,f,an,bn,.3,'wheel round-axle journal, diameter2.0/2.35',r))
            audit['radial_clearance_mm']=r['gap_mm'];audit['passed'] &= abs(r['gap_mm']-.175)<.01
        elif an=='BODY' and bn.startswith('SWITCH_') and bn+'_MOUNT' in features:
            audit.update(mate(b,a,features[bn+'_MOUNT'],bn,an,.5,'source-defined tilted/flat micro socket and transverse bolt holders',r))
        elif an=='BODY' and bn in ['SF_D2F_01F','SR_D2F_01F']:
            floor=body.intersect(box(17.3,25.5,41.8,71.2,12.1,13.7))
            divider=body.intersect(box(19.,25.5,54.95,55.75,13.7,19.5))
            audit.update(mate(b,a,unite(floor,divider),bn,an,.5,'side micro planar seat and end-positioning divider',r))
            guide=pair(b,divider,bn,'MOUNT_END_GUIDE',.3)
            audit['end_guide']=guide;audit['passed'] &= guide['pass_check']
        elif an in ['SF_RETAINER','SR_RETAINER'] and bn==an[:2]+'_D2F_01F':
            ya,yb=(41.8,55.) if an.startswith('SF') else (55.3,71.2)
            f=a.intersect(box(17.3,19.0,ya,yb,13.7,19.5))
            audit.update(mate(b,a,f,bn,an,.5,'backplate clamp against corresponding micro; terminal relief slots retained',r))
        elif an=='BODY' and bn=='USB_ADAPTER_PCB_REFERENCE':
            f=a.intersect(box(-10.6,10.6,9.6,20.5,5.4,8.000001))
            audit.update(mate(b,a,f,bn,an,.5,'USB adapter lower face on raised local posts',r))
        elif an in motions and bn==motions[an]['switch']:
            check=pair(a,rigid_housing(b,motions[an]),an,bn+'_RIGID',.3)
            audit.update(classification='matching compressible micro plunger at rest',rigid_housing=check,
                         passed=r['overlap_mm3']<=.001 and -.00001<=r['gap_mm']<=.031 and check['pass_check'])
        elif an=='WHEEL_CARRIER' and bn in ['ENCODER_ADAPTER_PCB_EST','ENCODER_EC10E_HOUSING']:
            f=a.intersect(box(1.4,8.7,19.9,36.1,10.399999,12.000001))
            audit.update(mate(b,a,f,bn,an,.3,'encoder terminal cradle / PCB seating surface in moving assembly',r))
        elif an=='WHEEL' and bn=='ENCODER_EC10E_HOUSING':
            audit.update(classification='wheel-to-encoder axial face running clearance',passed=r['overlap_mm3']<=.001 and .2<=r['gap_mm']<=.35)
        elif an=='WHEEL' and bn=='ENCODER_EC10E_ROTOR':
            audit.update(classification='mated AF1.67/1.73 hex drive; rotor co-rotates with wheel',passed=r['overlap_mm3']<=.001 and abs(r['gap_mm']-.03)<.001)
        else:audit.update(classification='UNRESOLVED ordinary-clearance failure',passed=False)
        rows.append(audit)
        if not audit['passed']:print('CONTACT_REVIEW',an,bn,audit,flush=True)
        save('functional_static_contacts.json',dict(rows=rows,passed=False,scope='Partial while running; dependent D7 checks resolved after completion'))
    side_path=RP/'side_functional_motion.json'
    if side_path.exists():
        sides={x['part']:x for x in json.loads(side_path.read_text())}
        for row in rows:
            if row.get('dependent_gate')=='side_functional_motion':row['passed']=bool(sides[row['raw']['b']]['passed'])
    save('functional_static_contacts.json',dict(rows=rows,passed=all(x['passed'] for x in rows)))

if __name__=='__main__':main()
