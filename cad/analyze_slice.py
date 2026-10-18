"""Read actual PrusaSlicer toolpaths, separate material roles, render layers."""
from pathlib import Path
import argparse
import json,re,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib import font_manager
ROOT=Path(__file__).resolve().parents[1]
GCODE=ROOT/'.tools/V0.1_estimate_with_support.gcode'
REPORT=ROOT/'reports';VIEWS=ROOT/'views';VERSION='0.1'
FONT=font_manager.FontProperties(fname='C:/Windows/Fonts/msyh.ttc')
plt.rcParams.update({'font.family':FONT.get_name(),'axes.unicode_minus':False})

def parse():
    pos=np.zeros(3);role='Other';lengths={};segments=[];categories=[];zs=[]
    text=GCODE.read_text(encoding='utf8');footer={}
    for line in text.splitlines():
        if line.startswith(';TYPE:'):role=line[6:].strip()
        if line.startswith('; ') and ' = ' in line:
            k,v=line[2:].split(' = ',1)
            if k.startswith(('filament used [','total filament used [','estimated printing time')):footer[k]=v
        if not line.startswith(('G1 ','G0 ')):continue
        tokens=dict((k,float(v)) for k,v in re.findall(r'([XYZEF])(-?[\d.]+)',line.split(';')[0]))
        new=pos.copy()
        for i,k in enumerate('XYZ'):
            if k in tokens:new[i]=tokens[k]
        if tokens.get('E',0)>0 and np.linalg.norm(new-pos)>.00001:
            lengths[role]=lengths.get(role,0)+tokens['E']
            segments.append([pos.copy(),new.copy()]);zs.append(new[2])
            categories.append('support' if role.startswith('Support') else 'adhesion' if role=='Skirt/Brim' else 'model')
        pos=new
    return np.asarray(segments),np.asarray(zs),np.asarray(categories),lengths,footer

def main():
    seg,z,cat,lengths,footer=parse();factor=math.pi*(1.75/2)**2/1000*1.24
    mass={r:round(l*factor,4) for r,l in lengths.items()}
    categories=dict(model_g=sum(v for k,v in mass.items() if not k.startswith('Support') and k!='Skirt/Brim'),support_g=sum(v for k,v in mass.items() if k.startswith('Support')),adhesion_g=mass.get('Skirt/Brim',0))
    profile='slicing/'+(f'V{VERSION}_' if VERSION!='0.1' else '')+'PLA_0.4_0.20_ESTIMATE.ini'
    result=dict(slicer='PrusaSlicer 2.9.6',version=VERSION,profile=profile,orientation='feet on Z=0; 100 percent scale',estimates_only=True,footer=footer,material_by_extrusion_role_g=mass,material_by_category_g={k:round(v,3) for k,v in categories.items()},calculation='Productive relative-E extrusion moves, 1.75 mm filament, PLA density 1.24 g/cm3; footer totals are authoritative',layers=len(np.unique(np.round(z,4))))
    result['model_layers']=len(np.unique(np.round(z[cat=='model'],4)))
    result['extrusion_z_planes_count']=result['layers']
    (REPORT/'slice_summary.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf8')
    fig,axes=plt.subplots(2,2,figsize=(12,11),dpi=160,facecolor='#f8fafc')
    colors={'model':'#315f73','support':'#e1973d','adhesion':'#95a95e'}
    for ax,target in zip(axes.flat,[.2,8,20,28]):
        layer=float(np.unique(z)[np.argmin(np.abs(np.unique(z)-target))]);mask=np.isclose(z,layer,atol=.0001)
        for c,col in colors.items():
            paths=seg[mask&(cat==c),:,:2]
            if len(paths):ax.add_collection(LineCollection(paths,colors=col,linewidths=.6))
        ax.set_xlim(70,150);ax.set_ylim(58,162);ax.set_aspect('equal');ax.grid(alpha=.12);ax.set_title(f'实际刀路截面 Z = {layer:g} mm',fontsize=13)
        ax.set_xlabel('切片器平台 X / mm');ax.set_ylabel('切片器平台 Y / mm')
    fig.suptitle('实际切片预览 / 0.4 mm 喷嘴 · 0.2 mm 层高',fontsize=21,y=.98)
    fig.text(.5,.025,'蓝：试握件   橙：支撑与界面   绿：裙边；此图来自最终 G-code，未实际打印。',ha='center',fontsize=12,color='#536779')
    fig.tight_layout(rect=(.015,.06,.995,.94));fig.savefig(VIEWS/'09_slice_layers.png');plt.close(fig)
    print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--version',choices=['0.1','0.2','0.3','0.4','0.5','0.6'],default='0.1');args=ap.parse_args();VERSION=args.version
    if VERSION=='0.2':GCODE=ROOT/'.tools/V0.2_estimate_with_support.gcode';REPORT=ROOT/'reports/v02';VIEWS=ROOT/'views/v02'
    if VERSION=='0.3':GCODE=ROOT/'.tools/V0.3_estimate_with_support.gcode';REPORT=ROOT/'reports/v03';VIEWS=ROOT/'views/v03'
    if VERSION=='0.4':GCODE=ROOT/'.tools/V0.4_estimate_with_support.gcode';REPORT=ROOT/'reports/v04';VIEWS=ROOT/'views/v04'
    if VERSION=='0.5':GCODE=ROOT/'.tools/V0.5_estimate_with_support.gcode';REPORT=ROOT/'reports/v05';VIEWS=ROOT/'views/v05'
    if VERSION=='0.6':GCODE=ROOT/'.tools/V0.6_estimate_with_support.gcode';REPORT=ROOT/'reports/v06';VIEWS=ROOT/'views/v06'
    main()
