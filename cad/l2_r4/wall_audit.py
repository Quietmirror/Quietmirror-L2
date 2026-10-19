"""Actual critical BRep sections plus deterministic surface-normal wall samples.

Sharp free edges have no positive mathematical global wall minimum. Report
finite measured sections and first exit chords, including thin features,
without relabeling an area sample as a global medial-axis proof.
"""
import json,math
import numpy as np
import trimesh
from common import *
from side_module import KEYS,RETAINER_MOUNTS,EAR_TOP

def line(shape,p,q):
    hit=shape.intersect(cq.Edge.makeLine(V(*p),V(*q)))
    return [dict(length_mm=e.Length(),a_mm=e.startPoint().toTuple(),b_mm=e.endPoint().toTuple()) for e in hit.Edges() if e.Length()>1e-5]

def main():
    body=load('BODY');samples=[]
    def section(label,part,p,q):
        s=body if part=='BODY' else load(part);segments=line(s,p,q)
        samples.append(dict(feature=label,part=part,from_mm=p,to_mm=q,segments=segments))
    for k in KEYS:
        x,y=k['hinge_x'],k['hinge_y'];n=k['name']
        section('moving hinge journal radial walls',n,(x-1.4,y,17.3),(x+1.4,y,17.3))
        section('moving outward ear Y width',n,(x-1.6,y-1,19.1),(x-1.6,y+1,19.1))
        for z in [14.7,20.2]:
            for angle in [0,45,90,135]:
                a=math.radians(angle);d=np.array([math.cos(a),math.sin(a),0.])*2.8
                section('fixed pin bearing radial section','BODY',tuple(np.array([x,y,z])-d),tuple(np.array([x,y,z])+d))
        for yy in np.linspace(k['y0']+2,k['y1']-2,5):
            section('cap contact skin X chord',n,(29,float(yy),17.4),(37,float(yy),17.4))
    for y in np.linspace(56.95,57.45,3):
        for z in np.linspace(15.4,19.6,8):section('C6 central divider retained outer lip','BODY',(28.5,float(y),float(z)),(36,float(y),float(z)))
    for x,y in [(18,47),(24.5,49),(18,63),(24.5,63)]:section('integrated floor Z thickness','BODY',(x,y,11.9),(x,y,13.8))
    for n,sign in [('LEFT_KEY',1),('RIGHT_KEY',-1)]:
        for y in [16,20,28,34]:section('main contact Z section',n,(18.3*sign,y,9),(18.3*sign,y,35))
    nominal=[dict(feature='side moving journal wall',mm=(2.5-1.05)/2),dict(feature='outward ear Y width',mm=.8),dict(feature='outward ear Z height',mm=EAR_TOP-18.6),dict(feature='upper fixed bearing Z height',mm=.8),dict(feature='lower fixed bearing Z height',mm=1.),dict(feature='integral floor',mm=1.6),dict(feature='SF retainer wall',mm=1.2),dict(feature='SR retainer wall',mm=1.7),dict(feature='retainer pilot radial boss wall',mm=1.8-.85),dict(feature='side cap X skin',mm=1.2),dict(feature='C6 retained lip X-offset',mm=.8)]
    save('critical_wall_sections.json',dict(nominal_source_dimensions=nominal,sections=samples,all_probes_cross_material=all(r['segments'] for r in samples),method='Exact BRep intersection with listed line segments; chord direction and endpoints retained. Nominal dimensions are separately identified.'))
    rows=[];rng=np.random.default_rng(20261019)
    for name in json.loads((RP/'assembly_inventory.json').read_text())['printable']:
        mesh=trimesh.load_mesh(OUT/'parts'/(name+'.stl'));area=mesh.area_faces
        count=6000 if name=='BODY' else 1200
        ids=rng.choice(len(mesh.faces),size=min(count,len(mesh.faces)),replace=False,p=area/area.sum())
        origins=mesh.triangles_center[ids]-mesh.face_normals[ids]*.005;direction=-mesh.face_normals[ids]
        values=[];miss=[]
        for start in range(0,len(ids),48):
            a=origins[start:start+48];d=direction[start:start+48]
            points,rays,_=mesh.ray.intersects_location(a,d,multiple_hits=False)
            hits={int(r):(p,float(np.linalg.norm(p-a[r]))+.005) for p,r in zip(points,rays)}
            for j in range(len(a)):
                if j in hits:
                    p,length=hits[j];values.append(dict(surface_point_mm=(a[j]-d[j]*.005).tolist(),exit_point_mm=p.tolist(),normal_chord_mm=length,face=int(ids[start+j])))
                else:miss.append(int(ids[start+j]))
        lengths=[v['normal_chord_mm'] for v in values]
        row=dict(part=name,sample_count=len(ids),hit_count=len(values),missed_faces=miss,minimum_sampled_chord_mm=min(lengths),percentiles_mm={str(q):float(np.percentile(lengths,q)) for q in [1,5,50]},thin_under_0p4_count=sum(v<.4 for v in lengths),thinnest_samples=sorted(values,key=lambda v:v['normal_chord_mm'])[:40])
        rows.append(row);save('surface_normal_wall_samples.json',dict(parts=rows,scope='Deterministic area-weighted face-centre first-exit rays on final closed meshes; finite sampling, not a global thickness bound. Sharp edges, rounds and junctions are explicitly retained in the low tail.'))
        print('WALL_SAMPLES',name,len(values),min(lengths),flush=True)

if __name__=='__main__':main()
