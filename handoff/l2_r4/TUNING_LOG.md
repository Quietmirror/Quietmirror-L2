# L2-r4 source revisions and rechecks

Status: CAD checks running. No L2-r4 Release is permitted until all CAD gates complete.

## Candidate 1

- Adopted the supplied execute-all plan and author evidence at f637118455159515a200e6e0f35c0eea1c7d1633 (descendant of the document reference 54dac615).
- D1-D6 are integrated into the BODY source generation sequence; the finished r3 BODY is not imported for boolean patching.
- D7 removes the remote tabs, moves hinges, scales the pads, and recalculates the 0.60 mm stop travel.
- The specified ear starts at Z19.85 but the hinge ends at Z19.5. Added a concealed root bridge joining the ear to the existing web; geometric and movement checks must pass before acceptance.
- A local outward stop land uses the entry slot allowance so the specified 1.0 mm slot does not inadvertently allow more than 0.5 degree outward play.
- Heavy processing runs on an isolated public GitHub runner. Each FEM solve must observe at least 10 GB available RAM and use default SPOOLES; no reduced mesh or omitted cases is allowed.

## Candidate 1 tool corrections

- CalculiX 2.21 version probe returns 201 despite printing its version; only this known probe response is accepted. Actual solver failures still fail the build.
- BODY and four new side parts passed STEP single-solid/valid round-trip; the first run stopped while measuring STL connected components because trimesh split implicitly invoked hole repair and required networkx. Changed component counting to scipy face-adjacency connected components, with no implicit mesh repair or hole filling. Final conforming Gmsh surface meshes are still required.

## Candidate 2 - pad sweep correction

- Independent rigid rotation of candidate 1 gave SF stop 7.24418094 degrees / 0.42158968 mm lateral slip; SR 6.75542490 degrees / 0.33405655 mm slip. Centered diameter 2.6 pads do not fully cover diameter 2.0 buttons at the endpoints. This is a CAD failure, not a hardware-pending item.
- Keep both pad diameters and key outlines; offset only crown centers in Y by SF +0.2018 mm and SR -0.1617 mm. Recomputed stops are +6.936485 / -6.540994 degrees. Conservative projected coverage margins are +0.08865 / +0.12981 mm at the endpoints. Actual final-part assembly and motion checks must still run.
- Trimesh's scipy component counter requires a NumPy array for explicit node IDs; corrected the range argument. No mesh repair is performed.
- Superseded work-branch CI jobs may be cancelled; only final candidate results count. This does not omit any required final mesh or load case.

## Candidate 2 measured outcome (source 59366156, results 013d5c78)

- Nine printable BReps passed single-solid validity and self-interference checks. All nine STL meshes are closed, consistently wound, and connected. Five newly generated meshes used conforming Gmsh triangulation without filling holes. BODY volume: 12644.254639 mm3. H STEP contains 92 independent components.
- Normal side-key presses through their respective stops had no intersections above 0.001 mm3. The forced extra 0.3-degree poses penetrate the intended inward stop (0.00556 / 0.00650 mm3); this is an intentionally blocked pose, not a physically permitted extra motion.
- Straight cap insertion FAILED: SF maximum 0.114403 mm3, SR maximum 0.140351 mm3, around the flat barrel end at Z15.5 and the rounded aperture corners. Merely fitting its Y bounds inside the rectangular aperture does not prove insertion.
- Outward limiting was not proved: both keys remained clear at 0.5 degree outward. The specified high +X stop arm/land does not fit the curved mother profile as assumed.
- Pad coverage correction passed the independent 101-pose conservative projected-rim calculation; minimum positive margins SF 0.088647 and SR 0.129808 mm.
- Retainer route execution stopped before geometry on an input UTF-8 BOM; updated input decoding to utf-8-sig. No route success was claimed.

## Candidate 3 - local interface corrections requiring complete recheck

- Keep the cap outside surface, side aperture outline, hinge axes, pad diameters, five feet and base interfaces. Shorten only the round hinge journal to Z16.4–18.6 (2.2 mm), retaining diameter 2.5 / bore 1.05 and both stationary steel-pin supports. This addresses the measured barrel/corner insertion clash without opening a larger visible hole.
- Reorient the radial outward stop arm inward: X26.7–29.0, Z18.6–19.5, width 0.8. Add its inboard stop and roof connection to the BODY source. This replaces the high +X ear and its external slot; the complete upper bearing remains intact. This is an explicit source correction to D7, not a claim that the original dimensions passed.
- Original retainer pilot radius 0.85 exceeded the SF edge distance 0.60, so the self-tapping hole broke out. New screw coordinates: SF (16.6,45.7), SR (16.6,70.4); round bosses radius 1.8, height 3.5, matching integrated floor pods radius 2.05. SF is between terminal rows. Retain diameter 1.7, depth 3.0 pilots. Update drivers, screws, assembly and stress checks together.
- Add two reference washers, OD3.6 / ID2.2 / thickness0.5. M2x5 shanks now start Z11.6 and end Z16.6; heads bear through washers onto the Z12.1 floor. The previous screw heads floated below the floor.
- Keep diameter1.5 x1.0 integral locating pins. Add an upper entry pocket Z13.0–13.7, leaving the lower 0.3 mm locating socket; enlarge terminal slots to Z15.6–17.2. Retainer routes use a 0.55 mm elevated approach, followed by aligned vertical seating. These changes still require actual voxel and BRep route tests.
- Side GPIO routes terminate at the side of the existing RF_IO_HEADER_EST instead of inside MCU_RADIO_EST; all route clearances remain subject to final checks.
- The CI now exposes each script as a separate job step. G6 cap translation computes exact overlap volume with PET installed, as requested; no unnecessary global-distance claim is made for these insertion poses. G5 still measures exact distances.
