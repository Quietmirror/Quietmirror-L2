"""Render actual diagnostic BRep components; no generated concept art."""
from pathlib import Path
import json
import cadquery as cq
import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2];WORK=ROOT/'_support/work/independent';OUT=ROOT/'views/l2_r1';OUT.mkdir(parents=True,exist_ok=True)
def actor(shape,color,alpha=1):
    vertices,triangles=shape.tessellate(.08,.15);pts=vtk.vtkPoints();pts.SetData(numpy_to_vtk(np.array([v.toTuple() for v in vertices]),deep=True))
    cells=vtk.vtkCellArray()
    for tri in triangles:
        cells.InsertNextCell(3)
        for i in tri:cells.InsertCellPoint(int(i))
    poly=vtk.vtkPolyData();poly.SetPoints(pts);poly.SetPolys(cells)
    norm=vtk.vtkPolyDataNormals();norm.SetInputData(poly);norm.SetFeatureAngle(40);norm.Update()
    mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(norm.GetOutputPort());a=vtk.vtkActor();a.SetMapper(mapper);a.GetProperty().SetColor(*color);a.GetProperty().SetOpacity(alpha);return a
def text(renderer,message,pos,size=22):
    a=vtk.vtkTextActor();a.SetInput(message);a.SetPosition(*pos);a.GetTextProperty().SetFontSize(size);a.GetTextProperty().SetColor(.12,.17,.23);renderer.AddActor2D(a)
def render():
    s=cq.importers.importStep(str(WORK/'document_side_layout_UNCORRECTED.step')).val();solids=s.Solids()
    ren=vtk.vtkRenderer();ren.SetBackground(.97,.98,.99)
    for i,p in enumerate(solids):
        c=(.47,.56,.64) if i==0 else ((.86,.16,.17) if i<3 else (.2,.63,.78))
        ren.AddActor(actor(p,c,1 if i<3 else .55))
    text(ren,'L2 PLAN: SIDE CARRIER CHECK',(28,748),28)
    text(ren,'Literal listed features form 3 disconnected solids',(28,712),22)
    text(ren,'Red: detached supports | Blue: switch / PCB envelopes',(28,42),20)
    text(ren,'Diagnostic geometry only - not a printable release',(28,15),18)
    window=vtk.vtkRenderWindow();window.SetOffScreenRendering(1);window.SetSize(1200,800);window.AddRenderer(ren)
    cam=ren.GetActiveCamera();cam.SetPosition(78,15,61);cam.SetFocalPoint(23.5,56,15);cam.SetViewUp(0,0,1);cam.ParallelProjectionOn();cam.SetParallelScale(20)
    window.Render();shot=vtk.vtkWindowToImageFilter();shot.SetInput(window);shot.Update();writer=vtk.vtkPNGWriter();writer.SetFileName(str(OUT/'K9_side_carrier_diagnostic.png'));writer.SetInputConnection(shot.GetOutputPort());writer.Write();window.Finalize()
    d=json.loads((ROOT/'reports/l2_r1/K4_K5_cross_tie_sections.json').read_text())
    fig,axes=plt.subplots(2,1,figsize=(11,4.6),sharex=True,layout='constrained')
    for ax,y in zip(axes,(54.,67.5)):
        row=next(r for r in d['samples'] if r['y']==y and r['z']==23.)
        for a,b in row['solid_x_intervals']:ax.plot([a,b],[0,0],lw=14,color='#416c89',solid_capstyle='butt')
        ax.axhline(0,color='#b9c5cd',lw=1,zorder=0);ax.set_yticks([]);ax.set_title(f'Exact BRep section: Y={y:g}, Z=23 mm',loc='left');ax.set_ylim(-.6,.6);ax.grid(axis='x',alpha=.2)
    axes[0].annotate('cut across both sides at X = +/-11.3 ... 13.7',xy=(12.5,0),xytext=(0,.4),ha='center',arrowprops=dict(arrowstyle='->',color='#b62929'),color='#b62929')
    axes[1].set_xlabel('Assembly X (mm)');axes[1].set_xlim(-35,35);fig.savefig(OUT/'K4_cross_tie_sections.png',dpi=180);plt.close(fig)
if __name__=='__main__':render()
