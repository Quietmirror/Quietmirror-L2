"""Run the release-pinned Dremel slicer in a software-rendered Linux environment."""
from pathlib import Path
import os, subprocess, urllib.request, json, shutil

ROOT=Path.cwd()
WORK=ROOT/"_support/work/l2_r4_3d45"
WORK.mkdir(parents=True,exist_ok=True)
image=WORK/"Dremel3DSlicer.AppImage"
url="https://github.com/dremel-digilab/Dremel-Slicer/releases/download/v2.3.2/Dremel3DSlicer_Linux_AppImage_Ubuntu2404_V2.3.2.AppImage"
urllib.request.urlretrieve(url,image)
assert image.stat().st_size==90229240
image.chmod(0o755)
with (WORK/"extract.log").open("w") as log:
    subprocess.run([str(image),"--appimage-extract"],cwd=WORK,stdout=log,stderr=subprocess.STDOUT,check=True)
base=WORK/"squashfs-root"
profiles=next(base.rglob("profiles/Dremel"))
app=profiles.parent.parent.parent
exe=base/"AppRun"
assert exe.exists(),list(base.iterdir())
print("APP",app,"EXE",exe,flush=True)
env=os.environ.copy()
env["QM_DREMEL_EXE"]=str(exe)
env["APPDIR"]=str(base)
env["LD_LIBRARY_PATH"]=":".join(str(p) for p in
    [base/"lib",base/"usr/lib",base/"usr/lib/x86_64-linux-gnu"] if p.exists())+":"+env.get("LD_LIBRARY_PATH","")
env["LIBGL_ALWAYS_SOFTWARE"]="1"
env["MESA_GL_VERSION_OVERRIDE"]="3.3"
env["OMP_NUM_THREADS"]="2"
env["OPENBLAS_NUM_THREADS"]="1"
subprocess.run(["python3","cad/l2_r4_3d45/build_print_package.py","--app",str(app)],env=env,check=True)
subprocess.run(["python3","cad/l2_r4_3d45/validate_print.py"],env=env,check=True)
