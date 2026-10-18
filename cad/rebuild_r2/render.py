"""Offscreen CPU renders and installation figures from the actual R2 meshes."""
from pathlib import Path
import ctypes, json, math, os
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
SUP=ROOT.parent/'_support'
mesa=SUP/'tools/PrusaSlicer/PrusaSlicer-2.9.6/mesa/opengl32.dll'
if mesa.exists():
    os.add_dll_directory(str(mesa.parent));ctypes.WinDLL(str(mesa))
try:ctypes.windll.kernel32.SetPriorityClass(ctypes.c_void_p(-1),0x4000)
except Exception:pass
import vtk
from PIL import Image,ImageDraw,ImageFont
OUT=ROOT/'views/rebuild_r2';OUT.mkdir(exist_ok=True,parents=True)
MESH=ROOT/'exports/rebuild_r2/assembly'
FONT='C:/Windows/Fonts/msyh.ttc'
COLORS={'BODY':(.18,.38,.43),'LEFT_KEY':(.72,.81,.77),'RIGHT_KEY':(.72,.81,.77),
        'WHEEL':(.17,.21,.23),'SIDE_FRONT_KEY':(.84,.59,.25),'SIDE_REAR_KEY':(.84,.59,.25)}


def render(name,names,camera,up=(0,0,1),scale=51,title='',note='',explode=False,labels=False,lowclip=False):
    renderer=vtk.vtkRenderer();renderer.SetViewport(0,.08,1,.87)
    renderer.SetBackground(.92,.95,.96);renderer.SetBackground2(.985,.99,.995);renderer.GradientBackgroundOn()
    centers=[]
    for i,n in enumerate(names):
        path=MESH/f'{n}.stl'
        if not path.exists():path=MESH.parent/'gauges'/f'{n}.stl'
        r=vtk.vtkSTLReader();r.SetFileName(str(path));r.Update()
        port=r.GetOutputPort()
        if lowclip:
            plane=vtk.vtkPlane();plane.SetOrigin(0,0,5);plane.SetNormal(0,0,1)
            clip=vtk.vtkClipPolyData();clip.SetInputConnection(port);clip.SetClipFunction(plane);clip.InsideOutOn();clip.Update();port=clip.GetOutputPort()
        normals=vtk.vtkPolyDataNormals();normals.SetInputConnection(port);normals.SetFeatureAngle(42);normals.ConsistencyOn();normals.Update()
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort())
        a=vtk.vtkActor();a.SetMapper(mapper)
        c=COLORS.get(n,(.64,.68,.71) if 'PIN' in n or 'AXLE' in n else (.72,.47,.19))
        a.GetProperty().SetColor(*c);a.GetProperty().SetAmbient(.2);a.GetProperty().SetDiffuse(.75);a.GetProperty().SetSpecular(.16);a.GetProperty().SetSpecularPower(25)
        if 'RESERVED' in n or 'OPTICAL' in n:
            a.GetProperty().SetColor(.12,.60,.87);a.GetProperty().SetOpacity(.30)
        delta=[0,0,0]
        if explode:
            if n in ('LEFT_KEY','RIGHT_KEY'):delta=[0,0,24]
            elif n.endswith('SWITCH_CLAMP'):delta=[0,0,20]
            elif n.startswith('SIDE_') and n.endswith('KEY'):delta=[18,0,7]
            elif n=='WHEEL':delta=[0,-2,36]
            elif 'PIN' in n or 'AXLE' in n:delta=[0,0,18]
            elif n!='BODY':delta=[0,0,10]
            a.SetPosition(*delta)
        renderer.AddActor(a)
        b=r.GetOutput().GetBounds();centers.append((n,[(b[0]+b[1])/2+delta[0],(b[2]+b[3])/2+delta[1],(b[4]+b[5])/2+delta[2]]))
    cam=renderer.GetActiveCamera();cam.SetPosition(*camera);cam.SetFocalPoint(0,40,18 if explode else 13);cam.SetViewUp(*up);cam.ParallelProjectionOn();cam.SetParallelScale(scale)
    renderer.ResetCameraClippingRange()
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.AddRenderer(renderer);win.SetSize(1500,1200);win.SetMultiSamples(4);win.Render()
    positions=[]
    if labels:
        for n,point in centers:
            if n in ('BODY','LEFT_KEY','RIGHT_KEY','SIDE_FRONT_KEY','SIDE_REAR_KEY','WHEEL','WHEEL_CARRIER') or n.endswith('SWITCH_CLAMP'):
                renderer.SetWorldPoint(*point,1);renderer.WorldToDisplay();x,y,_=renderer.GetDisplayPoint();positions.append((n,x,1200-y))
    capture=vtk.vtkWindowToImageFilter();capture.SetInput(win);capture.SetInputBufferTypeToRGB();capture.ReadFrontBufferOff();capture.Update()
    writer=vtk.vtkPNGWriter();writer.SetFileName(str(OUT/name));writer.SetInputConnection(capture.GetOutputPort());writer.Write();win.Finalize()
    im=Image.open(OUT/name);d=ImageDraw.Draw(im);d.rectangle((0,0,1500,150),fill='#f8fafb')
    d.text((48,23),title,font=ImageFont.truetype(FONT,30),fill='#173342')
    d.text((48,76),note,font=ImageFont.truetype(FONT,19),fill='#506776')
    d.rectangle((0,1100,1500,1200),fill='#f8fafb')
    d.text((48,1137),'R2  /  mm  /  实际 CAD 网格 · Fenrir 参考独立重建 · 通用机械样机',font=ImageFont.truetype(FONT,21),fill='#506776')
    for idx,(n,x,y) in enumerate(positions):
        if not(140<y<1080):continue
        d.ellipse((x-14,y-14,x+14,y+14),fill='#f8fafb',outline='#1c4857',width=2)
        d.text((x-6,y-12),str(idx+1),font=ImageFont.truetype(FONT,17),fill='#163645')
    im.quantize(colors=256,dither=Image.Dither.NONE).save(OUT/name,optimize=True)
    return positions


def main():
    metrics=json.loads((ROOT/'reports/rebuild_r2/cad_metrics.json').read_text())
    printed=[n for n,v in metrics.items() if v['printable']]
    hardware=[n for n,v in metrics.items() if not v['printable']]
    names=printed+hardware
    render('01_isometric.png',names,(125,-95,125),title='R2 / Fenrir 参考短宽外形 × MiniSE 外骨骼',note='实心独立主键 · 大三角 / 梯形窗口 · 左侧双键 · 下方无整片底板')
    render('02_top.png',names,(0,40,230),up=(0,-1,0),title='R2 / 俯视：前端朝上',note='重点对应 MiniSE 主键分区与大尺度外骨骼；不是均匀三角网格')
    render('03_left_side.png',names,(230,40,17),scale=47,title='R2 / 左侧：前端在左',note='双侧键有独立运动机构与微动安装；下方开敞，五脚通过上方支架承力')
    render('04_bottom.png',names,(0,40,-230),up=(0,-1,0),title='R2 / 底视：五脚之外无底板',note='视线可见上方曲面、局部机构和悬挂座；这些不是底部平板')
    render('05_five_feet_band.png',['BODY'],(0,40,-230),up=(0,-1,0),title='R2 / 实体裁切：只显示 Z = 0–5 mm',note='对实际 BODY 网格裁切；完整低位体积测试另见 requirements_geometry.json',lowclip=True)
    labels=render('06_exploded.png',names,(145,-115,125),scale=65,title='R2 / 安装分件示意',note='爆炸位移仅用于识别部件；装配方向与顺序见 INSTALLATION.md',explode=True,labels=True)
    legend='\n'.join(f'{i+1}. {n}' for i,(n,_,_) in enumerate(labels))
    (OUT/'exploded_legend.txt').write_text(legend+'\n',encoding='utf-8',newline='\n')
    stages=[('07_install_1_frame.png',['BODY'],'1 / 清理壳体与五脚','去支撑、去毛刺；铰孔按说明校准，先检查五脚共面'),
            ('08_install_2_hardware.png',['BODY']+[n for n in printed if n.endswith('SWITCH_CLAMP')]+hardware,'2 / 安装微动与可拆压条','先后侧、再前侧，分步装入；微动、编码器与金属轴为外购件，不参与 PLA 打印'),
            ('09_install_3_complete.png',names,'3 / 装主键、侧键与滚轮','按轴向安装并固定钢轴；检查全行程与回弹后再接电子模块')]
    for file,parts,title,note in stages:render(file,parts,(130,-110,115),title=title,note=note)
    import cadquery as cq
    for n in ('SENSOR_RESERVED_VOLUME','SENSOR_DOWNWARD_OPTICAL_PATH'):
        s=cq.importers.importStep(str(MESH.parent/'gauges'/f'{n}.step')).val()
        s.exportStl(str(MESH.parent/'gauges'/f'{n}.stl'),tolerance=.025,relative=False)
    render('10_internal_envelopes.png',['BODY']+hardware+['SENSOR_RESERVED_VOLUME','SENSOR_DOWNWARD_OPTICAL_PATH'],
           (125,-95,140),title='R2 / 内部硬件与传感器预留',note='蓝色为通用传感器空间／向下光路；不代表已测得的主板、电池或光学工作高度')
    # One convenient installation sheet, retaining detailed full-resolution files.
    sheet=Image.new('RGB',(1800,1440),'#f8fafb')
    files=['06_exploded.png','07_install_1_frame.png','08_install_2_hardware.png','09_install_3_complete.png']
    for i,file in enumerate(files):
        im=Image.open(OUT/file);im.thumbnail((900,720));sheet.paste(im,((i%2)*900,(i//2)*720))
    sheet.quantize(colors=256,dither=Image.Dither.NONE).save(OUT/'INSTALLATION_SHEET.png',optimize=True)
    print('Rendered',len(list(OUT.glob('*.png'))),'CAD-derived images')


if __name__=='__main__':main()
