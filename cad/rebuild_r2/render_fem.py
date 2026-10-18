"""Render actual completed FEM nodal displacement fields, with explicit 10x warp."""
from pathlib import Path
import ctypes,json,os
os.environ.setdefault('LP_NUM_THREADS','2')
os.environ.setdefault('OMP_NUM_THREADS','2')
ROOT=Path(__file__).resolve().parents[2];SUP=ROOT.parent/'_support'
mesa=SUP/'tools/PrusaSlicer/PrusaSlicer-2.9.6/mesa/opengl32.dll'
if mesa.exists():
    os.add_dll_directory(str(mesa.parent));ctypes.WinDLL(str(mesa))
try:ctypes.windll.kernel32.SetPriorityClass(ctypes.c_void_p(-1),0x4000)
except Exception:pass
import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray
from PIL import Image,ImageDraw,ImageFont

def main():
    report=json.loads((ROOT/'reports/rebuild_r2/fem_results.json').read_text(encoding='utf8'))
    fine=report['mesh_levels'][-1];size=fine['size_mm']
    directory=SUP/'work/fenrir_rebuild_r2/fem/body'/f'h{size:g}_{report["source_step_sha256"][:10]}'
    m=np.load(directory/'mesh_arrays.npz');xyz=m['xyz'];faces=m['boundary_faces']
    triangles=np.concatenate([faces[:,i] for i in ((0,3,5),(3,1,4),(5,4,2),(3,4,5))])
    cells=np.column_stack([np.full(len(triangles),3),triangles]).astype(np.int64)
    palette=vtk.vtkColorTransferFunction()
    for x,r,g,b in ((0,.10,.18,.52),(.25,.05,.49,.70),(.5,.18,.73,.56),(.75,.97,.80,.20),(1,.83,.12,.08)):
        palette.AddRGBPoint(x,r,g,b)
    out=Image.new('RGB',(2000,1620),'#f8fafb');draw=ImageDraw.Draw(out)
    font=lambda n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
    draw.text((40,20),'R2 / 实际有限元位移场',font=font(34),fill='#173342')
    draw.text((40,76),f'最终 {size:g} mm 网格 · E=1500 MPa / ν=0.35 · 变形显示放大 10 倍，色标为真实位移 mm',font=font(23),fill='#506776')
    names={'palm_down_20N':'掌压 20 N','left_main_root_down_5N':'左主键根座 5 N',
           'side_1_switch_fence_inward_5N':'前侧键背挡板 5 N','side_2_switch_fence_inward_5N':'后侧键背挡板 5 N'}
    summary=[]
    for i,res in enumerate(q for q in fine['results'] if q['material']['E_MPa']==1500):
        arr=np.load(directory/f'E1500_{res["case"]["name"]}'/'result_arrays.npz')
        assert np.array_equal(arr['node_ids'],m['node_ids'])
        u=arr['displacement_mm'];norm=np.linalg.norm(u,axis=1);peak=float(norm.max())
        assert abs(peak-res['maximum_displacement_mm'])<1e-9
        def poly(points):
            p=vtk.vtkPoints();p.SetData(numpy_to_vtk(points,deep=True))
            c=vtk.vtkCellArray();c.SetCells(len(cells),numpy_to_vtkIdTypeArray(cells.ravel(),deep=True))
            s=vtk.vtkPolyData();s.SetPoints(p);s.SetPolys(c);return s
        surf=poly(xyz+10*u);values=numpy_to_vtk(norm,deep=True);values.SetName('U_mm');surf.GetPointData().SetScalars(values)
        lut=vtk.vtkLookupTable();lut.SetNumberOfTableValues(256);lut.SetRange(0,peak)
        for j in range(256):lut.SetTableValue(j,*palette.GetColor(j/255),1)
        lut.Build();mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(surf);mapper.SetLookupTable(lut);mapper.SetScalarRange(0,peak)
        a=vtk.vtkActor();a.SetMapper(mapper);a.GetProperty().SetAmbient(.50);a.GetProperty().SetDiffuse(.50)
        ghostmap=vtk.vtkPolyDataMapper();ghostmap.SetInputData(poly(xyz));ghostmap.ScalarVisibilityOff()
        ghost=vtk.vtkActor();ghost.SetMapper(ghostmap);ghost.GetProperty().SetColor(.45,.51,.55);ghost.GetProperty().SetOpacity(.14)
        ren=vtk.vtkRenderer();ren.SetBackground(.965,.978,.98);ren.AddActor(a);ren.AddActor(ghost)
        cam=ren.GetActiveCamera();cam.SetPosition(105,-130,98);cam.SetFocalPoint(0,42,14);cam.SetViewUp(0,0,1);cam.ParallelProjectionOn();cam.SetParallelScale(54);ren.ResetCameraClippingRange()
        win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.AddRenderer(ren);win.SetSize(950,570);win.SetMultiSamples(0);win.Render()
        shot=vtk.vtkWindowToImageFilter();shot.SetInput(win);shot.SetInputBufferTypeToRGB();shot.ReadFrontBufferOff();shot.Update()
        from vtk.util.numpy_support import vtk_to_numpy
        pixels=vtk_to_numpy(shot.GetOutput().GetPointData().GetScalars()).reshape(570,950,3)[::-1].copy()
        x=(i%2)*1000+25;y=(i//2)*700+145;out.paste(Image.fromarray(pixels),(x,y+65));win.Finalize()
        draw.text((x+15,y),names[res['case']['name']]+f'  /  最大 {peak:.4f} mm',font=font(27),fill='#173342')
        for j in range(600):
            color=tuple(round(c*255) for c in palette.GetColor(j/599));draw.line((x+155+j,y+639,x+155+j,y+659),fill=color)
        draw.text((x+150,y+664),'0',font=font(18),fill='#506776');draw.text((x+700,y+664),f'{peak:.4f} mm',font=font(18),fill='#506776')
        summary.append(dict(case=res['case']['name'],maximum_displacement_mm=peak,warp_scale=10,
            source_dat_sha256=res['dat_sha256'],negative_foot_reactions=res['negative_foot_reactions']))
    draw.text((40,1553),'灰色为未变形轮廓；脚面为双向夹具支承。负反力对应真实脚点可能离地，不是桌面接触或成品强度认证。',font=font(23),fill='#506776')
    path=ROOT/'views/rebuild_r2/11_fem_displacement.png';out.save(path,optimize=True)
    (ROOT/'reports/rebuild_r2/fem_figure.json').write_text(json.dumps(dict(source_step_sha256=report['source_step_sha256'],mesh_mm=size,panels=summary),indent=2),encoding='utf8')
    print(path)

if __name__=='__main__':main()
