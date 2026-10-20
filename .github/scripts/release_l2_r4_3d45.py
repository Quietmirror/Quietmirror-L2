"""Publish only the separately verified 3D45 print deliverable; preserve L2-r4."""
from pathlib import Path
import hashlib, json, os, subprocess, sys, urllib.error, urllib.parse, zipfile
ROOT=Path.cwd()
sys.path.insert(0,str(ROOT/"cad/l2_r4"))
from release import request

TAG="L2-r4-3D45-PLA"
out=ROOT/"models/L2_r4_3D45_PLA"
report=json.loads((out/"PRINT_VALIDATION.json").read_text())
approved=json.loads((ROOT/"reports/l2_r4_3d45/APPROVED_PACKAGE.json").read_text())
assert report["status"]=="SLICED_AND_SOFTWARE_VERIFIED / PHYSICAL_PRINT_PENDING"
assert report["mesh_components"]==report["project_objects"]==9
assert report["scale"]==1 and report["project_roundtrip_bounds_error_mm"]<.02
assert approved["status"]=="SOFTWARE_CHECKS_PASSED"
for name,digest in approved["sha256"].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
assert os.environ["GITHUB_REF"]=="refs/heads/main"
sha=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
bundle=ROOT/"Quietmirror_L2_r4_Dremel3D45_PLA_PRINT_PACKAGE.zip"
with zipfile.ZipFile(bundle,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for folder in ["models/L2_r4_3D45_PLA","models/L2_r4/parts","cad/l2_r4_3d45","reports/l2_r4_3d45"]:
        for p in sorted((ROOT/folder).rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix!=".pyc":
                z.write(p,p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(bundle) as z:assert z.testzip() is None
try:release=request("/releases/tags/"+TAG)
except urllib.error.HTTPError as error:
    if error.code!=404:raise
    release=request("/releases","POST",dict(
        tag_name=TAG,target_commitish=sha,name="L2-r4 · Dremel 3D45 / PLA · Sliced print package",
        body=(ROOT/"reports/l2_r4_3d45/RELEASE_NOTES.md").read_text(),
        draft=False,prerelease=True,make_latest="false"))
ref=request("/git/ref/tags/"+TAG)["object"]
assert ref["type"]=="commit" and ref["sha"]==sha,"Do not change an existing release tag"
assets=[bundle]+[out/n for n in [
    "L2_r4_ALL_PARTS_PRINT_PLATE.stl","L2_r4_WHOLE_ASSEMBLED_PRINTABLES.stl",
    "L2_r4_3D45_PLA_PLATE.3mf","L2_r4_3D45_PLA_PLATE.gcode",
    "PRINT_PATH_VERIFIED.png","PRINT_VALIDATION.json"]]
existing={a["name"]:a for a in release["assets"]}
for p in assets:
    if p.name in existing:
        assert existing[p.name]["size"]==p.stat().st_size
        continue
    url=release["upload_url"].split("{")[0]+"?name="+urllib.parse.quote(p.name)
    a=request(url,"POST",p.read_bytes(),"application/octet-stream")
    assert a["size"]==p.stat().st_size
    print("RELEASE_ASSET",a["browser_download_url"],a["size"],flush=True)
print("RELEASE",release["html_url"],sha,flush=True)
