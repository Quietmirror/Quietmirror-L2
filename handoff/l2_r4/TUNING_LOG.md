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
