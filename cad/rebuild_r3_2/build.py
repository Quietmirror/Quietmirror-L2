"""Contour and compact the touch faces; preserve R3.1 internal interfaces."""
from pathlib import Path
import ctypes,importlib.util,json,sys,shutil
import cadquery as cq
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
BASE=ROOT/'exports/rebuild_r3_1';OUT=ROOT/'exports/rebuild_r3_2';RP=ROOT/'reports/rebuild_r3_2'
sys.path.insert(0,str(ROOT/'cad/rebuild_r2'))
from mechanics import box,check,cylinder,beam,join,build_mechanics
from surfaces import half_width,roof_height,make_surfaces
from interfaces import build_interfaces
from interface_check import possible
spec=importlib.util.spec_from_file_location('r2_exporter',ROOT/'cad/rebuild_r2/build.py')
exporter=importlib.util.module_from_spec(spec);spec.loader.exec_module(exporter)

def dump(n,d):(RP/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def yz_mask(length,height,y,z,r):
    return cq.Workplane('XY').box(30,length,height).edges('|X').fillet(r).val().translate((30,y,z))

def fill_known_closed_pocket(body):
    """Fill the small sealed cavity left at the old rear aperture corner.

    This edits the CAD solid's inner boundary, not an STL repair or deletion
    of material fragments. Reject any unrelated cavity instead of dropping it.
    """
    solid=body.Solids()[0];shells=solid.Shells()
    if len(shells)==1:return body,[]
    outer=max(shells,key=lambda sh:sh.BoundingBox().xlen*sh.BoundingBox().ylen*sh.BoundingBox().zlen)
    cavities=[]
    for sh in shells:
        if sh.isSame(outer):continue
        bb=sh.BoundingBox();void=cq.Solid.makeSolid(sh)
        assert 0<void.Volume()<.3 and 28.5<bb.xmin<bb.xmax<30.5 and 69<bb.ymin<bb.ymax<71 and 11<bb.zmin<bb.zmax<14.5,'Unexpected enclosed shell'
        cavities.append(dict(volume_mm3=void.Volume(),bounds_mm=[bb.xmin,bb.ymin,bb.zmin,bb.xmax,bb.ymax,bb.zmax],action='Fill sealed CAD cavity at obsolete rear aperture corner'))
    return check(cq.Solid.makeSolid(outer),'BODY_FILLED_LOCAL_POCKET'),cavities

def rebuild_body(p,design,apertures):
    """Apply changed apertures before the original surface is heavily trimmed.

    OCC fails Boolean classification on the already trimmed exported BSpline
    BODY. Regenerate its documented source operations instead of accepting an
    empty or partial Boolean. The unchanged R3/R3.1 corrections are reapplied.
    """
    outer,inner,_=make_surfaces(p);mech=build_mechanics(p,outer,inner)
    interface=build_interfaces(p,outer,mech['parts'])
    mech['body_cuts'].extend(interface['body_cuts']);mech['body_additions'].extend(interface['body_additions'])
    body=outer.cut(inner).clean()
    for sign in (-1,1):body=body.cut(box(25,25,50,(sign*40.8,12.5,32.5))).clean()
    for i,c in enumerate(mech['body_cuts']):
        bb=c.BoundingBox()
        if abs(bb.xlen-22)<1e-5 and abs(bb.ylen-10.7)<1e-5 and abs(bb.zlen-5.7)<1e-5:
            cy=round(c.Center().y)
            for tool in apertures[cy]['skin']:body=body.cut(tool.mirror('YZ')).clean()
        else:body=body.cut(c).clean()
        assert body.isValid(),('source cut',i)
    for name,points,tool in exporter.window_layout(p):body=body.cut(tool).clean()
    relief=[]
    for m in mech['metadata']['side_motions']:
        cx=m['actuation_point'][0]-7.1;cy=m['actuation_point'][1];cz=m['actuation_point'][2]
        relief.append(box(3.3,10.7,5.7,(cx+.5,cy,cz)))
    for i,support in enumerate(mech['body_additions']):
        for tool in relief:
            if possible(support,tool):support=support.cut(tool,tol=1e-5).clean()
        for ap in apertures.values():
            for tool in ap['supports']:
                tool=tool.mirror('YZ')
                if possible(support,tool):support=support.cut(tool,tol=1e-5).clean()
        body=body.fuse(support,tol=1e-5).clean()
        assert body.isValid(),('source support',i)
    for tool in interface['final_cuts']+mech['terminal_cuts']:body=body.cut(tool,tol=1e-5).clean()
    body=body.mirror('YZ');print('Regenerated source BODY',len(body.Solids()),body.Volume(),flush=True)
    for m in design['mechanisms']['motions']:
        if m['part'] in ('LEFT_KEY','RIGHT_KEY','WHEEL_CARRIER'):
            actor=cq.importers.importStep(str(BASE/f"assembly/{m['part']}.step")).val()
            ori=m['origin'];axis=[ori[0]+1,*ori[1:]]
            if m['part']=='WHEEL_CARRIER':
                cut=actor.rotate(ori,axis,m['end_deg']).translate((0,0,-.03)).intersect(box(2,5,8,(-4.35,41.5,14)))
            else:
                stop=box(7,11,7,(m['actuation_point'][0]/18.3*23,11.5,10.5))
                cut=actor.rotate(ori,axis,m['end_deg']).translate((0,0,-.04)).intersect(stop)
            body=body.cut(cut).clean()
    for x in (7.8,-7.8):
        post=cylinder(2.8,2.4,(x,13.,5.6));bridge=beam((x,13.,6.8),(x,17.5,6.8),1.35)
        body=join(body,post,bridge).cut(cylinder(.85,3.2,(x,13.,5.4))).clean()
    body=body.cut(box(20.4,10.4,20,(0,15,18))).clean()
    feet=design['mechanisms']['feet'];z=5.2
    local=join(*[cylinder(4.01,z+6,(*f['center'],-5)) for f in feet])
    body=body.cut(box(150,150,z+5,(0,44,(z-5)/2)).intersect(local))
    for f in feet:body=body.fuse(cylinder(4,1.6,(*f['center'],z)))
    return body

def main():
    ctypes.windll.kernel32.SetPriorityClass(ctypes.c_void_p(-1),0x4000)
    OUT.mkdir(parents=True,exist_ok=True);RP.mkdir(parents=True,exist_ok=True)
    p=json.loads((HERE/'parameters.json').read_text());s=p['side_keys']
    keys_only='--keys-only' in sys.argv
    if not keys_only:
        for folder in ('assembly','print','gauges','electronics'):shutil.copytree(BASE/folder,OUT/folder,dirs_exist_ok=True)
    source_report=RP if keys_only else ROOT/'reports/rebuild_r3_1'
    met=json.loads((source_report/'cad_metrics.json').read_text())
    d=json.loads((source_report/'design_metadata.json').read_text())
    if keys_only:
        before=dict(d['r3_2_scope']['side_keys']);after=dict(s)
        before.pop('outer_edge_radius_mm',None);after.pop('outer_edge_radius_mm',None)
        assert before==after,'Keys-only permits edge finishing, not changed apertures'
    outer=cq.importers.importStep(str(BASE/'gauges/MOTHER_OUTER_REFERENCE.step')).val()
    exporter.OUT=OUT;exporter.REPORT=RP;exporter.CACHE=ROOT.parent/'_support/work/fenrir_rebuild_r3_2/build';exporter.CACHE.mkdir(parents=True,exist_ok=True)
    rows=[];apertures={}
    for cy,ny,name in zip(s['mechanism_centers_y'],s['touch_centers_y'],('SIDE_FRONT_KEY','SIDE_REAR_KEY')):
        cz=s['z'];h=roof_height(cy,d['parameters']);w=half_width(cy,d['parameters'])
        wall=w*(1-((cz-5)/(h-5))**3.4)**(1/3.4)
        old=cq.importers.importStep(str(BASE/f'assembly/{name}.step')).val()
        back=wall-s['back_plane_inset_mm']
        mask=yz_mask(s['touch_length_y_mm'],s['touch_height_z_mm'],ny,cz,s['outline_corner_radius_mm'])
        cap=outer.translate((s['outward_x_offset_mm'],0,0)).intersect(mask).intersect(box(20,100,50,(back+10,44,25)))
        edge_radius=s.get('outer_edge_radius_mm',0)
        if edge_radius:
            exposed=[e for e in cap.Edges() if min(v.X for v in e.Vertices())>back+.1]
            cap=check(cap.Solids()[0].fillet(edge_radius,exposed),name+'_ROUNDED_CONTACT')
        # Retain the 5.2 x 3.4 slider, captured pin and actuator. Truncate the
        # old cap entirely: a hidden old cap would leave an exposed rear tab.
        hidden=old.intersect(box(8,5.2,3.4,(wall-5.8,cy,cz)))
        neck=box(.8,5.2,3.4,(wall-1.7,cy,cz)).intersect(mask)
        # One original broad forward compression land is retained. It seats
        # at the original 0.60mm stop; the slider/pin reacts the offset load.
        # No thin back strap or visually exposed second cap remains.
        stop=old.intersect(box(.5,1.0,2.8,(wall-1.36,cy-3.9,cz)))
        key=check(hidden.fuse(neck).fuse(cap).fuse(stop),name)
        exporter.export(name,key,True,met)
        backread=cq.importers.importStep(str(OUT/f'assembly/{name}.step')).val()
        assert backread.isValid() and len(backread.Solids())==1,name
        # Refill only each old external opening with the original shell skin.
        # A matched aperture follows the smaller cap; the underlying slider
        # channel and compression stops are retained, not translated.
        clearance=yz_mask(s['touch_length_y_mm']+2*s['edge_clearance_mm'],s['touch_height_z_mm']+2*s['edge_clearance_mm'],ny,cz,s['outline_corner_radius_mm']+s['edge_clearance_mm'])
        aperture=clearance.intersect(box(20,100,50,(back-s['travel_mm']-.05+10,44,25)))
        hidden_channel=box(10,5.8,4.0,(wall-6.5,cy,cz))
        apertures[round(cy)]=dict(skin=[clearance,hidden_channel],supports=[aperture])
        rows.append(dict(part=name,old_touch_center_y=cy,new_touch_center_y=ny,forward_mm=cy-ny,
            length_y_mm=s['touch_length_y_mm'],height_z_mm=s['touch_height_z_mm'],wall_reference_x=wall,
            cap_back_plane_x=back,mechanism_center_y=cy,outward_offset_x_mm=s['outward_x_offset_mm']))
        print(name,'new touch Y',ny,'valid exported solid',flush=True)
    base_p=json.loads((ROOT/'cad/rebuild_r2/parameters.json').read_text())
    body=cq.importers.importStep(str(OUT/'assembly/BODY.step')).val() if keys_only else rebuild_body(base_p,d,apertures)
    body,filled=fill_known_closed_pocket(body)
    if filled:d['r3_2_filled_pockets']=filled
    # Keep split faces: cleaning the inherited foot cylinders can invalidate
    # STEP roundtrip orientation. This is the same R3.1 export constraint.
    if len(body.Solids())!=1:
        for i,item in enumerate(body.Solids()):
            bb=item.BoundingBox();print('BODY COMPONENT',i,item.Volume(),[bb.xmin,bb.xmax,bb.ymin,bb.ymax,bb.zmin,bb.zmax],flush=True)
        cq.exporters.export(body,str(exporter.CACHE/'debug_body.step'))
    body=check(body,'BODY')
    if not keys_only or filled:exporter.export('BODY',body,True,met)
    b=cq.importers.importStep(str(OUT/'assembly/BODY.step')).val()
    assert b.isValid() and len(b.Solids())==1,'BODY STEP roundtrip'
    d['parameters']['version']='R3.2';d['r3_2_scope']=p;d['side_touch_geometry']=rows
    for motion in d['mechanisms']['motions']+d['mechanisms']['side_motions']:
        if motion['part'].startswith('SIDE_'):
            motion['stop_revision']='One retained forward compression land; original slider/pin and 0.60mm seating plane. Rear cap land removed with obsolete external cap.'
            if motion['part']=='SIDE_REAR_KEY':motion['assembly']='Offset Y -0.30mm, insert from +X to the seat, then return Y +0.30mm before fitting the capture pin. Finite route only; print tolerance must be checked.'
    dump('cad_metrics.json',met);dump('design_metadata.json',d)
    dump('change_scope.json',dict(base='R3.1',modified=['BODY','SIDE_FRONT_KEY','SIDE_REAR_KEY'],side_keys=rows,
        old_touch_gap_y_mm=5.,new_touch_gap_y_mm=s['touch_centers_y'][1]-s['touch_centers_y'][0]-s['touch_length_y_mm'],
        unchanged_switch_slider_pin_interfaces=True,side_stop_lands_per_key=1,filled_closed_cavities=d.get('r3_2_filled_pockets',[]),unchanged_foot_datum=True,geometry='Exact mother shell outer surface translated +0.45mm in X; rounded YZ footprint and 0.25mm contact-edge fillet; concealed original slider/actuator and offset load path.'))
    shutil.copyfile(ROOT/'cad/rebuild_r3_1/electronics.json',HERE/'electronics.json')
    print('R3.2 body exported and STEP reimport valid',flush=True)

if __name__=='__main__':main()
