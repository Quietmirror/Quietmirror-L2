"""Orthographic technical views from the actual exported assembly, 9 px/mm."""
from pathlib import Path
import json,math
import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk
from PIL import Image,ImageDraw,ImageFont
import cadquery as cq
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'views/l2_r3';MOD=ROOT/'models/L2_r3';RP=ROOT/'reports/l2_r3'
SIZE=(1200,1000);SCALE=9.;FONT='C:/Windows/Fonts/msyh.ttc'
inventory=json.loads((RP/'assembly_inventory.json').read_text())
shapes={};polys={}
def read(n,folder='parts'):
    key=folder+'/'+n
    if key not in shapes:shapes[key]=cq.importers.importStep(str(MOD/folder/(n+'.step'))).val()
    return shapes[key]
def poly(n,s):
    if n in polys:return polys[n]
    vs,ts=s.tessellate(.04,.13);pts=vtk.vtkPoints();pts.SetData(numpy_to_vtk(np.array([v.toTuple() for v in vs]),deep=True));cells=vtk.vtkCellArray()
    for tri in ts:
        cells.InsertNextCell(3)
        for i in tri:cells.InsertCellPoint(int(i))
    pd=vtk.vtkPolyData();pd.SetPoints(pts);pd.SetPolys(cells)
    norm=vtk.vtkPolyDataNormals();norm.SetInputData(pd);norm.SetFeatureAngle(45);norm.Update();result=vtk.vtkPolyData();result.DeepCopy(norm.GetOutput());polys[n]=result;return result
def objects(internal=False):
    result=[]
    for n in inventory['printable']:
        if internal and n=='BODY':continue
        col=(.72,.78,.82) if n=='BODY' else ((.9,.49,.19) if n.startswith('SIDE_') and n.endswith('KEY') else (.28,.39,.46))
        if n=='SIDE_SWITCH_CARRIER':col=(.26,.54,.69)
        result.append((n,read(n),col,.14 if internal and n=='BODY' else (.35 if internal and 'KEY' in n else 1)))
    for n in inventory['H_hardware']:
        col=(.17,.56,.37) if 'PCB' in n else ((.2,.22,.25) if 'BATTERY' in n else (.55,.57,.59))
        if 'SKATE' in n:col=(.92,.92,.90)
        if 'ROUTE' in n:col=(.83,.26,.18)
        result.append((n,read(n,'reference'),col,1))
    return result
def picture(name,objects_,direction,up=(0,0,1),focus=(0,44,16),scale=SCALE,title='',note='',clip=None):
    ren=vtk.vtkRenderer();ren.SetBackground(.97,.98,.99);ren.SetUseDepthPeeling(1);ren.SetMaximumNumberOfPeels(30)
    for n,s,col,alpha in objects_:
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(poly(n,s))
        if clip:
            plane=vtk.vtkPlane();plane.SetOrigin(*clip[0]);plane.SetNormal(*clip[1]);mapper.AddClippingPlane(plane)
        actor=vtk.vtkActor();actor.SetMapper(mapper);actor.GetProperty().SetColor(*col);actor.GetProperty().SetOpacity(alpha);actor.GetProperty().SetSpecular(.2);ren.AddActor(actor)
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetAlphaBitPlanes(1);win.SetMultiSamples(0);win.SetSize(*SIZE);win.AddRenderer(ren)
    c=ren.GetActiveCamera();c.SetFocalPoint(*focus);d=np.array(direction,dtype=float);d=d/np.linalg.norm(d)*250;c.SetPosition(*(np.array(focus)+d));c.SetViewUp(*up);c.ParallelProjectionOn();c.SetParallelScale(SIZE[1]/(2*scale));ren.ResetCameraClippingRange();win.Render()
    capture=vtk.vtkWindowToImageFilter();capture.SetInput(win);capture.Update();writer=vtk.vtkPNGWriter();path=OUT/(name+'.png');writer.SetFileName(str(path));writer.SetInputConnection(capture.GetOutputPort());writer.Write();win.Finalize()
    im=Image.open(path).convert('RGB');draw=ImageDraw.Draw(im);font=ImageFont.truetype(FONT,28);small=ImageFont.truetype(FONT,20)
    draw.rectangle((0,0,1200,100),fill='#edf2f5');draw.text((26,16),title,font=font,fill='#1c3340');draw.text((26,58),note,font=small,fill='#465b66')
    y=953;draw.line((32,y,32+10*scale,y),fill='#243b48',width=3);draw.line((32,y-6,32,y+6),fill='#243b48',width=2);draw.line((32+10*scale,y-6,32+10*scale,y+6),fill='#243b48',width=2)
    draw.text((145,936),'10 mm | L2-r3 INCOMPLETE | '+str(scale)+' px/mm',font=small,fill='#334e5b')
    im.save(path);print('VIEW',name,flush=True)
def main():
    OUT.mkdir(exist_ok=True);obj=objects();inside=objects(True)
    definitions=[('FRONT',(0,-1,0),(0,0,1),'前视 −Y','X / Z'),('BACK',(0,1,0),(0,0,1),'后视 +Y','X / Z'),('LEFT',(-1,0,0),(0,0,1),'左视 −X','Y / Z'),('RIGHT',(1,0,0),(0,0,1),'右视 +X · 侧键侧','Y / Z'),('TOP',(0,0,1),(0,-1,0),'俯视 +Z','X / Y'),('BOTTOM',(0,0,-1),(0,1,0),'底视 −Z','X / Y')]
    b=read('BODY').BoundingBox();dims=f'BODY {b.ylen:.3f} × {b.xlen:.3f} × {b.zlen:.3f} mm（长×宽×高）'
    for n,d,u,t,axes in definitions:
        picture('H_'+n,obj,d,u,title='Quietmirror L2-r3 | '+t,note=axes+' | '+dims)
        picture('INSIDE_'+n,inside,d,u,title='内部包络 | '+t,note='去掉 BODY；电子元件为估计包络，未认证真实装配')
    picture('H_ISO_FRONT',obj,(1,-1,1),title='Quietmirror L2-r3 | 前侧斜视',note='实际导出模型；橙色侧键、蓝色托架、绿色参考电路板')
    picture('H_ISO_REAR',obj,(-1,1,.8),title='Quietmirror L2-r3 | 后侧斜视',note='保留原六孔和五个共面脚贴平台')
    for name,origin,normal in [('X23',(23,0,0),(-1,0,0)),('Y50p25',(0,50.25,0),(0,1,0)),('Y64p45',(0,64.45,0),(0,1,0)),('Z16p6',(0,0,16.6),(0,0,-1))]:
        picture('SECTION_'+name,obj,(1,-1,.7),title='实际组件剖视 | '+name,note='剖切展示内部路径；不得作为实际供体尺寸证明',clip=(origin,normal))
    from side_module import KEYS
    for state,fraction in [('REST',0),('TRIGGER',.83),('STOP',1)]:
        shown=[]
        for n,s,c,a in inside:
            k=next((k for k in KEYS if k['name']==n),None)
            if k:s=s.rotate((29,k['hinge_y'],0),(29,k['hinge_y'],1),k['angle']*fraction);n+='_'+state
            shown.append((n,s,c,a))
        picture('SIDE_'+state,shown,(1,-.12,.12),focus=(24,57,16),scale=20,title='侧键机构 | '+state,note='触发图为名义近似姿态；实际触发点取决于微动与 PET 调整')
    overlay=[o for o in inside if o[0] not in [k['name'] for k in KEYS]]
    for k in KEYS:
        for state,fraction,col in [('REST',0,(.1,.5,.8)),('TRIGGER',.83,(.9,.55,.12)),('STOP',1,(.8,.18,.2))]:
            s=read(k['name']).rotate((29,k['hinge_y'],0),(29,k['hinge_y'],1),k['angle']*fraction)
            overlay.append((k['name']+'_'+state,s,col,.4))
    picture('SIDE_MOTION_OVERLAY',overlay,(0,0,1),up=(0,1,0),focus=(25,57,16),scale=20,title='侧键动作叠图 | 静止 / 触发示意 / 止挡',note='蓝=静止，黄=名义触发，红=止挡；实际触发角需微动实测')
    old=[]
    metrics=json.loads((ROOT/'reports/rebuild_r3_2/cad_metrics.json').read_text())
    for n,r in metrics.items():
        if r['printable']:
            s=cq.importers.importStep(str(ROOT/'exports/rebuild_r3_2/assembly'/(n+'.step'))).val();old.append(('R32_'+n,s,(.68,.73,.77),1))
    picture('R32_BASELINE',old,(1,-1,1),title='对照 | R3.2 原版',note='与 r3 斜视相同相机和比例')
    comparisons=Image.new('RGB',(2400,3000),'white')
    for row,n in enumerate(['TOP','RIGHT','BOTTOM']):
        entry=next(v for v in definitions if v[0]==n)
        picture('R32_'+n,old,entry[1],entry[2],title='R3.2 原版 | '+entry[3],note='与 r3 对应视图相同比例、相机')
        comparisons.paste(Image.open(OUT/('R32_'+n+'.png')),(0,1000*row))
        comparisons.paste(Image.open(OUT/('H_'+n+'.png')),(1200,1000*row))
    comparisons.save(OUT/'R32_VS_L2_r3_TOP_RIGHT_BOTTOM.png')
    sheet=Image.new('RGB',(4800,3000),'#edf2f5')
    for name,col,row in [('TOP',1,0),('LEFT',0,1),('FRONT',1,1),('RIGHT',2,1),('BACK',3,1),('BOTTOM',1,2)]:sheet.paste(Image.open(OUT/('H_'+name+'.png')),(1200*col,1000*row))
    sheet.paste(Image.open(OUT/'H_ISO_FRONT.png'),(3600,0));d=ImageDraw.Draw(sheet);font=ImageFont.truetype(FONT,50);small=ImageFont.truetype(FONT,32)
    d.text((70,130),'Quietmirror L2-r3',font=font,fill='#203d4b');d.text((70,220),'第三角投影 · 统一 9 px/mm',font=small,fill='#203d4b');d.text((70,290),'INCOMPLETE / 预发布',font=small,fill='#a45524');d.text((70,360),'所有图像均来自实际 CAD 组件',font=small,fill='#455e69');d.text((70,420),'供体与电子元件仍为估计包络',font=small,fill='#455e69')
    sheet.save(OUT/'L2_r3_H_SIX_VIEWS_SHEET.png')
    compare=Image.new('RGB',(2400,1000),'white');compare.paste(Image.open(OUT/'R32_BASELINE.png'),(0,0));compare.paste(Image.open(OUT/'H_ISO_FRONT.png'),(1200,0));compare.save(OUT/'R32_VS_L2_r3.png')
if __name__=='__main__':main()
