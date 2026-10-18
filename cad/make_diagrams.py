"""Dimension overlay and electronic envelope plan/elevation from final files."""
from pathlib import Path
import json
import argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib import font_manager
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
VIEWS=ROOT/'views';REPORT=ROOT/'reports';VERSION='0.1'
FONT=font_manager.FontProperties(fname='C:/Windows/Fonts/msyh.ttc')
plt.rcParams.update({'font.family':FONT.get_name(),'axes.unicode_minus':False})

def dimensions():
    im=Image.open(VIEWS/'02_top.png').crop((0,132,1500,1116))
    fig,ax=plt.subplots(figsize=(9,10.5),dpi=180)
    ax.imshow(im,extent=(-104*1500/984/2,104*1500/984/2,-96,8),aspect='equal')
    c='#213d52'
    def dim(a,b,text,where,rotation=0):
        ax.annotate('',b,a,arrowprops=dict(arrowstyle='<->',color=c,lw=1.3))
        ax.text(*where,text,ha='center',va='center',rotation=rotation,color=c,fontsize=12,bbox=dict(fc='white',ec='none',alpha=.9,pad=2))
    dim((-31,4),(31,4),'最大外宽 62 mm',(0,7))
    dim((38,0),(38,-90),'总长 90 mm',(42,-45),90)
    dim((-27,-49),(27,-49),'夹持中心目标约 54 mm',(0,-52.5))
    for x in (-31,31):ax.plot([x,x],[0,6],color=c,lw=.8)
    for y in (0,-90):ax.plot([31,40],[y,y],color=c,lw=.8)
    detail='高度 31 mm；右主键顶低于左主键 1.2 mm' if VERSION=='0.1' else '高度 31 mm；中心夹持截面实测约 54.04 mm'
    if VERSION in ('0.3','0.4','0.5'):
        actual=json.loads((REPORT/'validation.json').read_text())['grip_width_samples'][1]['outer_span_mm']
        detail=f'高度 {28 if VERSION in ("0.4","0.5") else 31} mm；中心夹持截面实测约 {actual:.2f} mm'
    ax.text(-38,-96,'左：拇指侧；右：无名指 / 小指侧\n'+detail,fontsize=11,color=c)
    ax.set_xlim(-43,48);ax.set_ylim(-101,13);ax.axis('off')
    fig.suptitle(f'V{VERSION} 尺寸基准 / 试握假设',fontsize=20,y=.97)
    fig.text(.5,.025,'实际 STL 正投影 + CAD 尺寸标注；单位 mm；打印比例 100%',ha='center',fontsize=10,color='#536779')
    fig.savefig(VIEWS/'07_dimensions.png',facecolor='#f8fafc');plt.close(fig)

def envelopes():
    env=json.loads((REPORT/'envelope_interferences.json').read_text())['envelopes']
    names=['主板及元件','参考传感器裸板','传感器封装','镜头','滚轮旋转范围','编码器','中键机构','左主键开关','右主键开关','两侧键板','电池','电池插头','线束通道','USB-C 与插入空间','电源开关','天线净空']
    fig=plt.figure(figsize=(16,10),dpi=160,facecolor='#f8fafc')
    top=fig.add_axes([.045,.15,.30,.72]);side=fig.add_axes([.39,.42,.30,.35]);legend=fig.add_axes([.73,.15,.255,.72])
    for ax in (top,side):ax.set_facecolor('#fff');ax.grid(alpha=.12)
    for i,e in enumerate(env):
        x,y,z=e['center'];w,l,h=e['size'];col=e['color']
        top.add_patch(Rectangle((x-w/2,y-l/2),w,l,fc=col,ec=col,alpha=.22,lw=1.5))
        top.text(x,y,str(i+1),color='#233950',fontsize=9,ha='center',va='center',bbox=dict(fc='white',alpha=.65,ec='none',pad=.2))
        side.add_patch(Rectangle((-y-l/2,z-h/2),l,h,fc=col,ec=col,alpha=.22,lw=1.5))
        side.text(-y,z,str(i+1),color='#233950',fontsize=9,ha='center',va='center')
    top.add_patch(Rectangle((-31,-90),62,90,fill=False,ec='#748897',ls='--'))
    top.set(xlim=(-36,36),ylim=(-95,12),xlabel='X / mm；负侧为拇指',ylabel='Y / mm；前端为 0')
    top.set_aspect('equal');top.set_title('俯视包络 / 前端向上',pad=16)
    side.add_patch(Rectangle((0,0),90,28 if VERSION in ('0.4','0.5') else 31,fill=False,ec='#748897',ls='--'))
    side.set(xlim=(-5,95),ylim=(-2,38),xlabel='距前端距离 / mm',ylabel='Z / mm');side.set_aspect('equal');side.set_title('侧面高度分布（投影重叠不等于碰撞）',pad=16)
    side.text(0,-17,('虚线仅为 90 × 62 × 28 外接框，' if VERSION in ('0.4','0.5') else '虚线仅为 90 × 62 × 31 外接框，')+'\n不表示包络已被壳体包住。\n\n红色天线区与主板 / 电池估计范围重叠，\n装配版须先改布局或板型。',fontsize=11,color='#984e4e',va='top')
    legend.axis('off')
    for i,(e,n) in enumerate(zip(env,names)):
        y=1-i*.06;legend.add_patch(Rectangle((0,y-.024),.034,.028,fc=e['color'],ec='none'))
        sizes=' × '.join(f'{v:g}' for v in e['size'])
        legend.text(.065,y,f'{i+1:02d}  {n}',fontsize=11,va='center',color='#21384a')
        legend.text(.065,y-.029,f'{sizes} mm',fontsize=9,va='center',color='#647583')
    fig.suptitle(f'V{VERSION} 电子参考包络 / ESTIMATES',x=.045,ha='left',y=.96,fontsize=22)
    fig.text(.045,.905,'除参考裸板外框外均为估计尺寸；所有摆放位置均待确认。未设计装配孔、卡扣或真实光学高度。',fontsize=12,color='#a65337')
    fig.text(.045,.055,'02 是 badjeff 参考转接板，不是完整无线主板。其他框不代表“ATK 蜻蜓 A1 Plus”的实际器件。\n传感器光轴沿 Z；具体镜头至鼠标垫距离待实物尺寸链确定。',fontsize=11,color='#536779')
    fig.savefig(VIEWS/'08_envelope_layout.png');plt.close(fig)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--version',choices=['0.1','0.2','0.3','0.4','0.5'],default='0.1');args=ap.parse_args();VERSION=args.version
    if VERSION=='0.2':VIEWS=ROOT/'views/v02';REPORT=ROOT/'reports/v02'
    if VERSION=='0.3':VIEWS=ROOT/'views/v03';REPORT=ROOT/'reports/v03'
    if VERSION=='0.4':VIEWS=ROOT/'views/v04';REPORT=ROOT/'reports/v04'
    if VERSION=='0.5':VIEWS=ROOT/'views/v05';REPORT=ROOT/'reports/v05'
    dimensions();envelopes()
