"""Render actual CAD-derived STL meshes; no generative image substitute."""
from pathlib import Path
import json,math
import vtk
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'views';OUT.mkdir(exist_ok=True)
FONT='C:/Windows/Fonts/msyh.ttc'
def actor(path,color,opacity=1):
    reader=vtk.vtkSTLReader();reader.SetFileName(str(path));reader.Update()
    normal=vtk.vtkPolyDataNormals();normal.SetInputConnection(reader.GetOutputPort());normal.SetFeatureAngle(40);normal.SplittingOn();normal.ConsistencyOn()
    mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normal.GetOutputPort())
    a=vtk.vtkActor();a.SetMapper(mapper);a.GetProperty().SetColor(*color);a.GetProperty().SetOpacity(opacity);a.GetProperty().SetDiffuse(.7);a.GetProperty().SetAmbient(.18);a.GetProperty().SetSpecular(.12);a.GetProperty().SetSpecularPower(24)
    return a
def render(name,paths,camera,up=(0,0,1),focus=(0,-44,13),scale=55,title='',subtitle='',env=False,version='V0.1',envfile=None,footer='固定试握件 · 非电子装配验收'):
    renderer=vtk.vtkRenderer();renderer.SetViewport(0,.07,1,.89);renderer.SetBackground(.94,.95,.96);renderer.SetBackground2(.985,.99,.995);renderer.GradientBackgroundOn()
    for path,col,opacity in paths:renderer.AddActor(actor(path,col,opacity))
    if env:
        ed=json.loads((envfile or ROOT/'reports/envelope_interferences.json').read_text())['envelopes']
        for e in ed:
            cube=vtk.vtkCubeSource();cube.SetXLength(e['size'][0]);cube.SetYLength(e['size'][1]);cube.SetZLength(e['size'][2]);cube.SetCenter(*e['center'])
            mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(cube.GetOutputPort());a=vtk.vtkActor();a.SetMapper(mapper)
            col=e['color'];a.GetProperty().SetColor(*[int(col[i:i+2],16)/255 for i in (1,3,5)]);a.GetProperty().SetOpacity(.3);a.GetProperty().EdgeVisibilityOn();a.GetProperty().SetLineWidth(1.4);renderer.AddActor(a)
    cam=renderer.GetActiveCamera();cam.SetPosition(*camera);cam.SetFocalPoint(*focus);cam.SetViewUp(*up);cam.ParallelProjectionOn();cam.SetParallelScale(scale)
    renderer.ResetCameraClippingRange()
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.AddRenderer(renderer);win.SetSize(1500,1200);win.SetMultiSamples(8);win.Render()
    capture=vtk.vtkWindowToImageFilter();capture.SetInput(win);capture.SetInputBufferTypeToRGB();capture.ReadFrontBufferOff();capture.Update()
    writer=vtk.vtkPNGWriter();writer.SetFileName(str(OUT/name));writer.SetInputConnection(capture.GetOutputPort());writer.Write();win.Finalize()
    im=Image.open(OUT/name);draw=ImageDraw.Draw(im);draw.rectangle((0,0,1500,131),fill='#f8fafc')
    draw.text((45,20),title,font=ImageFont.truetype(FONT,31),fill='#18293e');draw.text((46,69),subtitle,font=ImageFont.truetype(FONT,20),fill='#536779')
    draw.rectangle((0,1116,1500,1200),fill='#f8fafc');draw.text((45,1160),f'QUIETMIRROR   /   {version}   /   mm   /   {footer}',font=ImageFont.truetype(FONT,19),fill='#536779');im.save(OUT/name)

def main():
    p=ROOT/'exports/quietmirror_fingertip_V0.1.stl';paths=[(p,(.5,.65,.7),1)]
    render('01_isometric.png',paths,(-140,160,140),title='V0.1 / 右手指握试握件',subtitle='实际 STL 渲染；主键、侧键、滚轮均固定。拇指侧有两个触达凸台。',scale=48)
    render('02_top.png',paths,(0,-44,220),up=(0,1,0),title='俯视 / 前端向上',subtitle='左侧为拇指；右侧为无名指、小指。接触面不开孔，后部开放。',scale=52)
    render('03_left_side.png',paths,(-220,-44,14),title='左侧 / 拇指侧',subtitle='左为前端，右为后部；浅凹接触区 + 两个固定侧键凸台。',scale=40)
    render('04_bottom.png',paths,(0,-44,-220),up=(0,1,0),title='底视 / 五个圆形脚贴平台',subtitle='脚贴平台 Ø8.8；全部安装面 Z=0；只粘五个圆点脚贴。',scale=52)
    render('05_right_side.png',paths,(220,-44,14),title='右侧 / 无名指、小指支撑',subtitle='左为后部，右为前端；下缘有轻微防拖地托边。',scale=40)
    render('06_envelopes.png',[(p,(.66,.7,.74),.12)],(-130,150,130),env=True,title='电子参考包络 / 不参与打印',subtitle='彩色体为估计净空；不是供体实测、安装孔位或装配许可。详见包络报告。',scale=50)
    refs=ROOT/'.reference'
    if not (refs/'olliebella/STLs/shell.stl').exists():return
    render('ref_olliebella.png',[(refs/'olliebella/STLs/shell.stl',(.73,.78,.8),.4),(refs/'olliebella/STLs/base.stl',(.27,.48,.58),1),(refs/'olliebella/STLs/rear skake.stl',(.27,.48,.58),1),(refs/'olliebella/STLs/m1.stl',(.91,.67,.3),1),(refs/'olliebella/STLs/m2.stl',(.91,.67,.3),1),(refs/'olliebella/STLs/wheel.stl',(.53,.61,.63),1)],(-100,120,95),focus=(0,12,12),scale=42,title='参考实物网格 / badjeff · olliebella',subtitle='实际读取上游 STL；此图仅用于来源审阅，不是本项目试握件。')
    render('ref_kotinos.png',[(refs/'Kotinos/STL/Kotinos.stl',(.71,.77,.82),1)],(-165,-75,135),focus=(-43,78,16),scale=58,title='参考实物网格 / pseudoku · Kotinos',subtitle='实际读取 Kotinos.stl；指部接触面和开放承力骨架，原配 HSK Pro。')
if __name__=='__main__':main()
