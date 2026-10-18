"""Dimensioned drawing from actual rounded CAD profiles, not a concept image."""
from pathlib import Path
import json
import numpy as np
import trimesh
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT=Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'reports/v05/vent_layout.json').read_text())
v=json.loads((ROOT/'reports/v05/vent_verification.json').read_text())
font=font_manager.FontProperties(fname='C:/Windows/Fonts/msyh.ttc')
plt.rcParams.update({'font.family':font.get_name(),'axes.unicode_minus':False})
cm=trimesh.load_mesh(ROOT/'.tools/v05_symmetric_crown.stl')
# Project the saved crown mesh, filling its holes only for the outer silhouette.
triangles=[]
for f in cm.faces:
    p=cm.vertices[f,:2].copy();p[:,1]*=-1;q=Polygon(p)
    if q.area>1e-7:triangles.append(q)
projected=unary_union(triangles)
outline=Polygon(projected.exterior).intersection(box(-40,46,40,82))

fig=plt.figure(figsize=(15,10),dpi=160,facecolor='#f8fafc')
ax=fig.add_axes([.055,.16,.58,.70]);notes=fig.add_axes([.68,.16,.29,.70]);notes.axis('off')
x,d=outline.exterior.xy;ax.fill(x,d,color='#d6e0e4')
domain=Polygon(r['domain_xd_mm']);x,d=domain.exterior.xy;ax.fill(x,d,color='#547987')
for h in r['holes']:
    q=Polygon(h['rounded_xd_mm']);x,d=q.exterior.xy;ax.fill(x,d,color='white',ec='#325b70',lw=.7)
    pt=q.centroid
    ax.text(pt.x,pt.y-.5,h['id'],ha='center',va='center',fontsize=11,color='#214154')
    ax.text(pt.x,pt.y+1,f"{h['area_mm2']:.1f} mm²",ha='center',va='center',fontsize=9,color='#5a7482')
ax.axvline(0,ls='--',lw=.8,color='#e8ab52',alpha=.9)
ax.annotate('',xy=(-5.55,52.2),xytext=(-7.75,52.2),arrowprops=dict(arrowstyle='<->',lw=1.4,color='#cb7133'))
ax.annotate('2.2 mm',xy=(-6.65,52.2),xytext=(-10,46.9),fontsize=12,color='#a34b22',arrowprops=dict(arrowstyle='-',color='#cb7133'),ha='center')
ax.set(xlim=(-28,28),ylim=(82,46),xlabel='X / mm（中心线 X=0）',ylabel='距前端 D / mm')
ax.set_aspect('equal');ax.grid(alpha=.14);ax.set_facecolor('#f8fafc')
notes.text(0,1,'V0.4 → V0.5',fontsize=20,color='#1d3e51',va='top')
notes.text(0,.90,'6 孔 → 10 孔\n3—4—3 交错镜像排列\n\n19 对相邻孔最短间距\n全部为 2.200 mm\n\n单孔面积 80.7–99.3 mm²\n上一版每孔 85.3 mm²\n平均孔面积增大约 5.5%\n\n中间孔保留完整多边轮廓\n两肩孔随侧面收边\n尾部孔随尾壳收窄\n孔角 R1.0 mm',fontsize=14,color='#3f5f70',va='top',linespacing=1.55)
notes.text(0,.10,'灰色：外围承力 / 夹持带\n蓝色：连续孔间筋\n白色：圆角孔的真实 XY 轮廓',fontsize=12,color='#3f5f70',va='top',linespacing=1.6)
fig.text(.055,.94,'V0.5 / 孔形、对称与筋宽核对图',fontsize=25,color='#193b50')
fig.text(.055,.90,'从 CAD 圆弧轮廓生成；图中 D=-Y。侧键及下部底筋未投影到白色孔口中。',fontsize=13,color='#597080')
fig.text(.055,.075,'2.2 mm 指相邻孔直边之间的最短平面距离；圆角交汇节点与外围边框有意更宽。',fontsize=13,color='#3f5f70')
fig.text(.055,.035,'上壳主轮廓、主键与孔阵镜像；左侧键和冻结的右托边保留右手功能布局。单位 mm。',fontsize=12,color='#597080')
for ext in ('png','svg'):fig.savefig(ROOT/f'views/v05/14_vent_layout.{ext}')
plt.close(fig)
