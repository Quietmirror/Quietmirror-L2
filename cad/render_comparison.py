"""Create a comparison sheet from original CAD-rendered views, same camera."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
font='C:/Windows/Fonts/msyh.ttc'
im=Image.new('RGB',(2000,1130),'#f8fafc');d=ImageDraw.Draw(im)
d.text((48,25),'V0.1 → V0.2 / 从外露骨架到连续外壳',font=ImageFont.truetype(font,40),fill='#18364a')
for x,v,file in [(0,'V0.1',ROOT/'views/01_isometric.png'),(1000,'V0.2',ROOT/'views/v02/01_isometric.png')]:
    crop=Image.open(file).crop((0,132,1500,1116)).resize((1000,656),Image.Resampling.LANCZOS)
    im.paste(crop,(x,160));d.text((x+48,112),v,font=ImageFont.truetype(font,30),fill='#375d70')
    lines=['独立接触片 · 外露支柱 · 极低开放尾架','本体切片估重 18.53 g','保留作为外形探索存档'] if v=='V0.1' else ['连续侧壁 · 完整顶面 · 底部集中留空','本体切片估重 25.85 g（+7.32 g）','当前推荐试握版；主键 / 侧键 / 滚轮均固定']
    for i,line in enumerate(lines):d.text((x+48,847+i*52),line,font=ImageFont.truetype(font,25),fill='#375568')
d.text((48,1055),'共同基准：90 × 62 × 31 mm / 夹持目标约 54 mm / 五个共面圆点脚贴 / 尚未实物试握',font=ImageFont.truetype(font,25),fill='#667d8b')
im.save(ROOT/'views/v02/10_comparison.png')
