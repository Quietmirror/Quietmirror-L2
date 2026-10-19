"""Independent H components; the D board envelope is produced by validation."""
import json
from common import *
from mechanics import beam
ROUTES={
 'SIDE_SF_NO_ROUTE_EST':[(14.5,43.17,16.6),(14.2,43.17,18),(12.5,50,19),(4,62,19.1)],
 'SIDE_SR_NO_ROUTE_EST':[(15,57.37,16.6),(14.3,57.37,17.6),(12.,60,18.8),(4,64,19.1)],
 'SIDE_COM_ROUTE_EST':[(14.5,48.25,16.6),(13.6,48.25,17.6),(13.6,62.45,17.6),(15,62.45,16.6)],
 'SIDE_COM_GPIO_ROUTE_EST':[(13.6,60,17.6),(10,63,19.1),(4,66,19.1)]}
def main():
    for n,points in ROUTES.items():export(unite(*[beam(a,b,.3) for a,b in zip(points[:-1],points[1:])]),n,False)
    old=json.loads((ROOT/'reports/l2_r3/assembly_inventory.json').read_text(encoding='utf8'))
    printed=[p.stem for p in sorted((OUT/'parts').glob('*.step'))]
    excluded={'CARRIER_M2x5_1','CARRIER_M2x5_2','SIDE_IO_PCB','SIDE_ROUTE_EST'}
    hardware=[n for n in old['H_hardware'] if n not in excluded]+['SF_RETAINER_M2x5','SR_RETAINER_M2x5',*ROUTES]
    assert len(set(hardware))==len(hardware)
    assy=cq.Assembly(name='Quietmirror_L2_r4_CAD_CANDIDATE')
    for n in printed+hardware:
        s=load(n,OUT/('parts' if n in printed else 'reference'));valid(s,n)
        col=(.74,.79,.83) if n=='BODY' else ((.9,.49,.19) if n.startswith('SIDE_') and n.endswith('KEY') else ((.27,.39,.46) if n in printed else (.25,.59,.42)))
        assy.add(s,name=n,color=cq.Color(*col))
    assy.save(str(OUT/'FULL_ASSEMBLY_H.step'))
    save('assembly_inventory.json',dict(printable=printed,H_hardware=hardware,D_status='DONOR_PENDING',independent_components=len(printed)+len(hardware)))
    save('side_wiring.json',dict(routes={n:dict(points=p,diameter_mm=.6) for n,p in ROUTES.items()},assumption='COM/NO assignments and GPIO solder positions are reference interfaces, not a finalized PCB netlist. COM joins both switches; SF-NO and SR-NO are independent.',physical_wire='32 AWG silicone, actual diameter and bend radius HARDWARE_PENDING'))
    print('Assembly components',len(printed)+len(hardware),flush=True)
if __name__=='__main__':main()
