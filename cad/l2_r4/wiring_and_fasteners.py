"""All remaining printed/hardware intersections and local wire terminations."""
import json
from common import *
from side_module import RETAINER_MOUNTS
from assemble import ROUTES
from wire_layout import definition as wire_definition

def lower_bound(a,b):
    aa,bb=a.BoundingBox(),b.BoundingBox()
    return float(np.linalg.norm([max(0.,getattr(aa,c+'min')-getattr(bb,c+'max'),getattr(bb,c+'min')-getattr(aa,c+'max')) for c in 'xyz']))

def main():
    inv=json.loads((RP/'assembly_inventory.json').read_text());parts={n:load(n) for n in inv['printable']}
    hw={n:load(n,OUT/'reference') for n in inv['H_hardware']};meta=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text())
    threads={}
    for t in meta['thread_engagements']:
        x,y,z=t['center'];h=t['height_mm'];threads[(t['host'],t['screw'])]=cyl(t['diameter_mm']/2,h,(x,y,z-h/2))
    for short,m in RETAINER_MOUNTS.items():threads[(short+'_RETAINER',short+'_RETAINER_M2x5')]=cyl(1.01,2.91,(m['x'],m['y'],13.695))
    allpairs=[]
    for pn,p in parts.items():
        for n,h in hw.items():
            lb=lower_bound(p,h)
            if lb>1e-5:
                allpairs.append(dict(a=pn,b=n,overlap_mm3=0.,gap_mm=None,lower_bound_mm=lb,method='Disjoint bounds certify zero common volume only; no exact minimum-distance claim',passed=True));continue
            r=pair(p,h,pn,n,0.);residual=r['overlap_mm3'];allowed=0.;rule='No intentional overlap'
            if (pn,n) in threads:
                common=p.intersect(h);allowed=vol(common.intersect(threads[(pn,n)]));residual=vol(common.cut(threads[(pn,n)]))
                rule='M2 thread engagement envelope in diameter1.7 pilot only; other intersections remain failures'
            allpairs.append(dict(**r,named_thread_engagement_mm3=allowed,unexplained_overlap_mm3=residual,classification=rule,passed=residual<=.001))
            if residual>.001:print('PRINTED_HARDWARE_REVIEW',allpairs[-1],flush=True)
        save('all_printed_hardware_intersections.json',dict(rows=allpairs,passed=False))
    save('all_printed_hardware_intersections.json',dict(rows=allpairs,passed=all(p['passed'] for p in allpairs)))
    definition=wire_definition();ends={}
    for r in definition['routes']:
        if r['name'] not in hw:continue
        ends[r['name']]=[(n,p,r['radius']+.8) for n,p in zip(r['end_contacts'],[r['points'][0],r['points'][-1]])]
    mates={'SIDE_SF_NO_ROUTE_EST':['SF_D2F_01F','RF_IO_HEADER_EST'],
           'SIDE_SR_NO_ROUTE_EST':['SR_D2F_01F','RF_IO_HEADER_EST'],
           'SIDE_COM_ROUTE_EST':['SF_D2F_01F','SR_D2F_01F'],
           'SIDE_COM_GPIO_ROUTE_EST':['SIDE_COM_ROUTE_EST','RF_IO_HEADER_EST']}
    for n,ps in ROUTES.items():ends[n]=[(target,p,1.1) for target,p in zip(mates[n],[ps[0],ps[-1]])]
    # The same COM junction is considered in both pair directions.
    ends['SIDE_COM_ROUTE_EST'].append(('SIDE_COM_GPIO_ROUTE_EST',ROUTES['SIDE_COM_GPIO_ROUTE_EST'][0],1.1))
    wirechecks=[]
    for name,terminals in ends.items():
        wire=hw[name]
        for n,obstacle in hw.items():
            if n==name:continue
            lb=lower_bound(wire,obstacle)
            if lb>=.2-1e-6:
                wirechecks.append(dict(a=name,b=n,exact_gap_mm=None,certified_lower_bound_mm=lb,passed=True,method='Bound suffices for0.2mm requirement, not claimed as exact distance'));continue
            raw=pair(wire,obstacle,name,n,.2);record=dict(raw=raw,passed=raw['pass_check'],classification='ordinary wire clearance')
            localized=[(p,r) for target,p,r in terminals if target==n]
            if localized:
                remaining=wire
                for point,radius in localized:remaining=remaining.cut(cq.Solid.makeSphere(radius,V(*point),angleDegrees1=-90,angleDegrees2=90))
                check=pair(remaining,obstacle,name+'_AWAY_FROM_TERMINATION',n,.2)
                record.update(classification='Declared connector/solder termination only',termination_balls=[dict(center_mm=p,radius_mm=r) for p,r in localized],away_from_termination=check,
                              passed=raw['overlap_mm3']<=.001 and check['pass_check'])
            wirechecks.append(record)
            if not record['passed']:print('WIRE_CLEARANCE_REVIEW',name,n,record,flush=True)
        save('wire_component_clearances.json',dict(rows=wirechecks,passed=False))
    save('wire_component_clearances.json',dict(rows=wirechecks,passed=all(r['passed'] for r in wirechecks)))

if __name__=='__main__':main()
