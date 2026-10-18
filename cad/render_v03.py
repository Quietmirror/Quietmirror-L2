"""Real STL views and side-cap fit assembly, not image-generated concepts."""
from pathlib import Path
import render_views as rv
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
rv.OUT=ROOT/'views/v03';rv.OUT.mkdir(exist_ok=True)
p=ROOT/'exports/v03/quietmirror_fingertip_V0.3_FIT.stl'
paths=[(p,(.44,.57,.62),1)]
def render(*args,**kwargs):rv.render(*args,version='V0.3',**kwargs)
render('01_isometric.png',paths,(-140,160,140),title='V0.3 / 平顺侧壁 · 适量后壳镂空',subtitle='真实 STL 渲染；完整主键 + 连续夹持带；此图为一体固定试握版。',scale=48)
render('02_top.png',paths,(0,-44,220),up=(0,1,0),title='俯视 / 主键完整，10 个圆角六边孔',subtitle='前端向上；后半段集中减重，保留外围边框和纵向传力路径。',scale=52)
render('03_left_side.png',paths,(-220,-44,14),title='左侧 / 更平整的夹持面与两个侧键',subtitle='前端在左；侧键下方保持连续实面。另提供开孔壳体与两个独立键帽。',scale=40)
render('04_bottom.png',paths,(0,-44,-220),up=(0,1,0),title='底视 / 连续底筋连接五个圆脚',subtitle='脚贴平台 Ø8.8 mm，粘贴面 Z=0；固定滚轮支架和传感器参考框保留。',scale=52)
render('05_right_side.png',paths,(220,-44,14),title='右侧 / 平顺支撑，无名指与小指触面保留',subtitle='后部在左；侧面不开密集蜂窝，下缘保留低托边。',scale=40)
render('06_envelopes.png',[(p,(.66,.7,.74),.10)],(-130,150,130),env=True,envfile=ROOT/'reports/v03/envelope_interferences.json',title='内部包络 / 仍为估计，装配尚未定版',subtitle='侧键限位边与估计侧键板可能冲突；真实开关、PCB、镜头、电池尺寸待测。',scale=50)
shell=ROOT/'exports/v03/quietmirror_fingertip_V0.3_SHELL.stl'
exploded=[(shell,(.44,.57,.62),1)]+[(ROOT/f'.tools/v03_cap_{i}_exploded.stl',(.94,.63,.26),1) for i in (1,2)]
render('11_side_buttons_exploded.png',exploded,(-180,-145,115),title='侧键分解 / 开孔壳体 + 两个独立键帽',subtitle='橙色键帽向外移 14 mm 展示；实际从底部送入、由内向外装入窗口；暂用内侧胶带固定。',scale=55)
render('12_side_buttons_fitted.png',[(shell,(.44,.57,.62),.35)]+[(ROOT/f'.tools/v03_cap_{i}_placed.stl',(.94,.63,.26),1) for i in (1,2)],(-200,-90,40),title='侧键接口 / 导向段与内侧限位边',subtitle='壳体半透明显示独立键帽；留有打印配合间隙，不包含弹簧、转轴或真实微动开关。',scale=47)
im=Image.new('RGB',(2000,1250),'#f8fafc');d=ImageDraw.Draw(im);font=rv.FONT
d.text((48,22),'V0.2 → V0.3 / 侧面平顺化、独立侧键与后壳减重',font=ImageFont.truetype(font,37),fill='#18364a')
for x,v,folder in [(0,'V0.2','v02'),(1000,'V0.3','v03')]:
    crop=Image.open(ROOT/f'views/{folder}/02_top.png').crop((350,132,1150,1116)).resize((760,935),Image.Resampling.LANCZOS)
    im.paste(crop,(x+120,140));d.text((x+50,95),v,font=ImageFont.truetype(font,31),fill='#375d70')
    lines=['收腰再外鼓，完整尾壳','固定侧键凸台'] if v=='V0.2' else ['夹持带更直，10 个圆角六边孔','独立键帽 + 开孔壳；另有一体 FIT 版']
    for i,line in enumerate(lines):d.text((x+48,1110+i*43),line,font=ImageFont.truetype(font,25),fill='#375568')
im.save(rv.OUT/'10_comparison.png')
