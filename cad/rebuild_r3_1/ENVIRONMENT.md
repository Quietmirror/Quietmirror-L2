# Reproduce R3.1 / shortened feet

All dimensions are millimetres. Keep the original R3 assembly coordinate system: the new five skate bonding faces are at Z=5.2 mm. This equals the exported `SENSOR_RESERVED_VOLUME` lower plane, not a measured optical surface.

Use the same D-drive Python/CadQuery, FreeCADCmd and PrusaSlicer environment as R3. The source ZIP is a revision layer; its immutable base is [R3_SOURCE_AND_BASE.zip](https://github.com/Quietmirror/github/blob/da06237d066d8d4a6133f03f9929cff5bdd7a50e/releases/Fenrir-MiniSE-R3/R3_SOURCE_AND_BASE.zip). Extract that base first and then this R3.1 source ZIP into the same **new project folder**. The base includes exact R2 geometry and all required dependencies; do not overwrite an edited historical checkout.

`REPRODUCE.ps1` generates the R3 base if it is absent, then makes R3.1, checks exported CAD/mesh/datum/ground clearance and finite static/motion/insertion poses, slices the separated components, renders CAD views and writes/reopens native FreeCAD. All caches and tools remain in sibling `_support`. No foreground application is needed.

`parameters.json` controls the target plane, nominal pad diameter, landing thickness and the example skate thickness. `build.py` only modifies BODY in five local cylindrical regions. All other 71 mechanical STEP/STL references remain byte-identical to R3. The electronic positions are retained; only the optical-height equation gains the new foot datum. Actual skate thickness and optical working height must be measured separately.

Only the parameterized short-foot geometry, nominal interfaces and finite tests are released. This revision does not manufacture a PCB, recalibrate sensor optics, certify strength or verify actual printed click feel. The source layer contains the helper scripts it uses; see the retained CERN-OHL-P-2.0 license and attribution.
