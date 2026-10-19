"""F2 side-module trial and verified 3MF plate-layout images."""
from pathlib import Path
import json,subprocess,zipfile
import numpy as np
import trimesh
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'models/L2_r3';RP=ROOT/'reports/l2_r3';WORK=ROOT/'_support/work/l2_r3/slice';VIEWS=ROOT/'views/l2_r3'
GMSH=ROOT/'_support/tools/Gmsh/gmsh-4.15.2-Windows64/gmsh.exe'
SL=ROOT/'_support/tools/PrusaSlicer/PrusaSlicer-2.9.6/prusa-slicer-console.exe'
def main():
    scene=trimesh.Scene();x=10.;rows=[]
    for n in ['SIDE_FRONT_KEY_F2_TRIAL','SIDE_REAR_KEY_F2_TRIAL','SIDE_SWITCH_CARRIER']:
        if n.endswith('TRIAL'):
            geo=WORK/(n+'.geo');raw=WORK/(n+'.stl');src=OUT/'reference'/(n+'.step')
            geo.write_text(f'SetFactory("OpenCASCADE");\nMerge "{src.as_posix()}";\nMesh.MeshSizeMin=.1;\nMesh.MeshSizeMax=.6;\nMesh.MeshSizeFromCurvature=32;\nMesh.Binary=1;\n')
            with (WORK/(n+'.log')).open('w') as f:subprocess.run([str(GMSH),str(geo),'-2','-format','stl','-o',str(raw),'-nt','1'],stdout=f,stderr=subprocess.STDOUT,check=True)
        else:raw=OUT/'parts'/(n+'.stl')
        m=trimesh.load_mesh(raw);m.merge_vertices(digits_vertex=6);m.update_faces(m.nondegenerate_faces(height=1e-9));m.update_faces(m.unique_faces());m.remove_unreferenced_vertices()
        assert m.is_watertight and len(m.split())==1,n
        m.apply_translation([x-m.bounds[0,0],10-m.bounds[0,1],-m.bounds[0,2]])
        scene.add_geometry(m,node_name=n,geom_name=n);rows.append(dict(name=n,bounds_mm=m.bounds.tolist(),watertight=True));x+=m.extents[0]+8
    scene.units='mm';raw=WORK/'raw_F2.3mf';raw.write_bytes(trimesh.exchange.threemf.export_3MF(scene));target=OUT/'SIDE_MODULE_F2_TRIAL.3mf'
    ini=Path(__file__).with_name('PLA_0.4_0.20_ESTIMATE.ini')
    with (WORK/'F2_export.log').open('w') as f:subprocess.run([str(SL),'--sw-renderer','--threads','1','--load',str(ini),'--dont-arrange','--export-3mf','--output',str(target),str(raw)],stdout=f,stderr=subprocess.STDOUT,check=True)
    with zipfile.ZipFile(OUT/'L2_r3_H_ALL_PARTS_SINGLE_PLATE.3mf') as z:cfg=z.read('Metadata/Slic3r_PE.config')
    with zipfile.ZipFile(target) as z:data={n:z.read(n) for n in z.namelist()}
    data['Metadata/Slic3r_PE.config']=cfg
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in data.items():z.writestr(n,b)
    (RP/'F2_trial.json').write_text(json.dumps(dict(parts=rows,status='ERGONOMIC_TRIAL_NOT_MECHANISM_CERTIFIED',offset_x_mm=.3,extra_external_ridge=False,scope='Two alternative caps plus shared carrier; use with the main BODY and actual pins. No claim of separate F2 clearance acceptance.'),indent=2))
    # Plot actual triangulated meshes in their saved plate transforms.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    main_info=json.loads((RP/'slice_summary.json').read_text())
    fig,ax=plt.subplots(figsize=(12.75,7.75),layout='constrained');colors=plt.get_cmap('tab10')
    for i,p in enumerate(main_info['placements']):
        m=trimesh.load_mesh(OUT/'parts'/(p['name']+'.stl'))
        if p['rotation_y_deg']:m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,1,0]))
        m.apply_translation(p['translation_mm'])
        polygons=m.vertices[m.faces][:,:,:2]
        ax.add_collection(PolyCollection(polygons,facecolors=[colors(i%10)],edgecolors='none',alpha=.8))
        bb=m.bounds;ax.text((bb[0,0]+bb[1,0])/2,bb[0,1]-2.0,p['name'],ha='center',va='top',fontsize=6.5)
    ax.set(xlim=(0,255),ylim=(0,155),xlabel='X / mm',ylabel='Y / mm',aspect='equal',title='L2-r3 / actual single-plate placement | 255 x 155 mm | scale 1:1 in 3MF')
    ax.grid(alpha=.15);fig.savefig(VIEWS/'PRINT_PLATE.png',dpi=160);plt.close(fig)
    print('F2 3MF and actual plate projection exported',flush=True)
if __name__=='__main__':main()
