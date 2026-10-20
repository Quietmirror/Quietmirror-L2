"""Continuous rolling clearance via an axisymmetric envelope of actual wheel/rotor.

Full wheel click motion is checked separately. The cylinder union is invariant
under every angle about the roll axis and must contain both actual components.
It is conservative where the hex shaft and rotor socket leave empty space.
"""
import json,math
from common import *
from bounded_scene import scene_pairs
from contact_audit import mate

def main():
    p=json.loads((ROOT/'cad/rebuild_r2/parameters.json').read_text());h=p['hardware']
    wheel=load('WHEEL');rotor=load('ENCODER_EC10E_ROTOR',OUT/'reference')
    sweep=unite(cyl(h['wheel_diameter']/2,h['wheel_width'],(-h['wheel_width']/2,28,19),(1,0,0)),
                cyl(1.67/math.sqrt(3),6,(2.85,28,19),(1,0,0)),
                cyl(1.,4.2,(-7.25,28,19),(1,0,0)),
                cyl(1.49,4.4,(3.55,28,19),(1,0,0)))
    containment={n:vol(s.cut(sweep)) for n,s in [('WHEEL',wheel),('ENCODER_EC10E_ROTOR',rotor)]}
    inv=json.loads((RP/'assembly_inventory.json').read_text());fixed={n:load(n) for n in inv['printable'] if n!='WHEEL'}
    fixed.update({n:load(n,OUT/'reference') for n in inv['H_hardware'] if n!='ENCODER_EC10E_ROTOR'})
    scene=scene_pairs(sweep,fixed,'WHEEL_CONTINUOUS_ROLL_ENVELOPE',.3);classified=[]
    for r in scene['measured_pairs']:
        row=dict(raw=r,passed=r['pass_check'],classification='ordinary continuous rolling clearance')
        if not row['passed'] and r['b']=='WHEEL_CARRIER':
            f=fixed['WHEEL_CARRIER'].intersect(cyl(2.81,2.42,(-6.71,28,19),(1,0,0)))
            row.update(mate(sweep,fixed['WHEEL_CARRIER'],f,'WHEEL_CONTINUOUS_ROLL_ENVELOPE','WHEEL_CARRIER',.3,'round shaft diameter2 / bearing2.35',r))
            row['passed'] &= r['gap_mm']>=.1749
        elif not row['passed'] and r['b']=='ENCODER_EC10E_HOUSING':
            row.update(classification='encoder rotor radius1.49 in housing bore1.60; wheel axial face clearance0.25',
                       passed=r['overlap_mm3']<=.001 and r['gap_mm']>=.1099)
        classified.append(row)
    report=dict(axis_mm=[[0,28,19],[1,28,19]],method='Exact axisymmetric cylinder union; contains actual WHEEL and rotor and is invariant under all roll angles',
                containment_outside_mm3=containment,raw_scene=scene,classified_pairs=classified,
                passed=all(v<=.001 for v in containment.values()) and all(r['passed'] for r in classified),
                limitation='Geometric rolling freedom only; printed hex torsional strength, encoder detents and friction are physical tests.')
    save('wheel_continuous_rotation.json',report);print(report,flush=True)

if __name__=='__main__':main()
