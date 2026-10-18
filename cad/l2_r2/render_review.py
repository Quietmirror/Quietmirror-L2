"""Render actual review STEP files and measured results, not concept artwork."""
from pathlib import Path
import json
import numpy as np
import cadquery as cq
import vtk
from vtk.util.numpy_support import numpy_to_vtk
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'views/l2_r2';EXP=ROOT/'exports/l2_r2_diagnostic'

def load(n):return cq.importers.importStep(str(EXP/(n+'.step'))).val()
def actor(shape,color,alpha=1):
    vertices,triangles=shape.tessellate(.05,.12)
    pts=vtk.vtkPoints();pts.SetData(numpy_to_vtk(np.array([v.toTuple() for v in vertices]),deep=True))
    cells=vtk.vtkCellArray()
    for tri in triangles:
        cells.InsertNextCell(3)
        for i in tri:cells.InsertCellPoint(int(i))
    poly=vtk.vtkPolyData();poly.SetPoints(pts);poly.SetPolys(cells)
    norm=vtk.vtkPolyDataNormals();norm.SetInputData(poly);norm.SetFeatureAngle(40);norm.Update()
    mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(norm.GetOutputPort())
    a=vtk.vtkActor();a.SetMapper(mapper);a.GetProperty().SetColor(*color);a.GetProperty().SetOpacity(alpha)
    return a
def label(r,t,pos,size=20):
    a=vtk.vtkTextActor();a.SetInput(t);a.SetPosition(*pos);a.GetTextProperty().SetFontSize(size);a.GetTextProperty().SetColor(.12,.17,.22);r.AddActor2D(a)
def picture(name,objects,cam_pos,focus,scale,title,subtitle,legend,up=(0,0,1)):
    r=vtk.vtkRenderer();r.SetBackground(.97,.98,.99)
    for shape,col,alpha in objects:r.AddActor(actor(shape,col,alpha))
    label(r,title,(28,744),28);label(r,subtitle,(28,709),19)
    label(r,legend,(28,44),19);label(r,'Diagnostic reference only | dimensions in mm | not a printable release',(28,17),18)
    w=vtk.vtkRenderWindow();w.SetOffScreenRendering(1);w.SetSize(1200,800);w.AddRenderer(r)
    c=r.GetActiveCamera();c.SetPosition(*cam_pos);c.SetFocalPoint(*focus);c.SetViewUp(*up);c.ParallelProjectionOn();c.SetParallelScale(scale)
    w.Render();shot=vtk.vtkWindowToImageFilter();shot.SetInput(w);shot.Update()
    writer=vtk.vtkPNGWriter();writer.SetFileName(str(OUT/(name+'.png')));writer.SetInputConnection(shot.GetOutputPort());writer.Write();w.Finalize()
def main():
    OUT.mkdir(exist_ok=True)
    carrier=load('R2_CARRIER_DIAGNOSTIC');sf=load('SF_SWITCH_ENVELOPE');sr=load('SR_SWITCH_ENVELOPE');pcb=load('SIDE_IO_PCB_ENVELOPE')
    picture('R2_carrier_layout',[(carrier,(.22,.48,.64),1),(sf,(.76,.77,.79),.5),(sr,(.76,.77,.79),.5),(pcb,(.18,.65,.47),.85)],
            (82,20,65),(23.5,56,15),21,'R2 / SIDE CARRIER','One connected BRep solid; clearance review still has failures',
            'Blue: carrier | Gray: switch envelopes | Green: side PCB')
    collision=load('R2_COLLISION_REGIONS');hinge=load('MAIN_OUTER_HINGE_REFERENCE');skin=load('LOW_MOTHER_SKIN_REFERENCE')
    picture('R2_clearance_failures',[(carrier,(.22,.48,.64),.35),(hinge,(.95,.55,.16),.4),(skin,(.63,.68,.73),.2),(collision,(.9,.08,.12),1)],
            (23.5,55,110),(23.5,55,13),29,'R2 / CLEARANCE FAILURES','Plan-view projection: front bridge / hinge and outer bridge / sidewall regions',
            'Red: exact overlap regions | Orange: retained hinge | Gray: sidewall',up=(0,1,0))
    audit=json.loads((ROOT/'reports/l2_r2/K9_r2_contact_audit.json').read_text())
    fig,axs=plt.subplots(1,2,figsize=(11.4,4.2),layout='constrained')
    for ax,row in zip(axs,audit['ears']):
        xy=np.array(row['top_profile']);ax.plot(xy[:,0],xy[:,1],lw=2.6,label='BRep ear + rounded arm top',color='#356f91')
        ax.axhline(row['document_leg_bottom_z'],color='#ba3b36',ls='--',label='r2 leg bottom')
        ax.axhline(10.75,color='#8a969d',lw=.9,ls=':',label='planar land Z10.75')
        ax.set_title(f"{row['name'].upper()} | section X={row['top_profile_x']:.3f}",loc='left')
        ax.set(xlabel='Y (mm)',ylabel='Z (mm)',ylim=(10.45,10.86));ax.grid(alpha=.2)
        ax.legend(loc='lower right',fontsize=8)
    fig.suptitle('A point height is not a flat mounting datum',fontsize=15)
    fig.savefig(OUT/'R2_ear_contact_sections.png',dpi=180);plt.close(fig)
    paths=[ROOT/f'reports/l2_r2/K3_r2_baseline_{s}.json' for s in ('2.4','2','1.6')]
    data=[json.loads(p.read_text()) for p in paths if p.exists()]
    fig,ax=plt.subplots(figsize=(11,4.8),layout='constrained')
    for d in data:
        vals=[r['deviation_percent'] for r in d['results']]
        if all(v is not None for v in vals):ax.plot(np.arange(8),vals,'o-',lw=1.7,label=f"{d['inputs']['mesh_mm']} mm mesh")
    ax.axhspan(-3,3,color='#dfeddf',label='Document tolerance +/-3%');ax.axhline(0,color='#8c999e',lw=.9)
    ax.set_xticks(np.arange(8),['Palm','Main L','Main R','Side F','Side R','Grip','Press A','Press B'])
    ax.set_ylabel('Difference from corresponding document baseline (%)');ax.set_title('R3.2 baseline reproduction | not final L2 stiffness',loc='left',fontsize=15)
    ax.grid(axis='y',alpha=.2);ax.legend(ncol=1,loc='upper left')
    fig.savefig(OUT/'R2_FEM_baseline_comparison.png',dpi=180);plt.close(fig)
    print('Rendered four review figures',flush=True)

if __name__=='__main__':main()
