"""Preserve only this additive print package, with a guarded fast-forward push."""
import sys, os
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/"cad/l2_r4"))
from ci_checkpoint import git

paths=["models/L2_r4_3D45_PLA","reports/l2_r4_3d45","cad/l2_r4_3d45/profiles"]
paths=[p for p in paths if Path(p).exists()]
git("config","user.name","github-actions[bot]")
git("config","user.email","41898282+github-actions[bot]@users.noreply.github.com")
git("add","--",*paths)
if git("diff","--cached","--name-only"):
    parent=git("rev-parse","HEAD")
    git("commit","-m","Record actual Dremel 3D45 PLA print package and validation")
    target="codex/r4-3d45-pla"
    live=git("ls-remote","origin","refs/heads/"+target).split()[0]
    if live != parent:
        target += "-result-"+os.environ["GITHUB_RUN_ID"]
    git("push","origin","HEAD:refs/heads/"+target,auth=True)
    print("CHECKPOINT",target,git("rev-parse","HEAD"))
