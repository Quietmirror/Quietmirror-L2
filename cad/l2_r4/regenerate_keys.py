"""Rebuild and finish the two caps; retain exact BODY/retainer bytes."""
import json
from common import *
from side_module import KEYS,key,ROD_RADIUS,PAD_RADIUS,PAD_HEIGHT

def finished_key(outer,k,offset=.2):
    s,p=key(outer,k,offset)
    # The offset crown leaves a small crescent of the original rod outside
    # the backing sphere, intruding into the PET layer. Start the complete
    # cylindrical rod 0.02mm before the crown's rear plane. Only that crescent
    # is trimmed; the spherical contact face and its continuous root remain.
    sphere=cq.Solid.makeSphere(PAD_RADIUS,V(k['rod_end']+PAD_RADIUS,k['rod_y']+k['pad_y_offset'],16.6),angleDegrees1=-90,angleDegrees2=90)
    crescent=cyl(ROD_RADIUS+.00001,PAD_HEIGHT-.02-.40,(k['rod_end']+.40,k['rod_y'],16.6),(1,0,0)).cut(sphere)
    s=valid(s.cut(crescent).clean(),k['name'])
    p.update(rod_to_crown_finish='C10: remove rod crescent outside backing sphere over x=end+0.40..end+0.50; pad, contact skin, BODY and retainers unchanged')
    return s,p

def main():
    outer=load('MOTHER_OUTER_FROM_R32_SURFACE',ROOT/'exports/l2_r2_diagnostic/support_reference')
    rows=[];params=[]
    for k in KEYS:
        s,p=finished_key(outer,k);rows.append(export(s,k['name']));params.append(p)
        f2,_=finished_key(outer,k,.3);cq.exporters.export(f2,str(OUT/'reference'/(k['name']+'_F2_TRIAL.step')))
    data=json.loads((RP/'parameters_implemented.json').read_text());data['side_keys']=params;data['candidate']='C10 exact rod-to-pad backing-sphere finish';save('parameters_implemented.json',data)
    old=json.loads((RP/'side_module_solids.json').read_text());replacements={r['name']:r for r in rows}
    save('side_module_solids.json',[replacements.get(r['name'],r) for r in old])

if __name__=='__main__':main()
