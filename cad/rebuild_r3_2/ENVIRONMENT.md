# Reproduce R3.2 / contoured compact side keys

All dimensions are millimetres. This revision retains R3.1 five-foot bonding datum Z5.2, its reference origin and its estimated electronic layout.

Use the documented sibling `_support` Python/CadQuery, FreeCADCmd and PrusaSlicer environment. The source ZIP is a revision layer. Extract the immutable [R3_SOURCE_AND_BASE.zip](https://github.com/Quietmirror/github/blob/da06237d066d8d4a6133f03f9929cff5bdd7a50e/releases/Fenrir-MiniSE-R3/R3_SOURCE_AND_BASE.zip) first, then the new source layer into a new project folder. Do not overwrite an edited historical checkout. The retained R2 geometry and source are dependencies, not newly downloaded third-party CAD.

`parameters.json` controls side-key contact dimensions, Y positions, corner radii, outward X offset and opening clearance. The new contact faces use the actual mother shell surface. Internal switch positions, capture pins, actuator faces, travel and clamp interfaces remain at their R3.1 locations. Front is decreasing Y.

The heavily trimmed exported BSpline BODY gives unreliable Boolean classifications for the new aperture operations. `build.py` therefore regenerates the documented R2 source body with the new apertures first, then reapplies the original R3 internal corrections and R3.1 local foot shortening. All other mechanical parts are copied from the exact archived R3.1 base. Outside-edit surface samples and unchanged-part bytes are independently checked; this is not an assertion of globally exact BRep identity.

Only each original forward compression stop is retained; the obsolete rear cap lands are removed. The documented 0.203 mm3 sealed cavity at the old rear aperture corner is filled in CAD after a strict location/size check; this is not STL hole patching or component deletion. The rear key is inserted with a -0.30 mm Y offset, then returned to its final Y coordinate before inserting the capture pin. Direct straight insertion is not the validated route.

`REPRODUCE.ps1` prepares R3 and R3.1 if absent, builds R3.2, checks exported files, slices the separated pieces, renders CAD views, creates/reopens a native FreeCAD assembly, then packages reports. No foreground GUI is required. Native FCStd contains editable BRep objects; parametric editing uses the supplied Python and JSON rather than a solved feature tree.

This is an unprinted mechanical revision. Mesh and finite-position tests do not prove physical strength, friction, click feel, electrical function, actual donor-board fit or optical working height. Preserve the CERN-OHL-P-2.0 license and existing attribution.
