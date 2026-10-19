"""Six source-defined window boundaries and finite point occupancy checks.

Both the complete vertical prism and the roof-shell band are recorded, so
interior structural beams cannot disappear behind an ambiguous aperture test.
Any intentional modified region must be explained in the final G4 report.
"""
import importlib.util,json
import numpy as np
from common import *
from surfaces import make_surfaces
from side_module import integrated_frame,fixed_features,KEYS,UPPER_LUG_TOP
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
from OCP.gp import gp_Pnt,gp_Dir,gp_Lin
from OCP.TopAbs import TopAbs_IN

_classifiers={};_rays={}
def inside(shape,p,tol=1e-7):
    key=id(shape)
    if key not in _classifiers:_classifiers[key]=(shape,BRepClass3d_SolidClassifier(shape.wrapped))
    classifier=_classifiers[key][1];classifier.Perform(gp_Pnt(*p.toTuple()),tol)
    return classifier.State()==TopAbs_IN or classifier.IsOnAFace()

def z_interval(shape,x,y):
    key=id(shape)
    if key not in _rays:
        query=IntCurvesFace_ShapeIntersector();query.Load(shape.wrapped,1e-8);_rays[key]=(shape,query)
    query=_rays[key][1];query.Perform(gp_Lin(gp_Pnt(x,y,-1),gp_Dir(0,0,1)),0.,51.)
    if not query.IsDone():raise RuntimeError('Exact mother-surface ray intersection failed')
    zs=[query.Pnt(i).Z() for i in range(1,query.NbPnt()+1)]
    return (min(zs),max(zs)) if zs else None

def main():
    cfg=json.loads((ROOT/'cad/rebuild_r2/parameters.json').read_text());outer,inner,_=make_surfaces(cfg)
    b=load('BODY');old=baseline('BODY')
    # Explicit structural exceptions are retained as actual source solids,
    # not a blanket exclusion of anything also found in the old BODY.
    regions={'D1_integrated_side_frame':integrated_frame(outer),
        'D4_lower_tie':cyl(1.,80,(-40,56,8.6),(1,0,0)).intersect(outer),
        'D5_main_bearing_struts':unite(cyl(1.2,4.6,(-9.9,40.8,7.4)),cyl(1.2,4.6,(9.9,40.8,7.4))),
        'D6_enlarged_upper_tie':cyl(1.5,80,(-40,67.5,23),(1,0,0)).intersect(outer),
        'retained_central_Y54_connection':cyl(1.2,12,(-6,54,23),(1,0,0)),
        'D7_side_contact_band':outer.cut(inner).intersect(box(24,38,40,73,10.9,21))}
    adds,cuts,lands=fixed_features(outer)
    regions['D7_rims_bearings_and_stops']=unite(*adds,*lands)
    regions['D7_pin_service_reliefs']=unite(*[cyl(1.05,15,(k['hinge_x'],k['hinge_y'],UPPER_LUG_TOP)) for k in KEYS])
    for f in (OUT/'validation_features').glob('*FIXED_BEARINGS.step'):regions['retained_'+f.stem]=cq.importers.importStep(str(f)).val()
    from interfaces import build_interfaces
    it=build_interfaces(cfg,outer,{'LEFT_KEY':baseline('LEFT_KEY'),'RIGHT_KEY':baseline('RIGHT_KEY')})
    regions['retained_sensor_and_USB_mounts']=unite(*[s.mirror('YZ') for s in it['body_additions']])
    def exceptions(p):return [name for name,s in regions.items() if inside(s,p,1e-6)]
    spec=importlib.util.spec_from_file_location('original_windows',ROOT/'cad/rebuild_r2/build.py')
    source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)
    rng=np.random.default_rng(20261019);rows=[]
    for name,points,original_tool in source.window_layout(cfg):
        # Use the actual R3.2 source window, including the deliberately kept
        # finger-contact bands, rather than a fictitious full-depth polygon.
        tool=original_tool.mirror('YZ')
        top=max([f for f in tool.Faces() if f.geomType()=='PLANE' and abs(f.normalAt().z)>.99],key=lambda f:f.Center().z)
        wire=top.outerWire();bb=tool.BoundingBox()
        local=b.intersect(box(bb.xmin-1,bb.xmax+1,bb.ymin-1,bb.ymax+1,10,40))
        boundary=[]
        for i in range(200):
            p=wire.positionAt((i+.314159)/200)
            oi=z_interval(outer,p.x,p.y)
            if not oi:raise RuntimeError('Window outside mother surface '+name)
            if i<3:
                # Independent Boolean-line comparison protects the optimized
                # exact ray implementation; no tessellated roof substitute.
                hit=outer.intersect(cq.Edge.makeLine(V(p.x,p.y,-1),V(p.x,p.y,50)))
                zs=[q.z for e in hit.Edges() for q in [e.startPoint(),e.endPoint()]]
                assert zs and np.allclose(oi,[min(zs),max(zs)],atol=1e-6,rtol=0),(name,i,oi,zs)
            q=V(p.x,p.y,oi[1]);d=cq.Vertex.makeVertex(*q.toTuple()).distance(local)
            t=wire.tangentAt((i+.314159)/200);normal=V(-t.y,t.x,0).normalized()
            if not inside(tool,V(p.x+normal.x*.2,p.y+normal.y*.2,30),1e-7):normal=-normal
            qp=q+normal*.2
            inside=bool(inside(b,qp,1e-7));reasons=sorted(set(exceptions(q)+exceptions(qp))) if d>.01 or inside else []
            boundary.append(dict(point_mm=q.toTuple(),distance_mm=d,inward_point_mm=qp.toTuple(),inward_inside=inside,baseline_inside=bool(inside(old,qp,1e-7)),declared_regions=reasons,classified_pass=(d<=.01 and not inside) or bool(reasons)))
        full=[];roof=[]
        while len(full)<1000 or len(roof)<1000:
            x,y=rng.uniform(bb.xmin,bb.xmax),rng.uniform(bb.ymin,bb.ymax)
            if not inside(tool,V(x,y,30),1e-7):continue
            oi=z_interval(outer,x,y);ii=z_interval(inner,x,y)
            if not oi:continue
            if len(full)<1000:
                z=rng.uniform(10.5*cfg['host']['scale'],oi[1]+.2);p=V(x,y,z)
                if not inside(tool,p,1e-7):continue
                inside=bool(inside(b,p,1e-7));reasons=exceptions(p) if inside else []
                full.append(dict(point_mm=p.toTuple(),inside=inside,baseline_inside=bool(inside(old,p,1e-7)),declared_regions=reasons,classified_pass=not inside or bool(reasons)))
            if len(roof)<1000 and ii:
                z=rng.uniform(ii[1],oi[1]+.2);p=V(x,y,z)
                if not inside(tool,p,1e-7):continue
                inside=bool(inside(b,p,1e-7));reasons=exceptions(p) if inside else []
                roof.append(dict(point_mm=p.toTuple(),inside=inside,baseline_inside=bool(inside(old,p,1e-7)),declared_regions=reasons,classified_pass=not inside or bool(reasons)))
        r=dict(window=name,assembly_x_mirrored=True,boundary=boundary,full_prism=full,roof_shell_band=roof,
               boundary_raw_pass=all(p['distance_mm']<=.01 and not p['inward_inside'] for p in boundary),
               full_prism_raw_pass=not any(p['inside'] for p in full),roof_band_raw_pass=not any(p['inside'] for p in roof),
               full_prism_new_invasions=sum(p['inside'] and not p['baseline_inside'] for p in full),
               declared_structural_exceptions={n:bounds(s) for n,s in regions.items()},
               classified_pass=all(p['classified_pass'] for p in boundary+full+roof),
               definition='Actual six source cut tools including preserved grip bands; named retained bearings/mounts and D1/D4-D7 modifications are separately reported. Raw occupied points are never relabeled empty.')
        rows.append(r);save('six_window_samples.json',rows)
        print('WINDOW',name,r['boundary_raw_pass'],r['full_prism_raw_pass'],r['roof_band_raw_pass'],r['full_prism_new_invasions'],flush=True)

if __name__=='__main__':main()
