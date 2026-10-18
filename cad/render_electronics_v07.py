"""Actual STEP-exported components, with unresolved interference in red."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
import render_views as r
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'views/v07';r.OUT=OUT
info=json.loads((ROOT/'reports/v07/cad_metrics.json').read_text(encoding='utf8'))
for v,prefix,label in [('ATK_A1_PLUS','10','ATK A1 Plus / 供体空间示意'),('PAW3950_CUSTOM','11','PAW3950 / 半组装板空间示意')]:
    report=json.loads((ROOT/f'reports/v07/{v}_layout.json').read_text())
    parts=[(ROOT/a['file'],a['color'],.13 if a['name']=='BODY' or a['name'].endswith('_KEY') else .6) for a in info['parts']]
    parts += [(ROOT/a['file'],a['color'],1) for a in report['physical']]
    for n in ('left','right','middle','thumb_front','thumb_rear'):parts.append((ROOT/'exports/v07/placed'/(n+'_SWITCH_EXAMPLE.stl'),(.76,.31,.21),1))
    for suffix,cam,up,scale in [('isometric',(-140,160,140),(0,0,1),51),('top',(0,-44,220),(0,1,0),53),('side',(-220,-44,14),(0,0,1),40)]:
        r.render(prefix+'_'+suffix+'.png',parts,cam,up=up,scale=scale,title='V0.7 / '+label,subtitle='绿色：主板包络 · 金色：电池目标 · 红色：仍与试按机构干涉的电子件',version='V0.7',footer='估计空间示意 · 红色冲突待解决 · 非已适配主板或可用电子产品')
im=Image.new('RGB',(2250,740),'#f5f8fa');draw=ImageDraw.Draw(im)
for i,(file,title) in enumerate([('01_isometric.png','01 / 机械试握与试按'),('10_isometric.png','02 / ATK A1 Plus 示意'),('11_isometric.png','03 / PAW3950 示意')]):
    pic=Image.open(OUT/file).crop((0,140,1500,1120)).resize((750,490));im.paste(pic,(750*i,110));draw.text((750*i+25,35),title,font=ImageFont.truetype(r.FONT,28),fill='#263d4b')
draw.text((25,650),'实际模型渲染；电子件为估计尺寸。新增活动机构占用空间，红色冲突必须在电子装配前处理。',font=ImageFont.truetype(r.FONT,25),fill='#6b5555');im.save(OUT/'12_three_variants.png')
