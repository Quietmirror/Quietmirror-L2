"""Additive 3D45/PLA print package from the frozen, accepted L2-r4 meshes."""
from pathlib import Path
import argparse, json, math, os, shutil, subprocess, zipfile
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "models/L2_r4_3D45_PLA"
REPORT = ROOT / "reports/l2_r4_3d45"
WORK = ROOT / "_support/work/l2_r4_3d45"
NAMES = ["BODY", "LEFT_KEY", "RIGHT_KEY", "SF_RETAINER", "SIDE_FRONT_KEY",
         "SIDE_REAR_KEY", "SR_RETAINER", "WHEEL", "WHEEL_CARRIER"]
ANCHORS = {"BODY": (12,12), "LEFT_KEY": (110,12), "RIGHT_KEY": (155,12),
           "WHEEL_CARRIER": (205,12), "SF_RETAINER": (110,80), "SR_RETAINER": (130,80),
           "SIDE_FRONT_KEY": (155,80), "SIDE_REAR_KEY": (175,80), "WHEEL": (205,80)}

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf8")

def profile(app, category, name, chain=None):
    path = app / "resources/profiles/Dremel" / category / (name + ".json")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    chain = chain if chain is not None else []
    parent = profile(app, category, data["inherits"], chain) if data.get("inherits") else {}
    chain.append(path)
    parent.update(data)
    return parent

def profiles(app):
    folder = Path(__file__).parent / "profiles"
    folder.mkdir(exist_ok=True)
    sources = []
    machine = profile(app, "machine", "Dremel 3D45 0.4 nozzle", sources)
    process = profile(app, "process", "0.20mm Standard @Dremel 3D45 0.4", sources)
    filament = profile(app, "filament", "Dremel PLA @3D45", sources)
    original = {"machine": machine.copy(), "process": process.copy(), "filament": filament.copy()}
    for p in sources:
        target = folder / "upstream" / p.parent.name / p.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)
    license_path = app / "LICENSE.txt"
    if license_path.exists():
        shutil.copy2(license_path, folder / "UPSTREAM_LICENSE.txt")
    machine.update({
        "name": "Quietmirror Dremel 3D45 0.4", "printer_settings_id": "Quietmirror Dremel 3D45 0.4",
        "printable_area": ["-127.5x-77.5", "127.5x-77.5", "127.5x77.5", "-127.5x77.5"],
        "printable_height": "170",
        "use_relative_e_distances": "1",
        "before_layer_change_gcode": ";BEFORE_LAYER_CHANGE\n;[layer_z]\nG92 E0",
        "layer_change_gcode": ";AFTER_LAYER_CHANGE\n;[layer_z]",
        "emit_machine_limits_to_gcode": "0",
        "retraction_length": ["1"], "retraction_speed": ["30"], "deretraction_speed": ["30"],
        "machine_start_gcode":
            "G90\nM83\nM140 S[bed_temperature_initial_layer_single]\n"
            "M104 S[nozzle_temperature_initial_layer]\nG28\n"
            "M132 X Y Z A\nM907 X100 Y100 Z50 A100\n"
            "M190 S[bed_temperature_initial_layer_single]\n"
            "M109 S[nozzle_temperature_initial_layer]\n"
            "G1 Z10 F400\nG92 E0\nG1 E3 F200\nG92 E0",
        "machine_end_gcode": "M83\nG1 E-1 F300\nM104 S0\nM140 S0\nM107\n"
                             "G162 Z F600\nG162 X Y F2000\nM84",
        "default_filament_profile": ["Quietmirror PLA 3D45"],
        "default_print_profile": "Quietmirror 0.20mm PLA 3D45",
    })
    process.update({
        "name": "Quietmirror 0.20mm PLA 3D45",
        "print_settings_id": "Quietmirror 0.20mm PLA 3D45",
        "layer_height": "0.2", "initial_layer_print_height": "0.2",
        "wall_loops": "4", "wall_generator": "arachne", "only_one_wall_top": "0",
        "bottom_shell_layers": "5", "top_shell_layers": "5",
        "sparse_infill_density": "20%", "sparse_infill_pattern": "gyroid",
        "infill_combination": "0", "enable_arc_fitting": "0",
        "outer_wall_speed": "25", "inner_wall_speed": "35",
        "sparse_infill_speed": "45", "internal_solid_infill_speed": "35",
        "top_surface_speed": "25", "bridge_speed": "25", "gap_infill_speed": "20",
        "initial_layer_speed": "20", "initial_layer_infill_speed": "20",
        "travel_speed": "120", "default_acceleration": "500",
        "outer_wall_acceleration": "500", "inner_wall_acceleration": "500",
        "initial_layer_acceleration": "500", "top_surface_acceleration": "500",
        "travel_acceleration": "500",
        "enable_support": "1", "support_type": "tree(auto)", "support_style": "organic",
        "support_on_build_plate_only": "1", "support_threshold_angle": "45",
        "support_top_z_distance": "0.2", "support_bottom_z_distance": "0.2",
        "support_object_xy_distance": "0.35", "support_interface_top_layers": "3",
        "support_interface_spacing": "0.2", "support_interface_speed": "25",
        "support_speed": "35", "support_expansion": "0",
        "brim_type": "outer_only", "brim_width": "3", "brim_object_gap": "0.1",
        "skirt_loops": "0", "skirt_height": "1",
        "print_sequence": "by layer", "filename_format": "L2_r4_3D45_PLA_PLATE.gcode",
    })
    filament.update({
        "name": "Quietmirror PLA 3D45", "filament_settings_id": ["Quietmirror PLA 3D45"],
        "filament_type": ["PLA"], "filament_diameter": ["1.75"], "filament_density": ["1.24"],
        "filament_flow_ratio": ["1"], "filament_max_volumetric_speed": ["8"],
        "enable_pressure_advance": ["0"], "activate_air_filtration": ["0"],
        "additional_cooling_fan_speed": ["0"], "during_print_exhaust_fan_speed": ["0"],
        "complete_print_exhaust_fan_speed": ["0"],
        "nozzle_temperature": ["220"], "nozzle_temperature_initial_layer": ["220"],
        "fan_min_speed": ["100"], "fan_max_speed": ["100"], "close_fan_the_first_x_layers": ["1"],
        "slow_down_layer_time": ["10"], "slow_down_min_speed": ["10"],
    })
    # 45 C is the Dremel PLA bed preset. Avoid substituting a generic 60 C bed.
    for key in ["cool_plate_temp", "textured_cool_plate_temp", "hot_plate_temp",
                "smooth_pei_plate_temp", "textured_plate_temp"]:
        filament[key] = ["45"]; filament[key + "_initial_layer"] = ["45"]
    for kind, data in [("machine", machine), ("process", process), ("filament", filament)]:
        data["inherits"] = {"machine": "Dremel 3D45 0.4 nozzle",
                            "process": "0.20mm Standard @Dremel 3D45 0.4",
                            "filament": "Dremel PLA @3D45"}[kind]
        data["from"] = "User"
        data["instantiation"] = "true"
        data["compatible_printers"] = ["Dremel 3D45 0.4 nozzle"] if kind != "machine" else []
        data["compatible_printers_condition"] = ""
        save(folder / (kind + ".json"), data)
    save(REPORT / "profile_changes.json", {
        k: {a: {"upstream": original[k].get(a), "project": v}
            for a,v in d.items() if original[k].get(a) != v}
        for k,d in [("machine",machine), ("process",process), ("filament",filament)]})
    return folder

def meshes():
    plate = trimesh.Scene(); assembly = []; rows = []
    for name in NAMES:
        mesh = trimesh.load_mesh(ROOT / "models/L2_r4/parts" / (name + ".stl"))
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0, name
        assert len(mesh.split(only_watertight=False)) == 1, name
        assembly.append(mesh.copy())
        if name in ("SF_RETAINER", "SR_RETAINER"):
            mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[1,0,0]))
        if name == "WHEEL":
            mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[0,1,0]))
        x,y = ANCHORS[name]
        # Dremel's real coordinate origin is at the middle of its 255 x 155 bed.
        mesh.apply_translation([x-127.5-mesh.bounds[0,0], y-77.5-mesh.bounds[0,1], -mesh.bounds[0,2]])
        plate.add_geometry(mesh, node_name=name, geom_name=name)
        rows.append({"name":name,"bounds_mm":mesh.bounds.tolist(),"size_mm":mesh.extents.tolist(),
                     "volume_mm3":float(mesh.volume),"watertight":True,"components":1})
    plate.units = "mm"
    combined = trimesh.util.concatenate(list(plate.geometry.values()))
    combined.export(OUT / "L2_r4_ALL_PARTS_PRINT_PLATE.stl")
    assembled = trimesh.util.concatenate(assembly)
    assembled.export(OUT / "L2_r4_WHOLE_ASSEMBLED_PRINTABLES.stl")
    (WORK / "plate_input.3mf").write_bytes(trimesh.exchange.threemf.export_3MF(plate))
    save(REPORT / "mesh_checks.json", {"scale":1,"units":"mm","parts":rows,
         "plate_bounds_mm":plate.bounds.tolist(), "assembled_bounds_mm":assembled.bounds.tolist(),
         "assembled_size_mm":assembled.extents.tolist(), "printed_components":9,
         "whole_stl_use":"Assembly preview of nine separate printable parts; not print-in-place.",
         "cad_source":"L2-r4 frozen accepted meshes; original geometry unchanged."})

def run_slicer(app, folder, source, label, slice_it=True):
    exe = Path(os.environ.get("QM_DREMEL_EXE", str(app / "Dremel-3D-Slicer.exe")))
    target = OUT / (label + ".3mf")
    args = [str(exe), "--datadir", str(WORK / "appdata"), "--debug", "3",
            "--load-settings", str(folder/"machine.json")+";"+str(folder/"process.json"),
            "--load-filaments", str(folder/"filament.json"), "--arrange", "0", "--orient", "0",
            "--outputdir", str(OUT), "--export-3mf", str(target)]
    if slice_it: args += ["--slice", "0"]
    args += [str(source)]
    save(REPORT / "slicer_command.json",args)
    with (REPORT / "slicer.log").open("w",encoding="utf8") as stream:
        p=subprocess.run(args, stdout=stream, stderr=subprocess.STDOUT, timeout=2400,
                         creationflags=0x08000000 if os.name=="nt" else 0)
    assert p.returncode == 0, f"Slicer failed {p.returncode}; see slicer.log"
    assert target.exists()
    with zipfile.ZipFile(target) as z:
        gcodes = [n for n in z.namelist() if n.endswith(".gcode")]
        for name in gcodes:
            (OUT / (label + ".gcode")).write_bytes(z.read(name))
        save(REPORT / "sliced_project_contents.json",z.namelist())
    return target

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--app",type=Path,required=True)
    parser.add_argument("--probe",action="store_true")
    args=parser.parse_args()
    for p in [OUT, REPORT, WORK]: p.mkdir(parents=True,exist_ok=True)
    folder=profiles(args.app)
    if args.probe:
        run_slicer(args.app,folder,ROOT/"models/L2_r4/parts/WHEEL.stl","PROBE_WHEEL")
    else:
        meshes()
        run_slicer(args.app,folder,WORK/"plate_input.3mf","L2_r4_3D45_PLA_PLATE")

if __name__ == "__main__":
    main()
