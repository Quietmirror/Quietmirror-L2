from pathlib import Path
import subprocess,sys,json,math
r=Path.cwd();py=r/'.tools/cad-env/Scripts/python.exe';slicer=r/'.tools/PrusaSlicer-2.9.6/PrusaSlicer-2.9.6/prusa-slicer-console.exe';ini=r/'slicing/V0.6_PLA_0.4_0.20_ESTIMATE.ini';out=r/'exports/v06'
def run(args,log):
 with (r/'.tools'/log).open('w',encoding='utf8') as f:subprocess.run([str(x) for x in args],stdout=f,stderr=subprocess.STDOUT,check=True)
with (r/'reports/v06/slicer_model_info.txt').open('w') as f:subprocess.run([str(slicer),'--info',str(out/'quietmirror_fingertip_V0.6_FIT.stl')],stdout=f,check=True)
run([slicer,'--load',ini,'--export-gcode','--output',r/'.tools/V0.6_estimate_with_support.gcode',out/'quietmirror_fingertip_V0.6_FIT.stl'],'slice_v06.log')
run([slicer,'--load',ini,'--save',r/'slicing/V0.6_PLA_0.4_0.20_FULL.ini'],'profile_v06.log')
run([slicer,'--load',ini,'--center','110,110','--export-3mf','--output',out/'quietmirror_fingertip_V0.6_PRINT.3mf',out/'quietmirror_fingertip_V0.6_FIT.stl'],'3mf_v06.log')
run([py,'cad/embed_3mf_profile.py','--version','0.6'],'embed_v06.log')
run([slicer,'--export-gcode','--output',r/'.tools/V0.6_3mf_roundtrip.gcode',out/'quietmirror_fingertip_V0.6_PRINT.3mf'],'roundtrip_v06.log')
run([py,'cad/check_3mf_roundtrip.py','--version','0.6'],'3mf_check_v06.log')
run([py,'cad/analyze_slice.py','--version','0.6'],'slice_analysis_v06.log')
sys.path.insert(0,str(r/'cad'));import analyze_slice as a
parts=[]
for name,stem in [('SHELL','quietmirror_fingertip_V0.6_SHELL'),('front side cap','side_button_1_V0.6_PRINT'),('rear side cap','side_button_2_V0.6_PRINT')]:
 g=r/'.tools'/(stem+'.gcode');run([slicer,'--load',ini,'--export-gcode','--output',g,out/(stem+'.stl')],stem+'.log');a.GCODE=g
 seg,z,cat,lengths,footer=a.parse();factor=math.pi*(1.75/2)**2/1000*1.24
 mass={k:v*factor for k,v in lengths.items()};d=dict(name=name,source='exports/v06/'+stem+'.stl',model_g=sum(v for k,v in mass.items() if not k.startswith('Support') and k!='Skirt/Brim'),support_g=sum(v for k,v in mass.items() if k.startswith('Support')),adhesion_g=mass.get('Skirt/Brim',0),total_g=float(footer['filament used [g]']),time=footer['estimated printing time (normal mode)']);parts.append(d);print(d,flush=True)
(r/'reports/v06/separate_parts_slice.json').write_text(json.dumps(dict(slicer='PrusaSlicer 2.9.6',profile='slicing/V0.6_PLA_0.4_0.20_ESTIMATE.ini',parts=parts,separate_jobs=True,estimates_only=True),indent=2),encoding='utf8')
print('All final slices complete',flush=True)
