"""Rebuild only the two source-defined C7 caps; retain exact BODY/retainer bytes."""
import json
from common import *
from side_module import KEYS,key

def main():
    outer=load('MOTHER_OUTER_FROM_R32_SURFACE',ROOT/'exports/l2_r2_diagnostic/support_reference')
    rows=[];params=[]
    for k in KEYS:
        s,p=key(outer,k);rows.append(export(s,k['name']));params.append(p)
        f2,_=key(outer,k,.3);cq.exporters.export(f2,str(OUT/'reference'/(k['name']+'_F2_TRIAL.step')))
    data=json.loads((RP/'parameters_implemented.json').read_text());data['side_keys']=params;data['candidate']='C7 concealed cap clearances';save('parameters_implemented.json',data)
    old=json.loads((RP/'side_module_solids.json').read_text());replacements={r['name']:r for r in rows}
    save('side_module_solids.json',[replacements.get(r['name'],r) for r in old])

if __name__=='__main__':main()
