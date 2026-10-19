"""Regenerate printable geometry from parameterized source, never patch STEP.

Run only in a disposable clone/output checkout: this intentionally rebuilds
generated L2_r4 artifacts, which must then receive fresh numerical checks.
Historical L2_r3, author evidence, tags and releases are never modified.
"""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SCRIPTS=['bootstrap_build','restore_inputs','build_body','main_key_relief','side_module','assemble','surface_mesh']
if __name__=='__main__':
    for name in SCRIPTS:
        print('REBUILD',name,flush=True)
        subprocess.run([sys.executable,'-u',str(ROOT/'cad/l2_r4'/(name+'.py'))],cwd=ROOT,check=True)
    print('Geometry rebuilt. CAD_COMPLETE is not inherited: run every affected validation on these new artifacts.',flush=True)
