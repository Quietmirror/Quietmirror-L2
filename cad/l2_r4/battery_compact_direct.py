"""Compact estimate proposals at the unchanged original bay centre.

No cell capacity is inferred. Do not replace the formal assembly automatically.
"""
from battery_direct_service import main as test
from common import *

def main():
    trials=[];accepted=None
    for dims in [[14,20,6],[12,20,6],[10,20,6],[12,18,6],[10,18,6]]:
        row=test(dims,'battery_compact_latest_trial.json',False);trials.append(row)
        save('battery_compact_proposals.json',dict(trials=trials,accepted=None,passed=False))
        if row['passed']:
            inv=json.loads((RP/'assembly_inventory.json').read_text())
            old=load('BATTERY_CELL_EST',OUT/'reference');c=old.Center().toTuple();h=[v/2 for v in dims]
            cell=box(c[0]-h[0],c[0]+h[0],c[1]-h[1],c[1]+h[1],c[2]-h[2],c[2]+h[2])
            fixed={n:load(n) for n in inv['printable']}
            fixed.update({n:load(n,OUT/'reference') for n in inv['H_hardware'] if n not in ['BATTERY_CELL_EST','BATTERY_ROUTE_EST']})
            row['static']=scene_pairs(cell,fixed,'BATTERY_COMPACT_PROPOSAL',.5)
            if row['static']['passed']:
                accepted=row;break
    save('battery_compact_proposals.json',dict(trials=trials,accepted=accepted,passed=False,
        status='EXACT_PROPOSAL_NOT_ADOPTED' if accepted else 'NO_ACCEPTED_PROPOSAL',
        capacity='No measured cell capacity. Reduced package dimensions cannot establish12h runtime; actual full-power current and capacity still required.'))
    if not accepted:raise RuntimeError('No compact battery proposal passed route plus static checks')

if __name__=='__main__':main()
