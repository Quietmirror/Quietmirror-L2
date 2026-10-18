# Reproduce R3

All modelling uses millimetres. The validated working directory is `D:\Projects\Quietmirror\github`; runtimes, caches and logs stay in its sibling `_support`. Source `enter-project.ps1` before Python. R3 uses the same portable Python/CadQuery/OpenCascade/FreeCAD/PrusaSlicer versions documented in `cad/rebuild_r2/ENVIRONMENT.md`.

Extract `R3_SOURCE_AND_BASE.zip` into a dedicated project directory. It contains `exports/rebuild_r2/assembly`, `print`, `gauges` and the R2 Python dependencies used by `mechanical.py`; it does not require an unpublished mother-surface cache. Alternatively regenerate R2 using its published source before R3. Do not run R2 build over an edited historical checkout.

Run `REPRODUCE.ps1` after setting up the documented sibling runtimes. It builds R3, checks static/motion/mesh/insertion/bottom invariants, slices, renders, saves and reopens native FreeCAD, then generates reports and packages. `audit_r2.py` separately reproduces the historical missing-interface audit; `probe.py` is a development diagnostic, not an acceptance result. No GUI focus or system settings are required.

`parameters.json` controls the revised mechanical stops. `electronics.json` controls the separate estimated layouts. `mechanical.py` gives the additional adapter outlines, hole positions and raised mounting supports; it preserves R2 source and base files. The top-level R3 generated STEP scenes retain part names. CAD scene validity and clearance do not solve manufacturing tolerances, circuit design, PCB routing or physical assembly.

The R3 FEM is deliberately not rerun by this script: R2 FEM remains historical evidence, not certification of the revised BODY. Rendering uses bundled Mesa software OpenGL; Python and slicing run at reduced priority with two-thread environment limits where supported.
