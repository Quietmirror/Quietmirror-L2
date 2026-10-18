"""Verify first-layer support toolpaths occur beneath all five raised landings."""
from pathlib import Path
import json,re,math,hashlib
import numpy as np,trimesh
ROOT=Path(__file__).resolve().parents[2];RP=ROOT/'reports/rebuild_r3_2'
gcode=ROOT.parent/'_support/work/fenrir_rebuild_r3_2/slice/R3_2_validation_only.gcode'
def main():
    met=json.loads((RP/'cad_metrics.json').read_text());d=json.loads((RP/'design_metadata.json').read_text())
    sliced=json.loads((RP/'slice_summary.json').read_text())
    placed=next(p for p in sliced['placements'] if p['part']=='BODY')
    mesh=trimesh.load_mesh(ROOT/'exports/rebuild_r3_2/print/BODY.stl')
    offset=np.array(met['BODY']['print_translation'])+np.array(placed['bounds'][0])-mesh.bounds[0]
    centers=[(np.array([*f['center'],f['contact_z']])+offset).tolist() for f in d['mechanisms']['feet']]
    text=gcode.read_text();x=y=e=0.;layer=-1;relative=False;role='';counts=[0]*5
    for line in text.splitlines():
        if line.startswith(';LAYER_CHANGE'):
            layer+=1
            if layer>0:break
        if line.startswith('M83'):relative=True
        if line.startswith('M82'):relative=False
        if line.startswith(';TYPE:'):role=line[6:]
        vals={k:float(v) for k,v in re.findall(r'([XYE])(-?\d*\.?\d+)',line.split(';')[0])}
        if line.startswith('G92'):e=vals.get('E',e);continue
        if not line.startswith(('G0 ','G1 ')):continue
        xx=vals.get('X',x);yy=vals.get('Y',y);ee=vals.get('E',0. if relative else e)
        delta=ee if relative else ee-e;length2=(xx-x)**2+(yy-y)**2
        if layer==0 and delta>0 and length2>1e-8 and role.startswith('Support'):
            for i,(cx,cy,cz) in enumerate(centers):
                t=max(0,min(1,((cx-x)*(xx-x)+(cy-y)*(yy-y))/length2))
                if math.hypot(x+t*(xx-x)-cx,y+t*(yy-y)-cy)<3.5:counts[i]+=1
        x,y=xx,yy
        if not relative:e=ee
    result=dict(first_layer_z_mm=.2,plate_foot_centers_mm=centers,support_segments_within_3_5mm_of_center=counts,
        pass_check=all(c>0 for c in counts),gcode_sha256=hashlib.sha256(gcode.read_bytes()).hexdigest(),
        scope='Actual first-layer support extrusion segments beneath each landing, not a quantitative full-area support or physical adhesion proof. G-code is validation-only; users must re-slice.')
    (RP/'first_layer_support_checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print('FIRST-LAYER SUPPORT',counts,result['pass_check'],flush=True);assert result['pass_check']
if __name__=='__main__':main()
