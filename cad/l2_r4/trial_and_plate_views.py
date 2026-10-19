"""F2 side-module trial and verified 3MF plate-layout images."""
from pathlib import Path
import json,subprocess,zipfile,os
import numpy as np
import trimesh
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'models/L2_r4';RP=ROOT/'reports/l2_r4';WORK=ROOT/'_support/work/l2_r4/slice';VIEWS=ROOT/'views/l2_r4'
from slice_plate import SL,run,orient,embed_profile,parse_gcode
def main():
    scene=trimesh.Scene();x=10.;rows=[]
    for n in ['SIDE_FRONT_KEY_F2_TRIAL','SIDE_REAR_KEY_F2_TRIAL','SF_RETAINER','SR_RETAINER']:
        if n.endswith('TRIAL'):
            geo=WORK/(n+'.geo');raw=WORK/(n+'.stl');src=OUT/'reference'/(n+'.step')
            import gmsh
            gmsh.initialize();gmsh.option.setNumber('General.NumThreads',1)
            gmsh.model.occ.importShapes(str(src));gmsh.model.occ.synchronize()
            for key,value in [('Mesh.MeshSizeMin',.1),('Mesh.MeshSizeMax',.6),('Mesh.MeshSizeFromCurvature',32),('Mesh.Binary',1)]:gmsh.option.setNumber(key,value)
            gmsh.model.mesh.generate(2);gmsh.write(str(raw));gmsh.finalize()
        else:raw=OUT/'parts'/(n+'.stl')
        m=trimesh.load_mesh(raw);m.merge_vertices(digits_vertex=6);m.update_faces(m.nondegenerate_faces(height=1e-9));m.update_faces(m.unique_faces());m.remove_unreferenced_vertices()
        assert m.is_watertight and len(trimesh.graph.connected_components(m.face_adjacency,nodes=np.arange(len(m.faces)),engine='scipy',min_len=1))==1,n
        rotation=orient(n,m)
        m.apply_translation([x-m.bounds[0,0],10-m.bounds[0,1],-m.bounds[0,2]])
        scene.add_geometry(m,node_name=n,geom_name=n);rows.append(dict(name=n,bounds_mm=m.bounds.tolist(),watertight=True,rotation_y_deg=rotation,rotation_x_deg=90 if n in ('SF_RETAINER','SR_RETAINER') else 0));x+=m.extents[0]+8
    scene.units='mm';raw=WORK/'raw_F2.3mf';raw.write_bytes(trimesh.exchange.threemf.export_3MF(scene));target=OUT/'SIDE_MODULE_F2_TRIAL.3mf'
    ini=Path(__file__).with_name('PLA_0.4_0.20_ESTIMATE.ini')
    run(['--load',ini,'--dont-arrange','--export-3mf','--output',target,raw],'F2_export')
    embed_profile(target,WORK/'full.ini')
    gc=WORK/'F2_validation.gcode';run(['--dont-arrange','--export-gcode','--output',gc,target],'F2_slice')
    (RP/'F2_trial.json').write_text(json.dumps(dict(parts=rows,status='ERGONOMIC_TRIAL_NOT_MECHANISM_CERTIFIED',offset_x_mm=.3,extra_external_ridge=False,scope='Two alternative caps and two retainers; use with the main BODY and actual pins. F2 is an ergonomic comparison, not the accepted production mechanism.',real_slice=parse_gcode(gc)),indent=2))
    # Plot actual triangulated meshes in their saved plate transforms.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    VIEWS.mkdir(exist_ok=True,parents=True);main_info=json.loads((RP/'slice_summary.json').read_text())
    fig,ax=plt.subplots(figsize=(12.75,7.75),layout='constrained');colors=plt.get_cmap('tab10')
    for i,p in enumerate(main_info['placements']):
        m=trimesh.load_mesh(OUT/'parts'/(p['name']+'.stl'))
        if p.get('rotation_x_deg'):m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0]))
        if p['rotation_y_deg']:m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,1,0]))
        m.apply_translation(p['translation_mm'])
        polygons=m.vertices[m.faces][:,:,:2]
        ax.add_collection(PolyCollection(polygons,facecolors=[colors(i%10)],edgecolors='none',alpha=.8))
        bb=m.bounds;ax.text((bb[0,0]+bb[1,0])/2,bb[0,1]-2.0,p['name'],ha='center',va='top',fontsize=6.5)
    ax.set(xlim=(0,255),ylim=(0,155),xlabel='X / mm',ylabel='Y / mm',aspect='equal',title='L2-r4 / actual single-plate placement | 255 x 155 mm | scale 1:1 in 3MF')
    ax.grid(alpha=.15);fig.savefig(VIEWS/'PRINT_PLATE.png',dpi=160);plt.close(fig)
    print('F2 3MF and actual plate projection exported',flush=True)
if __name__=='__main__':main()
