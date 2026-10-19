"""Isolate a native slicer failure per actual part; no acceptance substitution."""
import json
import trimesh
from slice_plate import ROOT,OUT,RP,WORK,run,orient,parse_gcode
def main():
    WORK.mkdir(exist_ok=True,parents=True);ini=ROOT/'cad/l2_r4/PLA_0.4_0.20_ESTIMATE.ini';rows=[]
    for name in json.loads((RP/'assembly_inventory.json').read_text())['printable']:
        mesh=trimesh.load_mesh(OUT/'parts'/(name+'.stl'));orient(name,mesh);mesh.apply_translation([10-mesh.bounds[0,0],10-mesh.bounds[0,1],-mesh.bounds[0,2]])
        stl=WORK/(name+'_debug.stl');mesh.export(stl);gc=WORK/(name+'_debug.gcode')
        try:
            run(['--load',ini,'--dont-arrange','--export-gcode','--output',gc,stl],name+'_debug');r=dict(part=name,success=True,**parse_gcode(gc))
        except Exception as e:r=dict(part=name,success=False,error=str(e))
        rows.append(r);(RP/'slicer_failure_isolation.json').write_text(json.dumps(rows,indent=2));print('PART_DIAGNOSTIC',r,flush=True)
if __name__=='__main__':main()
