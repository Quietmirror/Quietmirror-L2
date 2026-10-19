"""Refresh only the compound STEP from unchanged independent component files."""
import json
from common import *

def main():
    inv=json.loads((RP/'assembly_inventory.json').read_text());assy=cq.Assembly(name='Quietmirror_L2_r4_CAD_CANDIDATE')
    for n in inv['printable']+inv['H_hardware']:
        s=load(n,OUT/('parts' if n in inv['printable'] else 'reference'));valid(s,n)
        col=(.74,.79,.83) if n=='BODY' else ((.9,.49,.19) if n.startswith('SIDE_') and n.endswith('KEY') else ((.27,.39,.46) if n in inv['printable'] else (.25,.59,.42)))
        assy.add(s,name=n,color=cq.Color(*col))
    assy.save(str(OUT/'FULL_ASSEMBLY_H.step'));print('ASSEMBLY_REFRESH',inv['independent_components'],flush=True)

if __name__=='__main__':main()
