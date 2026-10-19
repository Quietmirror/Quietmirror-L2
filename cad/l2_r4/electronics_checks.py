"""Exact final component distances and explicit reserved-space checks."""
import itertools,json
from common import *

def main():
    inv=json.loads((RP/'assembly_inventory.json').read_text())
    printed={n:load(n) for n in inv['printable']}
    hardware={n:load(n,OUT/'reference') for n in inv['H_hardware']}
    definition=json.loads((ROOT/'cad/rebuild_r3_2/electronics.json').read_text())
    electronic={n for n in hardware if n.endswith('_EST') or n.startswith('SWITCH_') or n.endswith('_D2F_01F') or n in ['USB_C_REFERENCE','USB_ADAPTER_PCB_REFERENCE','ENCODER_EC10E_HOUSING','ENCODER_EC10E_ROTOR']}
    rows=[]
    for n in sorted(electronic):
        for pn,p in printed.items():
            required=.2 if 'ROUTE' in n else (.5 if pn in ['BODY','SF_RETAINER','SR_RETAINER'] else .3)
            r=pair(p,hardware[n],pn,n,required);rows.append(r)
            if not r['pass_check']:print('ELECTRONIC_REVIEW',r,flush=True)
        save('component_pairs.json',rows)
    adjacent=[]
    for (an,a),(bn,b) in itertools.combinations(hardware.items(),2):
        # All component intersections are checked. AABB disjointness proves
        # zero overlap only; it is never emitted as an exact minimum distance.
        aa,bb=a.BoundingBox(),b.BoundingBox()
        separated=any(getattr(aa,c+'max')<getattr(bb,c+'min') or getattr(bb,c+'max')<getattr(aa,c+'min') for c in 'xyz')
        if separated:
            adjacent.append(dict(a=an,b=bn,overlap_mm3=0.,gap_mm=None,method='disjoint bounds prove zero intersection; no minimum-distance claim'))
            continue
        r=pair(a,b,an,bn,0.);adjacent.append(r)
        if r['overlap_mm3']>.001:print('HARDWARE_INTERSECTION',r,flush=True)
    save('hardware_intersections.json',adjacent)
    reserves=[]
    nonconductive={'MATCHED_LENS_EST',*[n for n in hardware if 'SKATE_' in n or '_TUNING_SHIM_' in n]}
    for reserve in definition['reserves']:
        name=reserve['name'];s=load(name,OUT/'reference');allowed=set(reserve['allowed'])
        targets={**printed,**hardware}
        if name.startswith('ANTENNA_'):targets={n:b for n,b in hardware.items() if n not in nonconductive}
        for n,b in targets.items():
            if n in allowed:continue
            row=pair(s,b,name,n,0.);row['reserve_policy']='zero solid invasion, not clearance to a physical part';reserves.append(row)
    save('reserved_space_checks.json',reserves)
    save('electronics_raw_status.json',dict(status='REVIEW_REQUIRED',
        physical_electronics='ESTIMATED_ENVELOPES; vendor PCB, holes, package and optical data remain HARDWARE_PENDING',
        raw_clearance_failures=sum(not r['pass_check'] for r in rows),
        unclassified_hardware_overlaps=sum(r['overlap_mm3']>.001 for r in adjacent),
        reserved_space_failures=sum(r['overlap_mm3']>.001 for r in reserves),
        functional_contacts='All raw results retained. Functional seating, solder endpoints, bearings and nominal self-tapping envelopes require explicit local classification.'))

if __name__=='__main__':main()
