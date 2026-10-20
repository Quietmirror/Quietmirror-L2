"""Prepare immutable inherited parts and directories for an R4 candidate."""
from pathlib import Path
import shutil,json
ROOT=Path(__file__).resolve().parents[2]
def main():
    for rel in ['models/L2_r4/parts','models/L2_r4/reference','reports/l2_r4','handoff/l2_r4','views/l2_r4','_support/work/l2_r4']:(ROOT/rel).mkdir(parents=True,exist_ok=True)
    for n in ['LEFT_KEY','RIGHT_KEY','WHEEL','WHEEL_CARRIER']:
        for ext in ['.step','.stl']:shutil.copy2(ROOT/'models/L2_r3/parts'/(n+ext),ROOT/'models/L2_r4/parts'/(n+ext))
    excluded={'CARRIER_M2x5_1','CARRIER_M2x5_2','SIDE_IO_PCB','SIDE_ROUTE_EST'}
    for p in (ROOT/'models/L2_r3/reference').glob('*.step'):
        if p.stem in excluded or p.stem.startswith(('SF_','SR_','SIDE_FRONT_KEY','SIDE_REAR_KEY','ATK_')):continue
        shutil.copy2(p,ROOT/'models/L2_r4/reference'/p.name)
    p=ROOT/'handoff/l2_r4/TUNING_LOG.md'
    if not p.exists():p.write_text('''# L2-r4 source revisions and rechecks\n\nStatus: CAD checks running. No L2-r4 Release is permitted until all CAD gates complete.\n\n## Candidate 1\n\n- Adopted the supplied execute-all plan and author evidence at f637118455159515a200e6e0f35c0eea1c7d1633 (descendant of the document reference 54dac615).\n- D1-D6 are integrated into the BODY source generation sequence; the finished r3 BODY is not imported for boolean patching.\n- D7 removes the remote tabs, moves hinges, scales the pads, and recalculates the 0.60 mm stop travel.\n- The specified ear starts at Z19.85 but the hinge ends at Z19.5. Added a concealed root bridge joining the ear to the existing web; geometric and movement checks must pass before acceptance.\n- A local outward stop land uses the entry slot allowance so the specified 1.0 mm slot does not inadvertently allow more than 0.5 degree outward play.\n- Heavy processing runs on an isolated public GitHub runner. Each FEM solve must observe at least 10 GB available RAM and use default SPOOLES; no reduced mesh or omitted cases is allowed.\n''',encoding='utf8')
    print('R4 directories and unchanged R3 components prepared',flush=True)
if __name__=='__main__':main()
