"""R2 independent Fenrir-reference / MiniSE-priority reconstruction.

Distinct from both upstream and our archived v0.9. Millimetres, positive Y.
Rebuild with the project D-drive Python, then check.py, fem_check.py, render.py.
"""
from pathlib import Path
import argparse, ctypes, json, os, time
os.environ.setdefault('OMP_NUM_THREADS','2')
import cadquery as cq
import trimesh
from surfaces import make_surfaces, roof_height, half_width
from mechanics import build_mechanics
from interfaces import build_interfaces

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=ROOT/'exports/rebuild_r2'
REPORT=ROOT/'reports/rebuild_r2'
CACHE=ROOT.parent/'_support/work/fenrir_rebuild_r2/build'


def dump(path,data):
    path.parent.mkdir(exist_ok=True,parents=True)
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')


def window(points,z=10.5):
    w=cq.Workplane('XY').polyline(points).close().extrude(50)
    try:w=w.edges('|Z').fillet(.85)
    except Exception:pass
    return w.val().translate((0,0,z))


def window_layout(p):
    """Large scale MiniSE-like triangular AND trapezoidal bays; no uniform grid.

    Nominal perimeter rail 2.8mm at the sampled outline. Low side gripping band
    is retained. Exact residual section and strength are checked on final CAD.
    """
    s=p['host']['scale']
    defs=[
       ('ROOT_TRI_L',[(-4.2,39.8),(-22.7,39.8),(-4.2,53.8)]),
       ('SHOULDER_TRI_L',[(-25.8,42.0),(-6.8,56.2),(-26.4,60.8)]),
       ('REAR_TRAP_L',[(-3.1,59.2),(-25.7,65.5),(-18.8,74.6),(-3.1,74.6)]),
    ]
    result=[]
    for name,points in defs:
        for side in (-1,1):
            q=[(x*s if side<0 else -x*s,y*s) for x,y in points]
            tool=window(q,10.5*s)
            # Preserve side-button surrounds and finger contact bands. This is
            # a local mask, not a bottom plate or a hidden horizontal floor.
            if side<0:
                keep=cq.Workplane('XY').box(14,28,10).val().translate((-29*s,53.5*s,14.75*s))
            else:
                keep=cq.Workplane('XY').box(14,33,8).val().translate((29*s,48*s,13*s))
            tool=tool.cut(keep)
            result.append((name if side<0 else name.replace('_L','_R'),q,tool))
    return result


def canonical(shape):
    solids=shape.Solids()
    assert shape.isValid() and len(solids)==1, ('Invalid/disconnected',len(solids))
    return solids[0]


def mirror_metadata(node,key=''):
    """Mirror construction X into user-left X. Rotation X is an axial vector
    and stays +X under this reflection; translations/normals change X sign."""
    point_keys={'origin','axis_origin','center','center_mm','center_xy','upper_connection',
        'actuation_point','stop_reference_point','switch_mount_holes','plunger_tip',
        'end_vector','outward_axis','hard_stop_reference','adapter_holes_mm',
        'mount_slots','reserved_center','xy'}
    if isinstance(node,dict):return {k:mirror_metadata(v,k) for k,v in node.items()}
    if isinstance(node,list):
        if key in point_keys and len(node) in (2,3) and all(isinstance(x,(float,int)) for x in node):
            return [-node[0],*node[1:]]
        return [mirror_metadata(v,key) for v in node]
    return node


def export(name,shape,printable,record):
    shape=canonical(shape)
    placed=OUT/'assembly';placed.mkdir(exist_ok=True,parents=True)
    cq.exporters.export(shape,str(placed/f'{name}.step'))
    # Reimport removes stale Boolean triangulations. Absolute tessellation is
    # required: the CadQuery generic export's relative chord setting can leave
    # large curved faces poorly resolved. Cleanup only welds numerical seam
    # duplicates and removes zero-area/duplicate facets; it patches no holes.
    mesh_shape=cq.importers.importStep(str(placed/f'{name}.step')).val()
    raw=CACHE/f'{name}_raw.stl'
    mesh_shape.exportStl(str(raw),tolerance=.025,angularTolerance=.12,relative=False,parallel=False)
    mesh=trimesh.load_mesh(raw);raw_faces=len(mesh.faces)
    mesh.merge_vertices(digits_vertex=6)
    mesh.update_faces(mesh.nondegenerate_faces(height=1e-7))
    mesh.update_faces(mesh.unique_faces());mesh.remove_unreferenced_vertices()
    mesh.export(placed/f'{name}.stl')
    b=shape.BoundingBox()
    info={'volume_mm3':shape.Volume(),'bounds_mm':[b.xlen,b.ylen,b.zlen],
          'min':[b.xmin,b.ymin,b.zmin],'max':[b.xmax,b.ymax,b.zmax],
          'cad_valid':shape.isValid(),'solids':len(shape.Solids()),'printable':printable,
          'mesh_cleanup':{'raw_faces':raw_faces,'final_faces':len(mesh.faces),
              'weld_decimal_places':6,'holes_patched':0,'components_discarded':0,
              'absolute_chord_mm':.025,'angular_tolerance_rad':.12}}
    if printable:
        # Wheel axis vertical, with the round shaft toward the bed. Supports
        # carry the underside of the disk; the small hex prints upward.
        q=shape.rotate((0,0,0),(0,1,0),90) if name=='WHEEL' else shape
        qb=q.BoundingBox()
        shift=[-(qb.xmin+qb.xmax)/2,-(qb.ymin+qb.ymax)/2,-qb.zmin]
        flat=q.translate(shift)
        dst=OUT/'print';dst.mkdir(exist_ok=True,parents=True)
        print_mesh=mesh.copy()
        if name=='WHEEL':
            import math
            print_mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[0,1,0]))
        print_mesh.apply_translation(shift)
        print_mesh.export(dst/f'{name}.stl')
        cq.exporters.export(flat,str(dst/f'{name}.step'))
        info['print_translation']=shift
        info['print_rotation_y_deg']=90 if name=='WHEEL' else 0
    record[name]=info


def main():
    try:ctypes.windll.kernel32.SetPriorityClass(ctypes.c_void_p(-1),0x4000)
    except Exception:pass
    p=json.loads((HERE/'parameters.json').read_text(encoding='utf-8-sig'))
    OUT.mkdir(exist_ok=True,parents=True);REPORT.mkdir(exist_ok=True,parents=True);CACHE.mkdir(exist_ok=True,parents=True)
    start=time.time(); outer,inner,sm=make_surfaces(p)
    cq.exporters.export(outer,str(CACHE/'mother_outer.step'))
    skin=outer.cut(inner).clean()
    print('Mother surfaces ready',round(time.time()-start,1),flush=True)
    mech=build_mechanics(p,outer,inner)
    interfaces=build_interfaces(p,outer,mech['parts'])
    mech['body_cuts'].extend(interfaces['body_cuts'])
    mech['body_additions'].extend(interfaces['body_additions'])
    mech['hardware'].update(interfaces['hardware'])
    body=skin
    # Remove front side-aperture knife edges identified by actual thickness
    # rays. The main-key width is retained; the lower front frame stays intact.
    from mechanics import box
    for sign in (-1,1):
        body=body.cut(box(25.,25.,50.,(sign*40.8,12.5,32.5))).clean()
    for i,c in enumerate(mech['body_cuts']):
        body=body.cut(c).clean()
        assert body.isValid(),('Invalid after mechanism cut',i)
        print('Mechanism clearance',i,'solids',len(body.Solids()),round(time.time()-start,1),flush=True)
    windows=[]
    for name,points,tool in window_layout(p):
        before=body.Volume();body=body.cut(tool).clean()
        assert body.isValid(),('Invalid after window',name)
        windows.append({'name':name,'xy':points,'removed_volume_mm3':before-body.Volume(),'lower_cut_z':10.5*p['host']['scale']})
        print('Window',name,'solids',len(body.Solids()),round(time.time()-start,1),flush=True)
    if len(body.Solids())!=1:
        cq.exporters.export(body,str(CACHE/'disconnected_skin.brep'))
        print('Disconnected skin:',[(s.Volume(),s.Center().toTuple()) for s in body.Solids()],flush=True)
    from mechanics import box
    relief=[]
    for motion in mech['metadata']['side_motions']:
        cx=motion['actuation_point'][0]-7.1
        cy=motion['actuation_point'][1];cz=motion['actuation_point'][2]
        relief.append(box(3.3,10.7,5.7,(cx+.5,cy,cz)))
    # Clear each small support before joining, avoiding a global coincident
    # BSpline subtraction on thousands of faces. Nothing is discarded.
    from interface_check import possible
    for j,support in enumerate(mech['body_additions']):
        for tool in relief:
            if possible(support,tool):support=support.cut(tool,tol=1e-5).clean()
        assert support.isValid(),('Invalid trimmed support',j)
        mech['body_additions'][j]=support
        print('Trimmed support',j,len(support.Solids()),flush=True)
    for i,s in enumerate(mech['body_additions']):
        cq.exporters.export(body,str(CACHE/'before_support.brep'))
        cq.exporters.export(s,str(CACHE/'adding_support.brep'))
        body=body.fuse(s,tol=1e-5).clean()
        print('Support',i,'solids',len(body.Solids()),round(time.time()-start,1),flush=True)
    for tool in interfaces['final_cuts']+mech['terminal_cuts']:
        body=body.cut(tool,tol=1e-5).clean()
    body=canonical(body)
    parts={'BODY':body,**mech['parts']}
    parts={n:s.mirror('YZ') for n,s in parts.items()}
    mech['hardware']={n:s.mirror('YZ') for n,s in mech['hardware'].items()}
    interfaces['gauges']={n:s.mirror('YZ') for n,s in interfaces['gauges'].items()}
    mech['metadata']=mirror_metadata(mech['metadata'])
    interfaces['metadata']=mirror_metadata(interfaces['metadata'])
    windows=mirror_metadata(windows)
    record={}
    for name,s in parts.items():
        export(name,s,True,record);print('Exported',name,flush=True)
    for name,s in mech.get('hardware',{}).items():
        export(name,s,False,record)
    gauge_dir=OUT/'gauges';gauge_dir.mkdir(exist_ok=True,parents=True)
    for name,s in interfaces['gauges'].items():cq.exporters.export(s,str(gauge_dir/f'{name}.step'))
    compound=cq.Compound.makeCompound(list(parts.values()))
    cq.exporters.export(compound,str(OUT/'FENRIR_MINISE_R2_ASSEMBLY.step'))
    dump(REPORT/'cad_metrics.json',record)
    dump(REPORT/'design_metadata.json',{'parameters':p,'surface':sm,'mechanisms':mech['metadata'],
        'windows':windows,'interfaces':interfaces['metadata'],'elapsed_s':time.time()-start,
        'provenance':'Independent reconstruction from public official dimensions/multiview. No manufacturer CAD or restricted scan incorporated.',
        'key_priority':'MiniSE-like separate solid keys, central gutter and large triangulated/trapezoidal exoskeleton; independent host dimensions.'})
    print('BUILD COMPLETE',round(time.time()-start,1),flush=True)


if __name__=='__main__':main()
