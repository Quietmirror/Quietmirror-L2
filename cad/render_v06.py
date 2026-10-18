"""Render the delivered CAD meshes and the two estimated electronics layouts."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import render_views as r
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'views/v06';OUT.mkdir(parents=True,exist_ok=True);r.OUT=OUT
FONT=r.FONT;fp=font_manager.FontProperties(fname=FONT);plt.rcParams.update({'font.family':fp.get_name(),'axes.unicode_minus':False})

def main():
    fit=ROOT/'exports/v06/quietmirror_fingertip_V0.6_FIT.stl';shell=ROOT/'exports/v06/quietmirror_fingertip_V0.6_SHELL.stl'
    paths=[(fit,(.45,.60,.65),1)]
    views=[('01_isometric.png',(-140,160,140),(0,0,1),48,'斜视 / 一体试握模型'),('02_top.png',(0,-44,220),(0,1,0),52,'俯视 / 侧键之外中轴对称'),('03_left_side.png',(-220,-44,14),(0,0,1),40,'左侧 / 双侧键触达'),('04_bottom.png',(0,-44,-220),(0,1,0),52,'底视 / 对称五脚与中心开关孔'),('05_right_side.png',(220,-44,14),(0,0,1),40,'右侧 / 移除外伸托边'),('06_front_charge.png',(0,220,7),(0,0,1),26,'正视 / 中心充电孔')]
    for name,camera,up,scale,title in views:
        r.render(name,paths,camera,up=up,scale=scale,title='V0.6 / '+title,subtitle='12 孔；孔间目标 2.2 mm，外缘目标 2.4 mm；固定主键、侧键和滚轮',version='V0.6')
    for variant,prefix,label in [('ATK_A1_PLUS','07','ATK A1 Plus 主板替换示意'),('PAW3950_CUSTOM','08','PAW3950 半组装主板示意')]:
        report=json.loads((ROOT/f'reports/v06/{variant}_layout.json').read_text());parts=[(ROOT/a['file'],a['color'],1) for a in report['physical']]
        for i in (1,2):parts.append((ROOT/f'.tools/v06_cap_{i}_placed.stl',(.88,.53,.25),1))
        for suffix,cam,up in [('isometric',(-140,160,140),(0,0,1)),('top',(0,-44,220),(0,1,0)),('side',(-220,-44,14),(0,0,1))]:
            r.render(f'{prefix}_{suffix}.png',[(shell,(.65,.72,.75),.16)]+parts,cam,up=up,scale=51 if suffix!='side' else 40,title='V0.6 / '+label,subtitle='绿色 PCB · 金色电池 · 黑色芯片/滚轮 · 橙色开关；全部为估计尺寸',version='V0.6',footer='估计装配示意 · 非实测主板 · 非可用电子产品')
        # Labelled plan view: a separate readable drawing accompanies the STEP.
        fig,ax=plt.subplots(figsize=(10,11),dpi=160)
        layout=json.loads((ROOT/'reports/v06/vent_layout.json').read_text());pts=layout['outer_contour_xd_mm'];ax.plot([a[0] for a in pts],[a[1] for a in pts],color='#697d89')
        for e in report['physical']:
            if 'size' not in e:continue
            x,y,z=e['center'];w,l,h=e['size'];color=e['color']
            ax.add_patch(plt.Rectangle((x-w/2,-y-l/2),w,l,edgecolor=color,facecolor=color,alpha=.23))
        labels=[('电池 500 mAh 目标',(0,46),(38,42)),('传感器 + 镜头',(0,48),(38,53)),('滚轮 / 编码器',(0,17),(38,16)),('USB-C + 充电区',(0,5),(38,3)),('双侧键板',(-16,40),(-56,32)),('天线净空',(0,67),(38,68)),('电源开关',(0,72),(38,80))]
        for text,xy,xytext in labels:ax.annotate(text,xy,xytext=xytext,arrowprops=dict(arrowstyle='-',color='#617382'),fontsize=11,va='center')
        ax.add_patch(plt.Rectangle((-9,62),18,10,edgecolor='#9d5ab4',facecolor='none',linestyle='--'))
        ax.set_xlim(-58,65);ax.set_ylim(94,-5);ax.set_aspect('equal');ax.set_xlabel('X / mm');ax.set_ylabel('距前端 D / mm');ax.grid(alpha=.15)
        ax.set_title(label+'\n平面包络投影，非实际 PCB 外形；全部尺寸为估计',fontsize=14,pad=18)
        fig.tight_layout();fig.savefig(OUT/f'{prefix}_layout.png');plt.close(fig)
    # Comparison and three deliverable overview are composites of actual meshes.
    for filename,files,titles in [('10_three_variants.png',['01_isometric.png','07_isometric.png','08_isometric.png'],['01 纯试握模型','02 ATK A1 Plus 示意','03 PAW3950 示意']),('11_comparison.png',['../v05/02_top.png','02_top.png'],['V0.5 / 冻结旧底部','V0.6 / 对称底部与窄外缘'])]:
        width=750*len(files);im=Image.new('RGB',(width,700),'#f5f8fa');draw=ImageDraw.Draw(im)
        for i,(f,title) in enumerate(zip(files,titles)):
            src=Image.open(OUT/f);src=src.crop((0,130,1500,1115)).resize((750,493));im.paste(src,(750*i,105));draw.text((750*i+25,35),title,font=ImageFont.truetype(FONT,26),fill='#22374a')
        draw.text((25,630),'实际交付网格渲染 / 电子版尺寸与布局均为估计',font=ImageFont.truetype(FONT,22),fill='#64788a');im.save(OUT/filename)
    layout=json.loads((ROOT/'reports/v06/vent_layout.json').read_text());fig,ax=plt.subplots(figsize=(9,9),dpi=180)
    pts=layout['outer_contour_xd_mm'];ax.plot([a[0] for a in pts],[a[1] for a in pts],color='#30465c',lw=1.5)
    for h in layout['holes']:
        q=h['rounded_xd_mm'];ax.fill([a[0] for a in q],[a[1] for a in q],color='#c8e3e6',edgecolor='#467a83',lw=1);x,d=h['seed_xd_mm'];ax.text(x,d,h['id'],ha='center',va='center',fontsize=10)
    ax.set_xlim(-33,33);ax.set_ylim(92,43);ax.set_aspect('equal');ax.grid(alpha=.15);ax.set_title('12 个轮廓孔 / 孔间 2.2 mm，外缘目标 2.4 mm\n前部侧键受力区和多筋交汇节点局部更宽',fontsize=13);ax.set_xlabel('X / mm');ax.set_ylabel('距前端 D / mm');fig.tight_layout();fig.savefig(OUT/'12_vent_layout.png');fig.savefig(OUT/'12_vent_layout.svg');plt.close(fig)

if __name__=='__main__':main()
