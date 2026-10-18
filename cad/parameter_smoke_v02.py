"""One nearby parameter combination, not a guarantee of every parameter range."""
import copy,json
from build_v02 import ROOT,create,bounds
p=json.loads((ROOT/'cad/parameters_v02.json').read_text())
p.update(length=94.,max_width=64.,height=32.,grip_width=56.)
p['left_key']['y']+=1;p['right_key']['y']+=1;p['wheel']['y']+=1.5
for b in p['side_buttons']:b['y']+=1
s,_,_,_=create(p);bb=bounds(s)
r=dict(parameters_changed='L94 W64 H32 grip56; both key patches back1; wheel back1.5; side bumps back1; mm',valid=s.isValid(),solids=len(s.Solids()),dimensions_xyz_mm=[bb[i+3]-bb[i] for i in range(3)],volume_mm3=s.Volume(),scope='One nearby parameter smoke check; no alternative print file exported; not a parameter-range certification')
(ROOT/'reports/v02/parameter_smoke_check.json').write_text(json.dumps(r,indent=2),encoding='utf8')
print(json.dumps(r,indent=2));assert r['valid'] and r['solids']==1
