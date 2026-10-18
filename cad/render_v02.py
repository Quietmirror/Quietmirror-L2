from pathlib import Path
import render_views as rv
ROOT=Path(__file__).resolve().parents[1]
rv.OUT=ROOT/'views/v02';rv.OUT.mkdir(exist_ok=True)
p=ROOT/'exports/v02/quietmirror_fingertip_V0.2.stl'
paths=[(p,(.44,.57,.62),1)]
def render(*args,**kwargs):rv.render(*args,version='V0.2',**kwargs)
render('01_isometric.png',paths,(-140,160,140),title='V0.2 / 连续外壳 · 右手指握',subtitle='短机身轮廓；顶部和侧壁不做蜂窝孔。真实 STL 渲染，全部按键固定。',scale=48)
render('02_top.png',paths,(0,-44,220),up=(0,1,0),title='俯视 / 短机身与完整指肚接触面',subtitle='前端向上；左为拇指。窄缝标示左右主键，保留实体桥连接。',scale=52)
render('03_left_side.png',paths,(-220,-44,14),title='左侧 / 连续拇指侧壁',subtitle='前端在左；两个固定侧键凸台。低尾部逐渐下降，避免把掌根抬起。',scale=40)
render('04_bottom.png',paths,(0,-44,-220),up=(0,1,0),title='底视 / 五脚与内部承力筋',subtitle='底部集中留空；Ø8.8 mm 平台，五个粘贴面 Z=0。传感器区只作位置参考。',scale=52)
render('05_right_side.png',paths,(220,-44,14),title='右侧 / 无名指、小指支撑',subtitle='后部在左；连续触面，下缘保留浅托边。外壳和底筋为同一实体。',scale=40)
render('06_envelopes.png',[(p,(.66,.7,.74),.10)],(-130,150,130),env=True,envfile=ROOT/'reports/v02/envelope_interferences.json',title='内部参考包络 / 未确认装配兼容',subtitle='主板、传感器镜头、滚轮、电池、侧键与天线均需实测；包络不参与打印。',scale=50)
