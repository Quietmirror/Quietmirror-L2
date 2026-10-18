"""Offscreen CPU renders and installation figures from the actual R3_1 meshes."""
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
OUT=ROOT/'views/rebuild_r3_1';OUT.mkdir(exist_ok=True,parents=True)
MESH=ROOT/'exports/rebuild_r3_1/assembly'
FONT='C:/Windows/Fonts/msyh.ttc'
COLORS={'BODY':(.18,.38,.43),'LEFT_KEY':(.72,.81,.77),'RIGHT_KEY':(.72,.81,.77),
        'WHEEL':(.17,.21,.23),'SIDE_FRONT_KEY':(.84,.59,.25),'SIDE_REAR_KEY':(.84,.59,.25)}


def render(name,names,camera,up=(0,0,1),scale=51,title='',note='',explode=False,labels=False,lowclip=False,transparent_body=False,focus=None):
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
        if n=="BODY" and transparent_body:a.GetProperty().SetOpacity(.16)
        renderer.AddActor(a)
        b=r.GetOutput().GetBounds();centers.append((n,[(b[0]+b[1])/2+delta[0],(b[2]+b[3])/2+delta[1],(b[4]+b[5])/2+delta[2]]))
    cam=renderer.GetActiveCamera();cam.SetPosition(*camera);cam.SetFocalPoint(*(focus or (0,40,18 if explode else 13)));cam.SetViewUp(*up);cam.ParallelProjectionOn();cam.SetParallelScale(scale)
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
    d.text((48,1137),'R3.1  /  mm  /  实际 CAD 网格 · Fenrir 参考独立重建 · 短脚版 · 原 R3 坐标基准 · 电子图中的 EST 为估计包络',font=ImageFont.truetype(FONT,21),fill='#506776')
    for idx,(n,x,y) in enumerate(positions):
        if not(140<y<1080):continue
        d.ellipse((x-14,y-14,x+14,y+14),fill='#f8fafb',outline='#1c4857',width=2)
        d.text((x-6,y-12),str(idx+1),font=ImageFont.truetype(FONT,17),fill='#163645')
    im.quantize(colors=256,dither=Image.Dither.NONE).save(OUT/name,optimize=True)
    return positions

def main():
    global MESH
    import shutil
    metrics=json.loads((ROOT/'reports/rebuild_r3_1/cad_metrics.json').read_text())
    data=json.loads((ROOT/'cad/rebuild_r3_1/electronics.json').read_text())
    dest=SUP/'work/fenrir_rebuild_r3_1/render_meshes';dest.mkdir(parents=True,exist_ok=True)
    for folder in ['assembly','gauges','electronics/custom','electronics/reserves','electronics/routes','electronics/donor_blocked']:
        for f in (ROOT/'exports/rebuild_r3_1'/folder).glob('*.stl'):shutil.copyfile(f,dest/f.name)
    MESH=dest;names=list(metrics)
    COLORS.update({'WHEEL_CARRIER':(.91,.57,.18),'ENCODER_ADAPTER_PCB_EST':(.12,.49,.36),'USB_ADAPTER_PCB_REFERENCE':(.12,.49,.36),'UNMEASURED_DONOR_SLAB':(.84,.15,.15)})
    palette={'pcb':(.15,.52,.39),'chip':(.26,.28,.32),'sensor':(.30,.34,.36),'battery':(.40,.56,.76),'lens':(.49,.27,.69),'connector':(.85,.67,.31),'antenna':(.92,.67,.17),'switch':(.33,.38,.43)}
    for row in data['custom']:COLORS[row['name']]=palette[row['kind']]
    for row in data['routes']:COLORS[row['name']]=(.90,.45,.13)
    render('01_overview.png',names,(125,-95,125),title='R3.1 / 五脚缩短并对齐镜头预留下平面',note='五脚粘贴面上移 5.2 mm；Ø8 mm 接触面；上下结构仍为一个实体')
    render('02_top.png',names,(0,40,230),up=(0,-1,0),title='R3.1 / 俯视 · 鼠标前端向上',note='左右主键触感面、宽度、铰链位置保持不变；内部限位按微动轴线重新计算')
    render('03_side.png',names,(230,40,17),scale=47,title='R3.1 / 左侧 · 鼠标前端在左',note='脚贴粘贴面 Z5.2；底框最低 Z5.0；0.5 mm 脚贴示例下离地 0.3 mm')
    render('04_bottom.png',names,(0,40,-230),up=(0,-1,0),title='R3.1 / 底视 · 五个共面脚贴平台',note='五个 Ø8 mm 粘贴面共面；保留开放底部；仅局部脚点与支柱缩短')
    est=[r['name'] for r in data['custom']];routes=[r['name'] for r in data['routes']]
    internals=[n for n in names if n not in ('LEFT_KEY','RIGHT_KEY','WHEEL')]
    render('05_custom_estimates.png',internals+est+routes,(135,-80,145),title='R3.1 / PAW3950 分体方案 · 估计空间布局',note='绿色：板卡　蓝色：18×22×6 电池包络　紫色：镜头包络　橙色：部分线束通道',transparent_body=True)
    render('06_atk_blocked.png',internals+['UNMEASURED_DONOR_SLAB'],(125,-95,130),title='R3.1 / ATK 整板方案 · 当前假设不通过',note='红色 36×50×1.2 mm 为历史假设板；与内部机构相交，不是 ATK 实测外形或可装配成品',transparent_body=True)
    wheelparts=['WHEEL_CARRIER','WHEEL','ENCODER_EC10E_HOUSING','ENCODER_EC10E_ROTOR','ENCODER_ADAPTER_PCB_EST']+[n for n in names if n.startswith('ENCODER_M2') or n.startswith('ENCODER_WASHER')]
    render('07_encoder_mount.png',wheelparts,(60,-20,70),scale=21,focus=(3,32,14),title='R3.1 / 编码器小板与滚轮载架',note='小板自定外形 + 两枚 M2×3；焊脚通道、螺钉、按压包络一起检查，板上电路未设计')
    render('08_internal_top.png',internals+est+routes,(0,45,230),up=(0,-1,0),title='R3.1 / 内部俯视 · 估计板卡与机械件同场核对',note='没有隐藏原机械安装座；这些包络通过不代表实际供体板、光学高度或续航已经通过',transparent_body=True)
    render('09_reserved_datum.png',['BODY','SENSOR_RESERVED_VOLUME'],(230,40,14),scale=47,title='R3.1 / 脚贴粘贴面与镜头预留下平面对齐',note='蓝色：18×18×9 mm 预留空间，下平面 Z5.2；五个脚点底面同为 Z5.2',transparent_body=True)
    sheet=Image.new('RGB',(1800,1440),'#f8fafb')
    for i,file in enumerate(['01_overview.png','02_top.png','03_side.png','04_bottom.png']):
        im=Image.open(OUT/file);im.thumbnail((900,720));sheet.paste(im,((i%2)*900,(i//2)*720))
    sheet.save(OUT/'R3_1_FOUR_VIEWS.png',optimize=True)
    print('R3_1 CAD views rendered',flush=True)

if __name__=='__main__':main()

