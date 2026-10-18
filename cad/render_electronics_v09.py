"""Actual STEP-exported components, with unresolved interference in red."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
import render_views as r
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'views/v09';r.OUT=OUT
info=json.loads((ROOT/'reports/v09/cad_metrics.json').read_text(encoding='utf8'))
for v,prefix,label in [('ATK_A1_PLUS','10','ATK A1 Plus / 供体空间示意'),('PAW3950_CUSTOM','11','PAW3950 / 半组装板空间示意')]:
    report=json.loads((ROOT/f'reports/v09/{v}_layout.json').read_text())
    parts=[(ROOT/a['file'],a['color'],.13 if a['name']=='BODY' or a['name'].endswith('_KEY') else .6) for a in info['parts'] if a['name'] in report['mechanical_parts']]
    parts += [(ROOT/a['file'],a['color'],1) for a in report['physical']]
    for n in ('left','right','middle','thumb_front','thumb_rear'):parts.append((ROOT/'exports/v09/placed'/(n+'_SWITCH_EXAMPLE.stl'),(.76,.31,.21),1))
    for suffix,cam,up,scale in [('isometric',(-140,160,140),(0,0,1),51),('top',(0,-44,220),(0,1,0),53),('side',(-220,-44,14),(0,0,1),40)]:
        r.render(prefix+'_'+suffix+'.png',parts,cam,up=up,scale=scale,title='V0.9 / '+label,subtitle='估计部件布局 · 本构型移除 11 个试按夹具 · 实际主板与编码器接口待测',version='V0.9',footer='独立电子示意构型 · 无静态穿模不代表已完成安装、走线或光学尺寸链')
im=Image.new('RGB',(2250,740),'#f5f8fa');draw=ImageDraw.Draw(im)
for i,(file,title) in enumerate([('01_isometric.png','01 / 机械试握与试按'),('10_isometric.png','02 / ATK A1 Plus 示意'),('11_isometric.png','03 / PAW3950 示意')]):
    pic=Image.open(OUT/file).crop((0,140,1500,1120)).resize((750,490));im.paste(pic,(750*i,110));draw.text((750*i+25,35),title,font=ImageFont.truetype(r.FONT,28),fill='#263d4b')
draw.text((25,650),'实际模型渲染；电子件为估计尺寸，使用独立构型。五键及滚轮体验请打印机械套件。',font=ImageFont.truetype(r.FONT,25),fill='#6b5555');im.save(OUT/'12_three_variants.png')
