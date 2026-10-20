"""Strict release accounting from actual version-linked numerical evidence.

Missing, stale or failed evidence never becomes HARDWARE_PENDING. Running this
script may write a failed candidate report; only all-completed CAD permits a
formal release. The release workflow reuses the same check-only assessment.
"""
from pathlib import Path
import argparse,json,math,os,sys,hashlib
import evidence_identity as evidence
ROOT=Path(__file__).resolve().parents[2];RP=ROOT/'reports/l2_r4';OUT=ROOT/'handoff/l2_r4'
HARDWARE_PENDING=[
 '实物侧键：贴膜调整、通断测试、手感',
 '实测按压力',
 'D2F-01F 实物的 FP / OP / TTP',
 'PAW3950 实际镜头高度',
 'D 方案供体型号确认和主板测绘（DONOR_PENDING）',
 '无线、续航、DPI、宏等功能验证',
 '打印实物的称重和试装']

def read(name,default=None):
    p=RP/name;return json.loads(p.read_text()) if p.exists() else ({} if default is None else default)
def every(xs,predicate):return bool(xs) and all(predicate(x) for x in xs)
def all_pass(xs):return every(xs,lambda x:x.get('passed',False))
def number(x):
    try:return float(x)
    except (TypeError,ValueError):return float('nan')

def assess():
    sols=read('solids.json',[]);mesh=read('mesh_self_intersections.json');units=read('mesh_units_and_volume.json',[]);feet=read('foot_planes.json');preservation=read('BODY_C19.json')
    contacts=read('functional_static_contacts.json');printed_hw=read('all_printed_hardware_intersections.json');hw=read('hardware_intersections.json',[])
    wires=read('wire_component_clearances.json');reserves=read('reserved_space_checks.json',[]);pairs=read('component_pairs.json',[])
    windows=read('six_window_samples.json',[]);motion=read('main_and_wheel_motion_raw.json',[]);side=read('side_functional_motion.json',[]);rotation=read('wheel_continuous_rotation.json')
    routes=read('assembly_routes_final.json').get('sequence',[]);caps=read('key_insertion_exact.json',[]);access=read('assembly_access.json',[]);hidden=read('D7_exterior_containment.json',[])
    donor=read('donor_envelope.json');native=read('native_roundtrip.json');inv=read('assembly_inventory.json')
    g8=read('fem/G8.json');s7=read('fem/S7.json');act=read('side_actuation_force_and_tuning.json');kin=read('side_kinematics_independent.json',[])
    optical=read('optical_stack_and_power.json');battery=read('battery_service_path.json');plug=read('battery_plug_access.json');mass=read('CAD_mass.json');sliced=read('slice_summary.json');f2=read('F2_trial.json')
    defs={
      'G1':['solids.json','mesh_self_intersections.json','mesh_units_and_volume.json','foot_planes.json','critical_wall_sections.json','surface_normal_wall_samples.json','BODY_C19.json'],
      'G2':['functional_static_contacts.json','all_printed_hardware_intersections.json','hardware_intersections.json'],
      'G3':['component_pairs.json','wire_component_clearances.json','reserved_space_checks.json'],
      'G4':['six_window_samples.json'],
      'G5':['main_and_wheel_motion_raw.json','side_functional_motion.json','wheel_continuous_rotation.json'],
      'G6':['assembly_routes_final.json','key_insertion_exact.json','assembly_access.json','D7_exterior_containment.json'],
      'G7':['donor_envelope.json','native_roundtrip.json'],
      'G8':['fem/G8.json'],
      'G9':['side_actuation_force_and_tuning.json','optical_stack_and_power.json','battery_service_path.json','battery_plug_access.json','fem/S7.json'],
      'G10':['CAD_mass.json','slice_summary.json','F2_trial.json'],
      'G11':['side_kinematics_independent.json','side_actuation_force_and_tuning.json','side_functional_motion.json','D7_exterior_containment.json']}
    auxiliary=['render_manifest.json','motion_plot_manifest.json','distance_regression.json']
    versions=evidence.verify(sorted(set(sum(defs.values(),[])+auxiliary))) if evidence.MANIFEST.exists() else []
    current={r['report']:r['passed'] for r in versions};gates={}
    def gate(n,ok,summary,data):
        missing=[p for p in defs[n] if not (RP/p).exists()];stale=[p for p in defs[n] if (RP/p).exists() and not current.get(p,False)]
        gates[n]=dict(status='COMPLETED' if ok and not missing and not stale else ('PENDING' if missing else 'FAILED'),summary=summary,metrics=data,missing_reports=missing,stale_reports=stale,evidence=defs[n])
    preservation_pass=(preservation.get('boundary_comparison',{}).get('passed')
                       and number(preservation.get('added_mm3'))<=.001
                       and preservation.get('low_band_clear_of_complete_changes')
                       and len(preservation.get('feet',[]))==5
                       and all(all(number(p['overlap_mm3'])<=.001 for p in f['complete_change_region_checks']) for f in preservation.get('feet',[]))
                       and preservation.get('regression_controls',{}).get('outside_change_rejected'))
    gate('G1',preservation_pass and len(sols)==9 and every(sols,lambda s:s.get('valid') and s.get('solids')==1 and s.get('closed_mesh') and s.get('consistent_winding') and s.get('mesh_components')==1 and s.get('brep_self_interference_check')) and mesh.get('passed') and len(units)==9 and every(units,lambda r:r.get('positive_mesh_volume') and r.get('closed') and abs(r['difference_percent'])<1.) and feet.get('coplanar'),
         '9 个打印件的实体、网格、自相交、尺寸和五脚共面；关键薄壁另列实测截面。',dict(printable_count=len(sols),valid_single_solids=sum(s.get('valid',False) and s.get('solids')==1 for s in sols),closed_meshes=sum(s.get('closed_mesh',False) for s in sols),self_intersecting_faces=sum(r['self_intersecting_faces'] for r in mesh.get('parts',[])),feet=feet))
    gate('G2',contacts.get('passed') and printed_hw.get('passed') and every(hw,lambda r:r['overlap_mm3']<=.001),
         '逐对原始结果保留；仅对明确的接触面、轴孔和自攻螺纹区作局部分解。',dict(static_pairs=len(contacts.get('rows',[])),unresolved_static=sum(not r['passed'] for r in contacts.get('rows',[])),printed_hardware_pairs=len(printed_hw.get('rows',[])),hardware_pairs=len(hw),max_hardware_overlap_mm3=max([r['overlap_mm3'] for r in hw],default=None)))
    battery_pairs=[r for r in pairs if r['b']=='BATTERY_CELL_EST']
    gate('G3',contacts.get('passed') and wires.get('passed') and every(reserves,lambda r:r['overlap_mm3']<=.001) and every(battery_pairs,lambda r:r['pass_check'] and r['gap_mm']>=.5-1e-5),
         '电池固定间隙、软线 0.2 mm 通道、光学/服务区和天线禁区。',dict(battery_minimum_gap_mm=min([r['gap_mm'] for r in battery_pairs],default=None),wire_checks=len(wires.get('rows',[])),reserve_checks=len(reserves),reserved_invasions=sum(r['overlap_mm3']>.001 for r in reserves)))
    gate('G4',len(windows)==6 and every(windows,lambda r:r.get('classified_pass') and len(r['boundary'])==200 and len(r['full_prism'])==1000 and len(r['roof_shell_band'])==1000),
         '每孔 200 个边界点及 1000 个棱柱点；另查 1000 个顶壳点。有意结构变更与原始占用结果单独列出。',dict(windows=[dict(name=r['window'],passed=r.get('classified_pass'),boundary_raw_pass=r['boundary_raw_pass'],prism_raw_pass=r['full_prism_raw_pass'],occupied_points=sum(p['inside'] for p in r['full_prism']),unclassified_samples=sum(not p['classified_pass'] for p in r['boundary']+r['full_prism']+r['roof_shell_band'])) for r in windows]))
    gate('G5',len(motion)==3 and all_pass(motion) and every(motion,lambda g:len(g['samples'])>=21) and len(side)==2 and all_pass(side) and rotation.get('passed'),
         '主键、滚轮点击组和两侧键逐姿态精确 BRep 检查；滚动另以包住实际零件的旋转不变包络验证。',dict(main_wheel=[dict(group=g['group'],poses=len(g['samples']),passed=g['passed']) for g in motion],side=[dict(part=g['part'],poses=len(g['samples']),passed=g['passed']) for g in side],continuous_roll_pass=rotation.get('passed',False)))
    gate('G6',len(routes)==4 and every(routes,lambda r:r['raw_pass']) and len(caps)==2 and all_pass(caps) and len(access)==4 and every(access,lambda r:r['pass_check']) and len(hidden)==2 and all_pass(hidden),
         '微动/挡板体素与精确转折点复核、两键帽每 0.25 mm 直推、顶压钢销及底部螺丝刀可达。',dict(loose_part_poses=sum(r['voxel_poses'] for r in routes),cap_translation_poses=sum(len(r['samples']) for r in caps),access_checks=len(access),max_cap_overlap_mm3=max([p['overlap_mm3'] for r in caps for p in r['samples']],default=None)))
    gate('G7',gates['G2']['status']=='COMPLETED' and gates['G3']['status']=='COMPLETED' and donor.get('candidate_geometric_pass') and native.get('all_valid') and native.get('full_step_roundtrip',{}).get('valid') and len(native.get('parts',[]))==inv.get('independent_components',-1)>=89,
         'H 估计包络与独立组件整机；D 仅交付指定高度下的保守最大连续板区及孔中心允许域。',dict(H_components=len(native.get('parts',[])),D_status=donor.get('status'),D_area_mm2=donor.get('area_mm2'),D_bounds_mm=donor.get('bounds_mm')))
    gate('G8',g8.get('status')=='COMPLETED' and len(g8.get('rows',[]))==18 and every(g8.get('rows',[]),lambda r:r['passed'] and r['ratio']>=1 and not r['author_difference_requires_investigation']),
         '六工况 × 三网格，实际 SPOOLES；所有比值≥100%，超过3%的作者偏差有独立调查。',dict(solves=len(g8.get('rows',[])),minimum_ratio=min([r['ratio'] for r in g8.get('rows',[])],default=None),rows=g8.get('rows',[])))
    s4= len(act.get('keys',[]))==2 and every(act['keys'],lambda r:len(r.get('force_positions',[]))==3 and every(r['force_positions'],lambda p:math.isfinite(p['ideal_force_N']) and p['ideal_force_N']>0))
    sim=dict(S1=gates['G2']['status']=='COMPLETED',S2=gates['G5']['status']=='COMPLETED',S3=len(act.get('keys',[]))==2 and every(act['keys'],lambda r:r['cad_pass']),S4=s4,S5=number(optical.get('lens_bottom_to_ground_mm'))>0 and optical.get('skate_mm')==.8,S6=battery.get('passed',False) and plug.get('passed',False) and wires.get('passed',False),S7=s7.get('status')=='COMPLETED' and len(s7.get('rows',[]))==12 and all_pass(s7.get('rows',[])),S8=gates['G8']['status']=='COMPLETED',S9=len(mass.get('parts',[]))==9 and number(sliced.get('total_filament_g'))>0)
    gate('G9',all(sim.values()),'S1–S9 的 CAD 证据闭合；实际器件参数和实测性能按限定清单保留。',dict(simulations=sim,side_forces=act.get('keys',[]),optical_stack=optical,S7_rows=s7.get('rows',[]),battery_service_pass=battery.get('passed',False),plug_access_pass=plug.get('passed',False)))
    gate('G10',len(mass.get('parts',[]))==9 and len(sliced.get('per_part',[]))==9 and number(sliced.get('total_filament_g'))>0 and sliced.get('scale')==1 and number(sliced.get('minimum_xy_bounding_rect_gap_mm'))>=5 and sliced.get('plate_roundtrip',{}).get('passed') and number(f2.get('real_slice',{}).get('total_filament_g'))>0,
         '逐件自适应 CAD 体积、密度假设，以及真正切片后的耗材、时间和单盘排布。',dict(volume_mm3=mass.get('total_volume_mm3'),PA12_g=mass.get('total_PA12_g'),solid_PLA_g=mass.get('total_solid_PLA_g'),slicer_total_PLA_g=sliced.get('total_filament_g'),slicer_time=sliced.get('time'),minimum_plate_gap_mm=sliced.get('minimum_xy_bounding_rect_gap_mm')))
    gate('G11',len(side)==2 and all_pass(side) and len(kin)==2 and every(kin,lambda r:r['pad_coverage_pass'] and len(r['samples'])>=101) and act.get('range_pass') and all_pass(hidden),
         '实际铰轴下的压盘覆盖、±0.35 mm 贴膜调整链、外向止挡及不破外表面。',dict(coverage_min_mm={r['part']:min(p['conservative_coverage_margin_mm'] for p in r['samples']) for r in kin},film_range_mm=act.get('film_range_mm'),outward_stop_angles_deg={r['part']:r['outward_stop_angle_deg'] for r in side}))
    required_assets=['models/L2_r4/FULL_ASSEMBLY_H.step','models/L2_r4/FULL_ASSEMBLY_H.FCStd','models/L2_r4/D_MAX_BOARD_ENVELOPE.step','models/L2_r4/L2_r4_H_ALL_PARTS_SINGLE_PLATE.3mf','models/L2_r4/SIDE_MODULE_F2_TRIAL.3mf','views/l2_r4/L2_r4_H_SIX_VIEWS_SHEET.png','views/l2_r4/PRINT_PLATE.png']
    required_assets += ['views/l2_r4/'+prefix+n+'.png' for prefix in ['H_','INSIDE_'] for n in ['TOP','BOTTOM','FRONT','BACK','LEFT','RIGHT']]
    required_assets += ['views/l2_r4/'+n+'.png' for n in ['H_ISO_FRONT','H_ISO_REAR','SIDE_MOTION_OVERLAY','SECTION_Z16p6','SECTION_Y50p25','SECTION_Y64p45','R3_VS_L2_r4_TOP_RIGHT_BOTTOM']]
    missing_assets=[p for p in required_assets if not (ROOT/p).exists()]
    # Existing stale pictures or binary CAD must never certify a new model.
    asset_identity={}
    for report,key in [(read('render_manifest.json'),'files'),(read('motion_plot_manifest.json'),'files'),(native,'artifact_sha256'),(sliced,'artifact_sha256'),(f2,'artifact_sha256')]:asset_identity.update(report.get(key,{}))
    asset_problems=[]
    for p in required_assets:
        if p.endswith('D_MAX_BOARD_ENVELOPE.step'):continue # Bound to producer's geometry/outline numerical report.
        if p not in asset_identity:asset_problems.append('No produced artifact identity: '+p)
        elif (ROOT/p).exists() and not evidence.hash_matches(ROOT/p,asset_identity[p]):asset_problems.append('Artifact version mismatch: '+p)
    for p in auxiliary:
        if not current.get(p,False):asset_problems.append('Stale/missing image producer: '+p)
    regression=read('distance_regression.json')
    if not regression.get('passed') or len(regression.get('samples',[]))!=5:
        asset_problems.append('Original-solid distance regression incomplete or failed')
    for p in sorted(set(sum(defs.values(),[]))):
        if (RP/p).exists() and 'BRepExtrema_crop' in (RP/p).read_text(encoding='utf8'):
            asset_problems.append('Withdrawn cropped-distance method in acceptance report: '+p)
    s7_numerical= len(s7.get('rows',[]))==12 and all(r.get('equilibrium_pass') and number(r.get('global_p95_MPa'))<=10 and number(r.get('side_frame_region',{}).get('p95_MPa',0))<=10 for r in s7.get('rows',[]))
    if not s7_numerical and gates['G9']['status']=='COMPLETED':gates['G9']['status']='FAILED'
    complete=all(r['status']=='COMPLETED' for r in gates.values()) and not missing_assets and not asset_problems
    return dict(status='CAD_COMPLETE / HARDWARE_PENDING' if complete else 'CAD_INCOMPLETE — RELEASE PROHIBITED',gates=gates,version_checks=versions,missing_assets=missing_assets,artifact_identity_problems=asset_problems,source_work_branch='l2-r4-build',tag='L2-r4',hardware_pending=HARDWARE_PENDING,printed_parts=mass.get('parts',[]),mass_and_slice=gates['G10']['metrics'],inventory=inv,baseline='Quietmirror/github@f1b1090931d717117287ea2b79c2e14ddc234937',author_evidence='Quietmirror/Quietmirror-L2@f637118455159515a200e6e0f35c0eea1c7d1633',evidence_limit='精确值仅对应声明的模型与离散姿态；封闭网格、线弹性模拟和参考电子包络均不等于实物装配/打印强度/电子性能认证。')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check-only',action='store_true');args=ap.parse_args();a=assess()
    print(json.dumps(dict(status=a['status'],gates={n:dict(status=g['status'],stale=g['stale_reports'],missing=g['missing_reports']) for n,g in a['gates'].items()},missing_assets=a['missing_assets']),indent=2,ensure_ascii=False))
    if args.check_only:return 0 if a['status']=='CAD_COMPLETE / HARDWARE_PENDING' else 1
    OUT.mkdir(exist_ok=True);(OUT/'FINAL_ACCOUNTING.json').write_text(json.dumps(a,indent=2,ensure_ascii=False),encoding='utf8')
    text='# L2-r4 CAD 门槛总表\n\n状态：**'+a['status']+'**\n\n| 门槛 | 结论 | 判据和证据 |\n|---|---|---|\n'
    for n,g in a['gates'].items():
        text+=f"| {n} | {g['status']} | {g['summary']} |\n"
    text+='\n## 数值与来源\n\n'
    for n,g in a['gates'].items():
        text+='### '+n+'\n\n'+g['summary']+'\n\n'
        text+='证据：'+', '.join('['+p+'](../../reports/l2_r4/'+p+')' for p in g['evidence'])+'。\n\n'
        if g['missing_reports']:text+='缺失：'+', '.join(g['missing_reports'])+'。\n\n'
        if g['stale_reports']:text+='未通过版本一致性核对：'+', '.join(g['stale_reports'])+'。\n\n'
        text+='详细数值见 [FINAL_ACCOUNTING.json](FINAL_ACCOUNTING.json) 的 `gates.'+n+'.metrics`。\n\n'
    text+='## 证据范围\n\n'+a['evidence_limit']+'\n\n## 仅以下实物项目保留\n\n'+''.join(str(i+1)+'. '+p+'\n' for i,p in enumerate(HARDWARE_PENDING))
    (OUT/'GATES.md').write_text(text,encoding='utf8');return 0

if __name__=='__main__':sys.exit(main())
