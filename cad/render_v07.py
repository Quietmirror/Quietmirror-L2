"""Orthographic, assembly and exploded views of real delivered STL geometry."""
from pathlib import Path
import json
import trimesh
from PIL import Image,ImageDraw,ImageFont
import render_views as r
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'views/v07';OUT.mkdir(parents=True,exist_ok=True);r.OUT=OUT
def main():
    info=json.loads((ROOT/'reports/v07/cad_metrics.json').read_text(encoding='utf8'));paths=[(ROOT/a['file'],a['color'],1) for a in info['parts']]
    switches=[(ROOT/'exports/v07/placed'/(n+'_SWITCH_EXAMPLE.stl'),(.76,.31,.21),1) for n in ('left','right','middle','thumb_front','thumb_rear')]
    paths+=switches
    for n,cam,up,scale,title in [('01_isometric.png',(-140,160,140),(0,0,1),49,'可拆装按键与滚轮'),('02_top.png',(0,-44,220),(0,1,0),53,'缩小主键 / 对称增加前部孔'),('03_left_side.png',(-220,-44,14),(0,0,1),40,'细长双侧键'),('04_bottom.png',(0,-44,-220),(0,1,0),53,'V0.6 底部保留 / 开放装配'),('05_right_side.png',(220,-44,14),(0,0,1),40,'平整右侧'),('06_front.png',(0,220,7),(0,0,1),27,'前部滚轮轴 / USB-C 预留')]:
        r.render(n,paths,cam,up=up,scale=scale,title='V0.7 / '+title,subtitle='16 × 27 mm 独立主键 · 五个可装轻触开关的导向机构 · 可旋转及下压滚轮',version='V0.7',footer='实际 CAD 网格渲染 · 机械样机待打印调校 · 无电子功能验证')
    exploded=[];inside=[]
    for a in info['parts']:
        n=a['name'];m=trimesh.load_mesh(ROOT/a['file']);delta=[0,0,0]
        if n.endswith('_KEY'):delta=[-15,0,0] if n.startswith('thumb') else [0,0,15]
        elif n.endswith('_TRAY'):delta=[12,0,0] if n.startswith('thumb') else [0,0,-12]
        elif n.endswith('_RETAINER'):delta=[7,0,0] if n.startswith('thumb') else [0,0,-6]
        elif n in ('WHEEL','AXLE','AXLE_WASHER','WHEEL_CARRIER','DETENT_LEAF'):delta=[0,0,13]
        m.apply_translation(delta);f=ROOT/'.tools'/('v07_exploded_'+n+'.stl');m.export(f);exploded.append((f,a['color'],1))
        inside.append((ROOT/a['file'],a['color'],.12 if n=='BODY' or n.endswith('_KEY') else 1))
    inside+=switches
    for name,pp,title,scale in [('07_exploded.png',exploded,'装配分解 / 螺钉和开关另备',65),('08_internal.png',inside,'内部导向 / 托架 / 滚轮架',51)]:
        r.render(name,pp,(-140,160,140),scale=scale,title='V0.7 / '+title,subtitle='试按机构为独立打印件；开关提供点击与回位，打印棘齿提供滚轮段落',version='V0.7',footer='0.4 mm 为 CAD 最大空行程 · 需按实际开关调校预压与限位')
    im=Image.new('RGB',(1500,740),'#f5f8fa');draw=ImageDraw.Draw(im)
    for i,(path,label) in enumerate([(ROOT/'views/v06/02_top.png','V0.6 / 23 × 41 mm 固定主键'),(OUT/'02_top.png','V0.7 / 16 × 27 mm 活动主键')]):
        src=Image.open(path).crop((0,140,1500,1120)).resize((750,490));im.paste(src,(i*750,100));draw.text((30+i*750,35),label,font=ImageFont.truetype(r.FONT,28),fill='#234050')
    draw.text((30,650),'投影矩形面积减少约 54%；接触面仍是原始连续曲面。',font=ImageFont.truetype(r.FONT,26),fill='#526674');im.save(OUT/'09_comparison.png')
if __name__=='__main__':main()
