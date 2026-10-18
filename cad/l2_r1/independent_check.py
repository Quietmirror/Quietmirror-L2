"""Independent L2 plan checks. Imports libraries, never project geometry helpers."""
from pathlib import Path
import json, math, sys, zipfile, xml.etree.ElementTree as ET
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRep import BRep_Tool
from OCP.Geom import Geom_Line
from OCP.GeomAPI import GeomAPI_IntCS
from OCP.gp import gp_Pnt, gp_Dir
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/l2_r1';OUT.mkdir(parents=True,exist_ok=True)
WORK=ROOT/'_support/work/independent';WORK.mkdir(parents=True,exist_ok=True)
def save(name,value): (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')
def vol(s):
    p=GProp_GProps();e=BRepGProp.VolumeProperties_s(s.wrapped,p,1e-8,True,False)
    return p.Mass(),e
def restore():
    records=[]
    for ver in ('3_1','3_2'):
        z=zipfile.ZipFile(ROOT/f'releases/Fenrir-MiniSE-R{ver.replace("_",".")}/FENRIR_MINISE_R{ver}.FCStd')
        tree=ET.fromstring(z.read('Document.xml'))
        base=ROOT/f'exports/rebuild_r{ver}/assembly';base.mkdir(parents=True,exist_ok=True)
        for obj in tree.findall('./ObjectData/Object'):
            p=obj.find('./Properties/Property[@name="Shape"]')
            if p is None:continue
            item=next(iter(p));file=item.attrib.get('file')
            if not file:
                print(ET.tostring(p,encoding='unicode'),flush=True);continue
            tmp=WORK/(ver+'_'+obj.attrib['name']+'.brep');tmp.write_bytes(z.read(file))
            shape=cq.importers.importBrep(str(tmp)).val()
            dst=base/(obj.attrib['name']+'.step')
            if not dst.exists():cq.exporters.export(shape,str(dst))
            records.append(dict(version=ver,part=obj.attrib['name'],shape_file=file,valid=shape.isValid(),solids=len(shape.Solids())))
        print('Restored',ver,len(list(base.glob('*.step'))),'parts',flush=True)
    save('baseline_restoration.json',records)

def load(n):return cq.importers.importStep(str(ROOT/f'exports/rebuild_r3_2/assembly/{n}.step')).val()
def intervals(s,y,z):
    line=cq.Edge.makeLine(cq.Vector(-45,y,z),cq.Vector(45,y,z))
    intersection=s.intersect(line)
    return sorted([[min(v.X for v in e.Vertices()),max(v.X for v in e.Vertices())] for e in intersection.Edges()])

def baseline():
    names=['BODY','LEFT_KEY','RIGHT_KEY','SIDE_FRONT_KEY','SIDE_FRONT_KEY_SWITCH_CLAMP','SIDE_REAR_KEY','SIDE_REAR_KEY_SWITCH_CLAMP','WHEEL','WHEEL_CARRIER']
    rows=[]
    for n in names:
        s=load(n);v,e=vol(s);rows.append(dict(part=n,volume_mm3=v,adaptive_error=e,valid=s.isValid(),solid_count=len(s.Solids())))
        print(n,v,flush=True)
    total=sum(r['volume_mm3'] for r in rows)
    save('K1_volume.json',dict(parts=rows,total_volume_mm3=total,document_mm3=18506.6761,difference_mm3=total-18506.6761,pass_tolerance_mm3=.5,passed=abs(total-18506.6761)<.5,mass_pa12_g=total*.00101))
    b=load('BODY');samples=[]
    for y in (53.,54.,55.,66.5,67.5,68.5):
        for z in (22.,23.,24.):samples.append(dict(y=y,z=z,solid_x_intervals=intervals(b,y,z)))
    save('K4_K5_cross_tie_sections.json',dict(method='Exact CAD line intersections at 18 sampled lines, no project geometry functions imported.',samples=samples))
    coords=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text())['mechanisms']['feet']
    feet=[]
    for p in coords:
        x,y=p['center'];probe=cq.Solid.makeCylinder(3.8,8,cq.Vector(x,y,-1),cq.Vector(0,0,1));cut=b.intersect(probe)
        feet.append(dict(center=[x,y],bottom_z=cut.BoundingBox().zmin,solid_count=len(cut.Solids())))
    save('foot_datum_check.json',feet)
    print('K1 total',total,'feet',feet,flush=True)

def arithmetic():
    out=[]
    for name,y0,y1,h,p,angle in [('SF',44.2,56.3,45.,50.25,6.55),('SR',58.1,70.8,70.,64.45,6.19)]:
        arm=abs(p-h);a=math.asin(.6/arm);far=max(abs(y0-h),abs(y1-h));quarter=y0+.25*(y1-y0) if name=='SF' else y1-.25*(y1-y0)
        out.append(dict(part=name,arm_mm=arm,nominal_angle_deg=math.degrees(a),document_angle_deg=angle,far_end_displacement_mm=far*math.sin(a),quarter_force_ratio=arm/abs(quarter-h),center_force_ratio=arm/abs((y0+y1)/2-h),far_force_ratio=arm/far,face_z_center_mm=17.5,pushrod_z_mm=16.6,pushrod_z_eccentricity_mm=-.9,stop_plunger_compression_mm=.6-.05))
    delta=sum([-227,-49.5,-970,-385.8,640,77,-48,45,-136,-261,-109,45,60])
    save('K8_K10_arithmetic.json',dict(side_keys=out,budget_delta_mm3=delta,budget_volume_mm3=18506.6761+delta,budget_pa12_g=(18506.6761+delta)*.00101,status='BUDGET_ONLY_NOT_MEASURED_FINAL_GEOMETRY'))
    print(out,flush=True)

def surface():
    b=load('BODY');faces=sorted([f for f in b.Faces() if f.geomType()=='BSPLINE'],key=lambda f:f.Area(),reverse=True)
    summaries=[]
    for f in faces:
        bb=f.BoundingBox();holes=[]
        for w in f.innerWires():
            wb=w.BoundingBox();holes.append([wb.xmin,wb.xmax,wb.ymin,wb.ymax,wb.zmin,wb.zmax])
        summaries.append(dict(area_mm2=f.Area(),bounds=[bb.xmin,bb.xmax,bb.ymin,bb.ymax,bb.zmin,bb.zmax],inner_wires=holes))
    # Underlying original B-spline is used only for surface coordinates, never
    # as a claim that an opening contains material. Largest |X| is the outer skin.
    data=[(41.8,[30.53,30.23,29.92,28.98]),(46.,[30.98,30.73,30.46,29.66]),(50.8,[31.67,31.44,31.21,30.51]),(56.3,[32.34,32.14,31.93,31.30]),(58.1,[32.44,32.24,32.04,31.43]),(62.,[32.55,32.34,32.13,31.50]),(66.,[32.05,31.82,31.58,30.87]),(70.8,[30.94,30.62,30.30,29.28])]
    rows=[]
    for y,values in data:
        for z,target in zip((15.5,16.6,17.5,19.5),values):
            xs=[]
            for f in faces[:8]:
                tool=GeomAPI_IntCS(Geom_Line(gp_Pnt(0,y,z),gp_Dir(1,0,0)),BRep_Tool.Surface_s(f.wrapped))
                if tool.IsDone():xs.extend(tool.Point(i).X() for i in range(1,tool.NbPoints()+1) if 0<tool.Point(i).X()<35)
            x=max(xs) if xs else None
            rows.append(dict(y=y,z=z,document_x=target,brep_x=x,difference_mm=None if x is None else x-target,passed=x is not None and abs(x-target)<=.05))
    save('K6_outer_surface_wires.json',summaries)
    save('K7_surface_coordinates.json',dict(method='Independent GeomAPI line/surface intersection of untrimmed BSpline supports read directly from R3.2 BODY STEP.',rows=rows,passed=all(r['passed'] for r in rows)))
    print('Surface faces',len(faces),'max error',max(abs(r['difference_mm']) for r in rows if r['difference_mm'] is not None),flush=True)

def layout():
    def box(x0,x1,y0,y1,z0,z1):return cq.Solid.makeBox(x1-x0,y1-y0,z1-z0,cq.Vector(x0,y0,z0))
    floor=box(17.5,25.5,41.,71.2,12.1,13.7)
    # Window Y centers are not specified: retain the floor for a conservative
    # connectivity test. Removing windows cannot connect a detached support.
    legs=[cq.Solid.makeCylinder(2,1.35,cq.Vector(x,y,10.75)).intersect(box(10,limit,35,75,10,14)) for x,y,limit in ((27.331,43.,29.),(28.604,66.8,30.1))]
    front=box(18.7,25.2,41.85,54.65,13.7,19.5);rear=box(19.2,25.7,56.05,68.85,13.7,19.5)
    columns=[box(25.5,29.74,53.8,55.6,13.7,16.4),box(26.,30.04,58.,60.,13.7,16.4)]
    back=box(17.5,18.7,41.,71.2,12.1,19.5);divider=box(17.5,25.5,54.95,55.75,13.7,19.5)
    carrier=floor.fuse(back,divider,*legs,*columns).clean()
    pcb=box(15.2,16.2,44.,70.,13.,18.5)
    body=load('BODY');main_hinge=body.intersect(box(25.2,30.,36.,41.85,13.7,22))
    sensor_tab=body.intersect(box(9.4,15.6,50.6,59.4,10.3,12.9))
    meta=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text())['mechanisms']
    foot=next(f for f in meta['feet'] if abs(f['center'][0]-24.84)<.01 and abs(f['center'][1]-62.64)<.01)
    p=cq.Vector(24.84,62.64,7.4);q=cq.Vector(*foot['upper_connection']);vec=q-p
    strut=cq.Solid.makeCylinder(1.7,vec.Length,p,vec.normalized()).fuse(cq.Solid.makeSphere(1.7,p),cq.Solid.makeSphere(1.7,q)).intersect(body).clean()
    checks=[dict(pair=['SF_stop','SF_switch'],distance_mm=columns[0].distance(front),criterion_mm=.5),dict(pair=['SR_stop','SR_switch'],distance_mm=columns[1].distance(rear),criterion_mm=.5),dict(pair=['SF_switch','main_outer_hinge_ear'],distance_mm=front.distance(main_hinge),criterion_mm=.5),dict(pair=['rear_leg','rear_foot_strut'],distance_mm=legs[1].distance(strut),criterion_mm=.5),dict(pair=['SIDE_IO_PCB','sensor_tab'],distance_mm=pcb.distance(sensor_tab),criterion_mm=.5),dict(pair=['rear_leg','carrier_floor'],distance_mm=legs[1].distance(floor),criterion='continuous joint required'),dict(pair=['front_leg','carrier_floor'],distance_mm=legs[0].distance(floor),criterion='continuous joint with sufficient bearing area required'),dict(pair=['SIDE_IO_PCB','back_wall'],distance_mm=pcb.distance(back),criterion='support not defined in document')]
    cq.exporters.export(cq.Compound.makeCompound([carrier,front,rear,pcb]),str(WORK/'document_side_layout_UNCORRECTED.step'))
    save('K9_document_layout.json',dict(status='DIAGNOSTIC_NOT_PRINTABLE',carrier_solid_count=len(carrier.Solids()),carrier_uncut_volume_mm3=vol(carrier)[0],checks=checks,limitations=['No undisclosed joining ribs were invented. Switch terminal openings, two floor windows and fillets omitted because their positions or paths are underdefined; none can connect a detached post.','Old BODY side socket must be removed before full new-assembly collision checks.']))
    print('Carrier solids',len(carrier.Solids()),checks,flush=True)

def source_openings():
    b=load('BODY')
    faces=sorted([f for f in b.Faces() if f.geomType()=='BSPLINE'],key=lambda f:f.Area(),reverse=True)
    def close_support(face,base_z):
        roof=cq.Face(BRepBuilderAPI_MakeFace(BRep_Tool.Surface_s(face.wrapped),1e-7).Face())
        bottom_edges=[];side_faces=[]
        for e in roof.Edges():
            a,c=e.startPoint(),e.endPoint();aa=cq.Vector(a.x,a.y,base_z);cc=cq.Vector(c.x,c.y,base_z)
            if abs(a.y-c.y)>80:
                be=e.translate((0,0,base_z-a.z));bottom_edges.append(be)
                if abs(base_z-a.z)>1e-6:side_faces.append(cq.Face.makeRuledSurface(e,be))
            else:
                be=cq.Edge.makeLine(cc,aa);bottom_edges.append(be)
                ed=[e,be] if abs(base_z-a.z)<1e-6 else [e,cq.Edge.makeLine(c,cc),be,cq.Edge.makeLine(aa,a)]
                side_faces.append(cq.Face.makeFromWires(cq.Wire.assembleEdges(ed)))
        base=cq.Face.makeFromWires(cq.Wire.assembleEdges(bottom_edges))
        solid=cq.Solid.makeSolid(cq.Shell.makeShell([roof,base]+side_faces))
        assert solid.isValid() and len(solid.Solids())==1
        return solid
    outer=close_support(faces[0],5.)
    inner=close_support(faces[1],-8.)
    cq.exporters.export(outer,str(WORK/'MOTHER_OUTER_FROM_R32_SURFACE.step'))
    cq.exporters.export(inner,str(WORK/'MOTHER_INNER_FROM_R32_SURFACE.step'))
    skin=outer.cut(inner).clean();assert skin.isValid()
    # Rebuild only the six documented window polygons as verification tools.
    # These numeric baseline parameters are data, not imported builder code.
    polygons=[[(4.2,39.8),(22.7,39.8),(4.2,53.8)],[(25.8,42),(6.8,56.2),(26.4,60.8)],[(3.1,59.2),(25.7,65.5),(18.8,74.6),(3.1,74.6)]]
    windows=[]
    for points in polygons:
        for sign in (-1,1):
            points_mm=[(sign*x*1.08,y*1.08) for x,y in points]
            tool=cq.Workplane('XY').polyline(points_mm).close().extrude(50).edges('|Z').fillet(.85).val().translate((0,0,11.34))
            keep=cq.Workplane('XY').box(14,28 if sign>0 else 33,10 if sign>0 else 8).val().translate((sign*29*1.08,(53.5 if sign>0 else 48)*1.08,(14.75 if sign>0 else 13)*1.08))
            windows.append(tool.cut(keep))
    metadata=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text())['mechanisms']
    fast=metadata['fasteners'];rows=[]
    for name,prefix in [('O1','SIDE_FRONT_KEY_M2_SWITCH_1'),('O2','SIDE_REAR_KEY_M2_SWITCH_1'),('O4','SIDE_REAR_KEY_M2_SWITCH_2')]:
        item=next(f for f in fast if f['prefix']==prefix);c=item['center_mm'];tool=cq.Solid.makeCylinder(2.15,38,cq.Vector(c[0],c[1],c[2]+4.85))
        removed=skin.intersect(tool).clean();raw_volume=vol(removed)[0]
        for win in windows:removed=removed.cut(win).clean()
        bb=removed.BoundingBox()
        remaining=b.intersect(tool).clean()
        rows.append(dict(opening=name,source='cad/rebuild_r2/fasteners.py:m2_set driver access cylinder r=2.15,length=38; mechanics.py side switch M2 call',fastener=prefix,tool_center=c,raw_skin_intersection_mm3=raw_volume,additional_cut_outside_six_windows_mm3=vol(removed)[0],body_material_in_tool_mm3=vol(remaining)[0] if len(remaining.Solids()) else 0,bounds_mm=[bb.xmin,bb.xmax,bb.ymin,bb.ymax,bb.zmin,bb.zmax],action='REMOVE_OBSOLETE_SIDE_SWITCH_DRIVER_CUT_IN_SOURCE; preserve original six window boundary'))
        print(name,rows[-1],flush=True)
    for name,n in [('PH1','SIDE_FRONT_KEY_CAPTURE_PIN'),('PH2','SIDE_REAR_KEY_CAPTURE_PIN')]:
        pin=load(n);bb=pin.BoundingBox();x=(bb.xmin+bb.xmax)/2;y=(bb.ymin+bb.ymax)/2
        rows.append(dict(opening=name,center_xy=[x,y],hole_diameter_mm=1.72,source='cad/rebuild_r2/mechanics.py: capture channel and cylinder(.86,30,...); final additions cut around pin paths',action='REMOVE_OBSOLETE_CAPTURE_PIN_CUT_IN_SOURCE'))
    rows.append(dict(opening='O3',axis_yz=[50.,19.],diameter_mm=2.35,source='cad/rebuild_r2/mechanics.py: pin_paths.append(cylinder(1.175,82.,(-41.,50.,19.),(1,0,0)))',observed_outer_wire_bounds_mm=[-31.02650002,-29.99780635,48.82499990,51.17500010,17.82499989,20.17500010],action='KEEP_FUNCTIONAL_WHEEL_CARRIER_PIN_ACCESS; do not fill as an unknown cosmetic hole'))
    save('K6_source_openings.json',dict(method='Sources read from exact baseline; numerical cuts independently rebuilt without importing project functions. Full raw mother-skin tool intersection is not equal to additional material beyond original six windows.',openings=rows))

def skin_connectivity():
    b=load('BODY');inner=cq.importers.importStep(str(WORK/'MOTHER_INNER_FROM_R32_SURFACE.step')).val()
    region=b.intersect(inner).clean();rows=[]
    assert region.isValid()
    for s in region.Solids():
        bb=s.BoundingBox();v,e=vol(s)
        rows.append(dict(volume_mm3=v,bounds=[bb.xmin,bb.xmax,bb.ymin,bb.ymax,bb.zmin,bb.zmax],valid=s.isValid()))
    save('K5_cavity_material_components.json',dict(method='Exact intersection of R3.2 BODY with untrimmed original cavity reconstructed from its underlying BSpline. Shell material removed to inspect support connectivity. Components are geometric groups, not separate manufactured parts.',components=sorted(rows,key=lambda r:r['volume_mm3'],reverse=True),count=len(rows)))
    cq.exporters.export(region,str(WORK/'K5_INTERNAL_COMPONENTS_WITHOUT_SKIN.step'))
    print('K5 groups',len(rows),rows,flush=True)

if __name__=='__main__':
    task=sys.argv[1] if len(sys.argv)>1 else 'baseline'
    {'restore':restore,'baseline':baseline,'arithmetic':arithmetic,'surface':surface,'layout':layout,'openings':source_openings,'connectivity':skin_connectivity}[task]()
