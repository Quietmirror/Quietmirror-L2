"""Shorter longitudinal cell proposals retaining similar estimated volume."""
from battery_direct_service import main as test
from common import *
from bounded_scene import scene_pairs

def main():
    inv=json.loads((RP/'assembly_inventory.json').read_text())
    fixed={n:load(n) for n in inv['printable']}
    fixed.update({n:load(n,OUT/'reference') for n in inv['H_hardware'] if n not in ['BATTERY_CELL_EST','BATTERY_ROUTE_EST']})
    outer=load('MOTHER_OUTER_FROM_R32_SURFACE',ROOT/'exports/l2_r2_diagnostic/support_reference')
    trials=[];accepted=None
    for dims,c in [([22,18,6],[-18.5,57,16.4]),([20,20,6],[-17.5,57,16.4]),([20,18,6],[-17.5,57,16.4]),([22,16,6],[-18.5,57,16.4]),([24,16,6],[-19,57,16.4])]:
        h=[v/2 for v in dims];cell=box(c[0]-h[0],c[0]+h[0],c[1]-h[1],c[1]+h[1],c[2]-h[2],c[2]+h[2])
        reserve=box(c[0]-h[0]-.5,c[0]+h[0]+.5,c[1]-h[1]-.5,c[1]+h[1]+.5,c[2]-h[2]-.5,c[2]+h[2]+.5)
        static=scene_pairs(cell,fixed,'BATTERY_WIDE_PROPOSAL',.5)
        row=dict(dimensions_mm=dims,center_mm=c,volume_mm3=vol(cell),static=static,outside_mother_mm3=vol(cell.cut(outer)),reserve_body_mm3=vol(reserve.intersect(fixed['BODY'])),passed=False);trials.append(row)
        save('battery_wide_proposals.json',dict(trials=trials,accepted=None,passed=False))
        if not static['passed'] or row['outside_mother_mm3']>.001 or row['reserve_body_mm3']>.001:continue
        result=test(dims,'battery_wide_latest_trial.json',False,c);row['route_test']=result
        if result['passed']:row['passed']=True;accepted=row;break
    save('battery_wide_proposals.json',dict(trials=trials,accepted=accepted,passed=False,
        status='EXACT_PROPOSAL_NOT_ADOPTED' if accepted else 'NO_ACCEPTED_PROPOSAL',
        capacity='Package volume comparison is not a capacity or endurance claim; actual12h validation remains pending.'))
    if not accepted:raise RuntimeError('No similar-volume shorter-longitudinal package passed static/reserve/route checks')

if __name__=='__main__':main()
