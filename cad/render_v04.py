"""Real STL views and side-cap fit assembly, not image-generated concepts."""
from pathlib import Path
import render_views as rv
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
rv.OUT=ROOT/'views/v04';rv.OUT.mkdir(exist_ok=True)
p=ROOT/'exports/v04/quietmirror_fingertip_V0.4_FIT.stl'
paths=[(p,(.44,.57,.62),1)]
def render(*args,**kwargs):rv.render(*args,version='V0.4',**kwargs)
render('01_isometric.png',paths,(-140,160,140),title='V0.4 / Fenrir 方向 · 低前端与缓升主键',subtitle='真实 STL 渲染；完整主键 + 连续夹持带 + 原 V0.3 底部；此图为一体固定试握版。',scale=48)
render('02_top.png',paths,(0,-44,220),up=(0,1,0),title='俯视 / 主键完整，6 个较大圆角六边窗口',subtitle='前端向上；后半段集中减重，保留外围边框和纵向传力路径。',scale=52)
render('03_left_side.png',paths,(-220,-44,14),title='左侧 / 低前端、后移壳背与保留的侧键',subtitle='前端在左；侧键下方保持连续实面。另提供开孔壳体与两个独立键帽。',scale=40)
render('04_bottom.png',paths,(0,-44,-220),up=(0,1,0),title='底视 / V0.3 底部整段锁定不变',subtitle='Z≤6 mm 全部沿用 V0.3；五脚、底筋、传感器框、右托边及轮架根部不变。',scale=52)
render('05_right_side.png',paths,(220,-44,14),title='右侧 / 平顺支撑，无名指与小指触面保留',subtitle='后部在左；侧面不开密集蜂窝，下缘保留低托边。',scale=40)
render('06_envelopes.png',[(p,(.66,.7,.74),.10)],(-130,150,130),env=True,envfile=ROOT/'reports/v04/envelope_interferences.json',title='内部包络 / 仍为估计，装配尚未定版',subtitle='侧键限位边与估计侧键板可能冲突；真实开关、PCB、镜头、电池尺寸待测。',scale=50)
shell=ROOT/'exports/v04/quietmirror_fingertip_V0.4_SHELL.stl'
exploded=[(shell,(.44,.57,.62),1)]+[(ROOT/f'.tools/v04_cap_{i}_exploded.stl',(.94,.63,.26),1) for i in (1,2)]
render('11_side_buttons_exploded.png',exploded,(-180,-145,115),title='侧键分解 / 开孔壳体 + 两个独立键帽',subtitle='橙色键帽向外移 14 mm 展示；实际从底部送入、由内向外装入窗口；暂用内侧胶带固定。',scale=55)
render('12_side_buttons_fitted.png',[(shell,(.44,.57,.62),.35)]+[(ROOT/f'.tools/v04_cap_{i}_placed.stl',(.94,.63,.26),1) for i in (1,2)],(-200,-90,40),title='侧键接口 / 导向段与内侧限位边',subtitle='壳体半透明显示独立键帽；留有打印配合间隙，不包含弹簧、转轴或真实微动开关。',scale=47)

# Equal-camera side comparison makes the actual height change visible.
im=Image.new('RGB',(2000,1450),'#f8fafc');d=ImageDraw.Draw(im);font=rv.FONT
d.text((45,20),'V0.3 → V0.4 / 底部保留，前端降低，壳背后移',font=ImageFont.truetype(font,37),fill='#18364a')
for y,v,folder in [(100,'V0.3','v03'),(745,'V0.4','v04')]:
 crop=Image.open(ROOT/f'views/{folder}/03_left_side.png').crop((180,315,1320,900))
 im.paste(crop,(430,y-20))
 d.text((45,y+220),v,font=ImageFont.truetype(font,34),fill='#375d70')
 d.text((45,y+300),'31 mm' if v=='V0.3' else '约 28 mm',font=ImageFont.truetype(font,24),fill='#375568')
d.text((45,1380),'相同正投影视角；键帽同形、位置微调；具体尺寸和底部零差异检查见报告。',font=ImageFont.truetype(font,27),fill='#375568')
im.save(rv.OUT/'10_comparison.png')
render('13_frozen_bottom.png',[(ROOT/'.tools/v04_frozen_bottom.stl',(.19,.60,.50),1)],(0,-44,-220),up=(0,1,0),title='冻结底部 / Z≤6 mm 完整几何',subtitle='从 V0.3 已交付 STEP 直接取出；保存后的新旧 STEP 另做双向布尔差检查。',scale=52)
# Render old and new upper frames side-by-side, same camera and crop.
im=Image.new('RGB',(2000,1220),'#f8fafc');d=ImageDraw.Draw(im)
d.text((40,20),'四个历史版本 / 实际 STL 等轴视图',font=ImageFont.truetype(font,37),fill='#18364a')
for i,(ver,folder) in enumerate([('V0.1',''),('V0.2','v02/'),('V0.3','v03/'),('V0.4','v04/')]):
 x=(i%2)*1000;y=90+(i//2)*550
 crop=Image.open(ROOT/f'views/{folder}01_isometric.png').crop((170,210,1340,1116));crop.thumbnail((900,470),Image.Resampling.LANCZOS)
 im.paste(crop,(x+50,y+45));d.text((x+40,y),ver,font=ImageFont.truetype(font,30),fill='#375d70')
im.save(ROOT/'views/history_V0.1-V0.4.png')
