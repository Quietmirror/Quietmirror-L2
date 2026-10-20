"""Validate the actual exported project and toolpath; never imply physical printing."""
from pathlib import Path
import collections, json, math, re, zipfile
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from build_print_package import ROOT, OUT, REPORT, NAMES, save

def main():
    checks=json.loads((REPORT/"mesh_checks.json").read_text())
    project=OUT/"L2_r4_3D45_PLA_PLATE.3mf"
    gc=OUT/"L2_r4_3D45_PLA_PLATE.gcode"
    lines=gc.read_text().splitlines()
    scene=trimesh.load(project,force="scene")
    assert len(scene.graph.nodes_geometry)==9,len(scene.graph.nodes_geometry)
    diff=float(np.max(np.abs(scene.bounds-np.array(checks["plate_bounds_mm"]))))
    assert diff<.02,(diff,scene.bounds,checks["plate_bounds_mm"])
    for name in ["L2_r4_ALL_PARTS_PRINT_PLATE.stl","L2_r4_WHOLE_ASSEMBLED_PRINTABLES.stl"]:
        m=trimesh.load_mesh(OUT/name)
        assert m.is_watertight and m.is_winding_consistent,name
        assert len(m.split(only_watertight=False))==9,name
        del m
    with zipfile.ZipFile(project) as z:
        assert z.testzip() is None
        embedded=[n for n in z.namelist() if n.endswith(".gcode")]
        assert len(embedded)==1 and z.read(embedded[0])==gc.read_bytes()
    position=np.array([np.nan,np.nan,0.]); relative_e=False; absolute_xyz=True
    last_e=0.;role="Custom";obj="";segments=[];roles=[];zvalues=[];objects=collections.Counter()
    e_by_role=collections.Counter();bounds=[];moves=[];layer_z=set();commands=collections.Counter()
    temps=[];retractions=[];metadata={}
    for line in lines:
        if line.startswith(";TYPE:"):role=line.split(":",1)[1].strip()
        if line.startswith("; printing object "):
            obj=line[len("; printing object "):].split(" id:")[0].strip().removesuffix(".stl")
        if line.startswith(";Z:"):layer_z.add(float(line[3:]))
        if line.startswith("; ") and " = " in line:
            key,val=line[2:].split(" = ",1);metadata[key]=val
        code=line.split(";",1)[0].strip()
        if not code:continue
        tokens=code.split();cmd=tokens[0];commands[cmd]+=1
        vals={k:float(v) for k,v in re.findall(r"([XYZEFSP])(-?(?:\d+(?:\.\d*)?|\.\d+))",code)}
        if cmd=="M83":relative_e=True
        if cmd=="M82":relative_e=False
        if cmd=="G90":absolute_xyz=True
        if cmd=="G91":absolute_xyz=False
        if cmd=="G92" and "E" in vals:last_e=vals["E"]
        if cmd in ["M104","M109","M140","M190"]:temps.append([cmd,vals.get("S")])
        if cmd not in ["G0","G1"]:continue
        old=position.copy()
        for i,k in enumerate("XYZ"):
            if k in vals:position[i]=vals[k] if absolute_xyz else position[i]+vals[k]
        de=(vals.get("E",0) if relative_e else vals.get("E",last_e)-last_e)
        if "E" in vals:last_e=vals["E"]
        if de<0:retractions.append(-de)
        if np.isfinite(position).all():moves.append(position.copy())
        if de>0 and ("X" in vals or "Y" in vals) and np.isfinite(old).all():
            assert absolute_xyz and relative_e,(cmd,line)
            segments.append([old[:2].copy(),position[:2].copy()])
            roles.append(role);zvalues.append(position[2]);bounds.extend([old.copy(),position.copy()])
            e_by_role[role]+=de
            if not any(t in role.lower() for t in ["support","skirt","brim","custom"]):
                objects[obj]+=de
    bounds=np.array(bounds);moves=np.array(moves)
    bb=np.vstack([bounds.min(axis=0),bounds.max(axis=0)])
    assert bb[0,0]>=-127.5 and bb[1,0]<=127.5 and bb[0,1]>=-77.5 and bb[1,1]<=77.5,bb
    assert bb[0,2]>=.19 and bb[1,2]<170,bb
    assert moves[:,0].min()>=-127.5 and moves[:,0].max()<=127.5
    assert moves[:,1].min()>=-77.5 and moves[:,1].max()<=77.5
    assert max(retractions)<=1.01,max(retractions)
    assert ["M109",220.] in temps and ["M190",45.] in temps,temps
    assert ["M104",0.] in temps and ["M140",0.] in temps
    assert not (set(commands)&{"M900","M572","G2","G3","M486"}),commands
    assert commands["G162"]==2 and commands["M84"]==1
    assert len(objects)==9,(objects,NAMES)
    assert all(any(n==o or o.startswith(n+" ") for o in objects) for n in NAMES),objects
    assert all(v>0 for v in objects.values())
    assert metadata["filament_type"]=="PLA"
    assert metadata["nozzle_diameter"]=="0.4"
    assert metadata["layer_height"]=="0.2"
    assert float(metadata["total filament used [g]"])>20
    # Geometry-preserving layout validation uses 3MF roundtrip, actual toolpath
    # bounds include support/brims. This does not certify printer calibration.
    area=math.pi*(1.75/2)**2
    masses={k:round(v*area*1.24/1000,4) for k,v in e_by_role.items()}
    result={"status":"SLICED_AND_SOFTWARE_VERIFIED / PHYSICAL_PRINT_PENDING",
        "slicer_release":"Dremel 3D Slicer v2.3.2","slicer_header":lines[1],
        "machine":"Dremel 3D45","nozzle_mm":.4,"bed_mm":[255,155,170],
        "bed_origin":"center","material":"PLA","filament_mm":1.75,"density_g_cm3":1.24,
        "nozzle_C":220,"bed_C":45,"layer_mm":.2,"wall_loops":4,
        "infill":"20% gyroid","supports":"organic, buildplate only, top gap 0.2mm",
        "brim_mm":3,"scale":1,"mesh_components":9,"project_objects":9,
        "project_roundtrip_bounds_error_mm":diff,
        "extrusion_bounds_mm":bb.tolist(),"layer_count":len(layer_z),
        "model_extrusion_mm_by_object":dict(objects),
        "mass_g":float(metadata["total filament used [g]"]),
        "estimated_print_time":metadata.get("estimated printing time (normal mode)"),
        "estimated_first_layer_time":metadata.get("estimated first layer printing time (normal mode)"),
        "filament_mm":metadata.get("filament used [mm]"),
        "mass_g_by_role_approx":masses,"commands":dict(commands),
        "hardware_tests":"Not performed; original L2-r4 hardware-pending items remain open.",
        "whole_stl":"Nine printable parts in assembly pose, NOT print-in-place."}
    save(REPORT/"validation.json",result)
    # Views come from the exact G-code, not a conceptual rendering.
    seg=np.array(segments);zs=np.array(zvalues);support=np.array(["support" in r.lower() for r in roles])
    fig,axs=plt.subplots(2,2,figsize=(13,9),constrained_layout=True)
    choices=[("Entire toolpath",np.ones(len(zs),bool)),("First layer",np.isclose(zs,.2)),
             ("Supports",support),("Layer near Z=7.2 mm",np.isclose(zs,7.2))]
    for ax,(title,mask) in zip(axs.flat,choices):
        idx=np.flatnonzero(mask)
        # Full projection is thinned only for rendering; numerical checks above
        # include every movement. Detailed first/mid layers are not thinned.
        if title=="Entire toolpath":idx=idx[::max(1,len(idx)//100000)]
        colors=np.where(support[idx],"#df9234","#157b99")
        ax.add_collection(LineCollection(seg[idx],colors=colors,linewidths=.3))
        ax.set(xlim=(-127.5,127.5),ylim=(-77.5,77.5),title=title,xlabel="X (mm)",ylabel="Y (mm)")
        ax.set_aspect("equal");ax.grid(alpha=.15)
    fig.suptitle("Quietmirror L2-r4 | actual Dremel 3D45 / PLA G-code\n"
                 f'{result["mass_g"]:.2f} g | {result["estimated_print_time"]} | 220 / 45 C')
    fig.savefig(OUT/"PRINT_PATH_VERIFIED.png",dpi=170);plt.close(fig)
    save(OUT/"PRINT_VALIDATION.json",result)
    # Keep a single clearly named, printer-ready G-code, not ambiguous temporary files.
    temporary=OUT/"plate_1.gcode"
    if temporary.exists():
        assert temporary.read_bytes()==gc.read_bytes()
        temporary.unlink()
    print(json.dumps(result,indent=2),flush=True)

if __name__=="__main__":main()
