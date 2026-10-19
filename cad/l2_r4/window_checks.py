"""Six source-defined window boundaries and finite point occupancy checks.

Both the complete vertical prism and the roof-shell band are recorded, so
interior structural beams cannot disappear behind an ambiguous aperture test.
Any intentional modified region must be explained in the final G4 report.
"""
import importlib.util,json
import numpy as np
from common import *
from surfaces import make_surfaces

def z_interval(shape,x,y):
    hit=shape.intersect(cq.Edge.makeLine(V(x,y,-1),V(x,y,50)))
    zs=[p.z for e in hit.Edges() for p in [e.startPoint(),e.endPoint()]]
    return (min(zs),max(zs)) if zs else None

def main():
    cfg=json.loads((ROOT/'cad/rebuild_r2/parameters.json').read_text());outer,inner,_=make_surfaces(cfg)
    b=load('BODY');old=baseline('BODY')
    spec=importlib.util.spec_from_file_location('original_windows',ROOT/'cad/rebuild_r2/build.py')
    source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)
    rng=np.random.default_rng(20261019);rows=[]
    for name,points,_ in source.window_layout(cfg):
        tool=source.window(points,10.5*cfg['host']['scale']).mirror('YZ')
        top=max([f for f in tool.Faces() if f.geomType()=='PLANE' and abs(f.normalAt().z)>.99],key=lambda f:f.Center().z)
        wire=top.outerWire();bb=tool.BoundingBox()
        local=b.intersect(box(bb.xmin-1,bb.xmax+1,bb.ymin-1,bb.ymax+1,10,40))
        boundary=[]
        for i in range(200):
            p=wire.positionAt((i+.314159)/200)
            oi=z_interval(outer,p.x,p.y)
            if not oi:raise RuntimeError('Window outside mother surface '+name)
            q=V(p.x,p.y,oi[1]);d=cq.Vertex.makeVertex(*q.toTuple()).distance(local)
            t=wire.tangentAt((i+.314159)/200);normal=V(-t.y,t.x,0).normalized()
            if not tool.isInside(V(p.x+normal.x*.2,p.y+normal.y*.2,30),1e-7):normal=-normal
            qp=q+normal*.2
            boundary.append(dict(point_mm=q.toTuple(),distance_mm=d,inward_point_mm=qp.toTuple(),inward_inside=bool(b.isInside(qp,1e-7)),baseline_inside=bool(old.isInside(qp,1e-7))))
        full=[];roof=[]
        while len(full)<1000 or len(roof)<1000:
            x,y=rng.uniform(bb.xmin,bb.xmax),rng.uniform(bb.ymin,bb.ymax)
            if not tool.isInside(V(x,y,30),1e-7):continue
            oi=z_interval(outer,x,y);ii=z_interval(inner,x,y)
            if not oi:continue
            if len(full)<1000:
                z=rng.uniform(10.5*cfg['host']['scale'],oi[1]+.2);p=V(x,y,z)
                full.append(dict(point_mm=p.toTuple(),inside=bool(b.isInside(p,1e-7)),baseline_inside=bool(old.isInside(p,1e-7))))
            if len(roof)<1000 and ii:
                z=rng.uniform(ii[1],oi[1]+.2);p=V(x,y,z)
                roof.append(dict(point_mm=p.toTuple(),inside=bool(b.isInside(p,1e-7)),baseline_inside=bool(old.isInside(p,1e-7))))
        r=dict(window=name,assembly_x_mirrored=True,boundary=boundary,full_prism=full,roof_shell_band=roof,
               boundary_raw_pass=all(p['distance_mm']<=.01 and not p['inward_inside'] for p in boundary),
               full_prism_raw_pass=not any(p['inside'] for p in full),roof_band_raw_pass=not any(p['inside'] for p in roof),
               full_prism_new_invasions=sum(p['inside'] and not p['baseline_inside'] for p in full))
        rows.append(r);save('six_window_samples.json',rows)
        print('WINDOW',name,r['boundary_raw_pass'],r['full_prism_raw_pass'],r['roof_band_raw_pass'],r['full_prism_new_invasions'],flush=True)

if __name__=='__main__':main()
