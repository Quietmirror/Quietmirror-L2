"""Publish measured results and explicit gaps; never promote missing checks."""
from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[2];RP=ROOT/'reports/l2_r3';H=ROOT/'handoff/l2_r3';H.mkdir(exist_ok=True)
def get(n,default=None):
    p=RP/n;return json.loads(p.read_text(encoding='utf8')) if p.exists() else default
def write(n,text):(H/n).write_text(text.strip()+'\n',encoding='utf8')
def table(headers,rows):return '| '+' | '.join(headers)+' |\n|'+'|'.join(['---']*len(headers))+'|\n'+''.join('| '+' | '.join(str(v) for v in r)+' |\n' for r in rows)
def main():
    solids=get('solids.json',[]);static=get('static_pairs.json',[]);components=get('component_pairs.json',[]);motions=get('motion_samples.json',[]);feet=get('foot_planes.json',{});extra=get('openings_check.json',{});native=get('native_roundtrip.json',{});sliced=get('slice_summary.json',{});actuation=get('side_actuation_housing_check.json',[])
    collisions=[r for r in static if r['overlap_mm3']>.001];tight=[r for r in static if not r['pass_check'] and r['overlap_mm3']<=.001]
    cfail=[r for r in components if not r['pass_check']];movefail=[]
    for motion in motions:
        for sample in motion['samples']:
            if sample.get('beyond_stop'):continue
            for pair in sample['pairs']:
                if pair['overlap_mm3']>.001:movefail.append(dict(part=motion['part'],angle=sample['angle_deg'],**pair))
    total=sum(r['volume_mm3'] for r in solids);mass=total*.00101
    g1=len(solids)==8 and all(r['valid'] and r['solids']==1 and r['closed_mesh'] and r['mesh_components']==1 and r['brep_self_interference_check'] is True for r in solids)
    actfail=[dict(part=r['part'],**s) for r in actuation for s in r['samples'] if s['key_housing_intersection_mm3']>.001 or s['shim_housing_intersection_mm3']>.001]
    functional=get('functional_motion.json',{})
    functional_fail=[dict(part=g['part'],angle=s['angle_deg'],**p) for g in functional.get('groups',[]) for s in g['samples'] for p in s['pairs'] if p['overlap_mm3']>.001]
    insertion=get('insertion_attempts.json',{})
    insertion_peak=max((r['overlap_mm3'] for r in insertion.get('carrier_straight_up',[])),default=0.)
    donor=get('donor_placeholder_check.json',{})
    donor_hits=[r for r in donor.get('pairs',[]) if r['overlap_mm3']>.001]
    gates=[['G1','PASS' if g1 else 'INCOMPLETE',f'{len(solids)} 个打印件；CAD 单实体、自相交和封闭网格见 solids.json'],
           ['G2','PASS' if len(static)==28 and not collisions and not tight else 'INCOMPLETE',f'打印件 {len(static)}/28 对；穿模 {len(collisions)} 对；不足目标间隙 {len(tight)} 对'],
           ['G3','INCOMPLETE',f'最终装配包络检查 {len(components)} 对，其中 {len(cfail)} 项未满足通用阈值；作者 62 项原始证据未提供'],
           ['G4','INCOMPLETE',f'O3 贯通：{extra.get("O3_body_pass","UNVERIFIED")}；原六孔多边形保留，最终曲面边界等价性未完整证明'],
           ['G5','INCOMPLETE',f'{len(motions)}/5 组打印件运动穿模记录 {len(movefail)}；微动壳体/滚轮随动组件 {len(functional_fail)}；运动最小间隙曲线未认证'],
           ['G6','INCOMPLETE',f'Ø2钢销顶部探针已检查；载架直线上装最大重叠 {insertion_peak:.3f} mm³，此路径不能使用，倾斜装入未证明'],
           ['G7','INCOMPLETE',f'H 为估计包络；D 假设板 {len(donor_hits)} 处相交，不能宣称真实供体适配'],
           ['G8','3D_FEM_BLOCKED','本机直接求解触发系统低内存保护；不得沿用 r2 数字冒充 r3 三档刚度'],
           ['G9','INCOMPLETE','S1/S2/S3/S5/S6/S9 提供相应证据；S4 实际按压力、S7 预紧/托架应力和 S8 刚度未完成认证'],
           ['G10','PASS_CAD_ESTIMATE',f'CAD {total:.3f} mm³；PA12 密度 1.01 时 {mass:.3f} g；切片 {sliced.get("total_filament_g","UNVERIFIED")} g'],
           ['G11','INCOMPLETE' if actfail else 'UNVERIFIED',f'键帽/垫片对壳体包络的行程干涉记录 {len(actfail)}；实物微动、PET 调整和通断未测']]
    fem=get('fem_status.json')
    if fem:gates[7][1]=fem.get('G8_status','INCOMPLETE');gates[7][2]=fem.get('summary',gates[7][2])
    summary=dict(version='L2-r3',status='INCOMPLETE',prerelease=True,gates=[dict(id=a,status=b,evidence=c) for a,b,c in gates],static_overlap_count=len(collisions),static_clearance_failures=len(tight),motion_overlap_samples=len(movefail),estimated_component_failure_count=len(cfail),print_volume_mm3=total,PA12_g=mass,slice=sliced,native=native,physical_tests=False)
    (RP/'release_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    accounting=dict(printed_parts=[dict(name=r['name'],volume_mm3=r['volume_mm3'],PA12_g=r['volume_mm3']*.00101) for r in solids],printed_volume_mm3=total,PA12_density_g_cm3=1.01,PA12_printed_mass_g=mass,plan_budget_g=17.42,budget_difference_g=mass-17.42,PLA_slicer=sliced,total_assembled_mouse_mass='UNVERIFIED: battery, PCB, fasteners and material specifications not measured',unverified=['Full global minimum wall thickness','PCB and lens dimensions','Radio/firmware/receiver compatibility','400-6400 DPI, 1kHz, macros, LOD, no sync','12h full-power endurance','Physical switch feel and reset'])
    (H/'FINAL_ACCOUNTING.json').write_text(json.dumps(accounting,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    write('FINAL_ACCOUNTING.md',f'''# L2-r3 实际核算 · INCOMPLETE

{table(['零件','CAD 体积 mm³','PA12 估重 g'],[[r['name'],f"{r['volume_mm3']:.3f}",f"{r['volume_mm3']*.00101:.3f}"] for r in solids])}

合计 **{total:.3f} mm³ / {mass:.3f} g**。用自适应 BRep 积分，PA12 密度 1.01 g/cm³。与文档 17.42 g 预算相差 {mass-17.42:+.3f} g。这是打印件质量，不含电子元件、金属件和脚贴。

PLA 真实切片总耗材：**{sliced.get('total_filament_g','UNVERIFIED')} g**；时间 **{sliced.get('time','UNVERIFIED')}**。切片与 CAD 密度/填充/支撑不同，不应直接当作同一种材料的测量误差。

零件、支撑及裙边按 G-code TYPE 分类的估重见 [slice_summary.json](../../reports/l2_r3/slice_summary.json)。这不是实际称重。
''')
    write('SECOND_CHECK.md',f'''# L2-r3 独立复核

状态：**INCOMPLETE / 预发布**。用户已明确要求继续复核、建模和 GitHub 发布，不通过则预发布。本轮没有把附件中“作者已验证”当成本机验收结论。

基准：Quietmirror/github@f1b1090931d717117287ea2b79c2e14ddc234937 的 R3.2。当前 r3 方案见 [原文](../../specs/Quietmirror_L2_r3_FINAL_Build_and_Release_2026-10-18.md)。R3.2、R3.3、r1/r2 历史保留。

{table(['门槛','状态','证据/限制'],gates)}

K1：重新导入原九个打印 STEP，自适应体积 18506.678218 mm³，与文档一致。K2：既有独立梁验证误差约 −1.47%/−1.38%；本轮新迭代求解链的梁验证误差为 {get('FEM_beam_2.4.json',{}).get('analytic_error_percent','UNVERIFIED')}%，详见FEM_beam_2.4.json。K3：r3 使用 curvature=24 和不同最小网格尺寸，已生成新基线网格，原 r2 网格数值不替代它。

K5：保留原 r2 的 12 组来源分类，实际修改在版本化 mechanics.py 中完成。Y54 外臂在源生成时裁至 X±6；原后横梁、滚轮枢纽、主键铰座与底部接口保留。K6：旧侧键开口、捕获销和 M2 工具通道随旧循环一起取消。

K9：本轮载架由文档坐标独立生成。未收到作者 r3_parameters.json、参考 STEP、fem_variants.py 或 repo_scan 目录，无法声称与作者参考模型逐项差异≤0.02 mm。实际修正和失败项见配套报告。

测量中 AABB 下界只用于证明某些零件距离已超过验收阈值，不冒充精确最小距离；BODY 只截取目标附近的局部区域做精确求交和阈值距离检查。运动是每组至少 21 个姿态，侧键另有超止挡 0.3° 诊断，不能证明全部连续路径或真实装配。
''')
    write('PARAMETERS_CORRECTED.md','''# L2-r3 参数与实现修正

1. 以新 r3 文档作为当前执行方案；旧 r2 文本归档。未提供的作者 JSON 不伪造，独立转录结果见 reports/l2_r3/parameters_implemented.json。
2. 止挡筋 Z15.9–16.4 为 0.5 mm，保留坐标端面，修正文中“高0.6”的冲突。
3. 推杆名义运动约0.6003/0.6001 mm，保留0.35静止间隙时，微动压入仅约0.25 mm。平压盘加0.33垫片时在倾转末段碰微动外壳，实测几何记录已归档；改为Ø3、高0.6、R2.175圆顶接触面及随形垫片，端点不变。新接触面仍须真实微动测试。
4. 文档估计的键帽内表面 X 与实际母面不同。推杆根部和卡舌连接筋延至实际键帽，端点及卡舌坐标不变；随后以圆角键面轮廓裁剪连接筋，去除隐藏穿模。初次碰撞位置保存在 pre_correction_overlap.json。
5. 端子槽明确为 Y宽1.6、Z高1.2、中心Z16.6；端子参考截面0.9×0.4。PCB窄中座只承托，两个端座补M1.2固定孔，仍需真实电路板/焊接空间验证。
6. 钢销竖直范围14.75–20.25；固定凸耳14.2–15.2、19.8–20.8；隐藏铰节配合与薄壁需试打印校准。孔径0.95/1.05不能当作FDM实际成孔精度保证。
7. 外键面使用母面沿X偏移0.20形成，属于法向偏移的近似；不能冒称严格等距面。F2外偏0.30为单独试验件，没有另加文档所称的0.15外凸脊，因此实际名义偏移0.30，不冒称总突出0.45。
8. 主键局部薄壳和纵/斜筋保留原触发、铰链、前端区域；硬止挡附近额外保留原厚度，纵筋从Y14.5开始，避免侵入止挡运动空间。固定滚轮铰座的前缘局部退让至Y47.5，轴孔不变、剩余前壁至少1.325。筋根R0.4尚未完整落实，列为未通过细节。
9. 原五脚粘贴面保持Z5.2，示意脚贴0.8，垫面Z4.4，原外缘Z5.0，外缘离垫0.6。没有按手长再次等比放大。
10. 供体仍为用户所称ATK A1 Plus且待确认，不能替换为A1 Pro。H的PAW3950只是传感器型号，不代表统一PCB或已验证无线功能。
11. 重型程序使用现有 -MemoryGiB 4 参数；不使用不存在的 -LimitGB 8，不更改系统内存策略。
12. Ø2顶部视线试验最初分别被0.467/0.448mm³材料挡住。在(29,45)/(29,70)从Z20.8向上作Ø2.1局部通道，保留下方固定凸耳和压配孔；这改变两处局部窗口/上圈边缘，属于为满足B7作出的明确偏离，不能声称六孔边界严格完全不变。
13. 原主键内侧固定轴座局部轴向厚度从2.4降为2.2（内面|X|8.7→8.9），轴孔/轴线不变，给滚轮载架让位。仍存在的功能配合和目标间隙差异见最终干涉报告。
14. 主键纵/斜筋在按下末端与微动硬壳相交，已按21姿态反变换的硬壳外扩0.3包络局部削减加强筋，保留触发柱。编码器假设转接板在4.1°末端有0.0033mm³碰撞，新增局部避让缺口；不要求切割任何真实供体PCB。
''')
    pairs_text=table(['A','B','间隙/下界 mm','相交 mm³','说明'],[[r['a'],r['b'],f"{r['gap_mm']:.4f}",f"{r['overlap_mm3']:.6f}",r.get('distance_kind','exact')] for r in static])
    write('INTERFERENCE_REPORT.md',f'''# 最终模型干涉报告

静态打印件检查 {len(static)}/28 对。穿模 {len(collisions)} 对，未达到通用间隙阈值 {len(tight)} 对。

{pairs_text}

有意接触：载架与安装耳、微动与载架承压面、侧板与安装座、卡舌静止时与端圈、硬止挡、钢销及螺钉功能配合。即使是有意接触，非螺纹实体相交体积仍应≤0.001 mm³。不能用“有意接触”解释明显穿模。

电子检查未满足阈值的项目、运动逐姿态数据见 [component_pairs.json](../../reports/l2_r3/component_pairs.json)、[motion_samples.json](../../reports/l2_r3/motion_samples.json)。电子件均是估计包络；触点、焊脚、插头和线束需实测。零间隙垫片另查 [side_actuation_housing_check.json](../../reports/l2_r3/side_actuation_housing_check.json)。

主键/中键硬壳及滚轮、编码器、固定螺钉、转接板随动的附加检查见 [functional_motion.json](../../reports/l2_r3/functional_motion.json)，最终大于0.001mm³记录 {len(functional_fail)} 条。托架直线上装路径最大相交 {insertion_peak:.3f} mm³，不能按此路径组装。D供体假设板碰撞 {len(donor_hits)} 对，详见donor_placeholder_check.json；这只否定当前假设布局，不是对未知真实ATK板的测量。

最终全局最薄壁尚未认证；已提供关键位置的直线截面采样和名义截面。刀口、小孔和配合不适合直接凭渲染判断。
''')
    write('OPENINGS_RESOLUTION.md',f'''# 开口来源与处理

O1/O2/O4：原侧键M2工具路径，随旧侧键机构循环在源码中取消，不向成品孔洞贴补片。PH1/PH2：原捕获销孔随旧滑块结构一起取消。

O3：原Y50/Z19、Ø2.35滚轮钢销路径保留；新R5顶圈在合并前也切出对应通道。最终BODY求交体积 {extra.get('O3_body_intersection_mm3','UNVERIFIED')} mm³，贯通判定 {extra.get('O3_body_pass','UNVERIFIED')}。

六个原顶面窗口仍使用原多边形坐标和圆角生成器；+X侧保留遮罩按r3 B9更新。最终全部曲面边界与旧版的严格等价、每项独立体积差未完成证明，不把源码一致等同于完整几何证明。

另外为侧键竖销添加了两处Ø2.1顶部通道，起点Z20.8，轴心(29,45)/(29,70)。这是局部窗口边缘变化，G4的严格边界一致条件未通过；最终Ø2直线插入探针结果见pin_access_precheck.json。
''')
    write('ASSEMBLY_SEQUENCE.md','''# 装配顺序与路径限制

1. 试打印销孔/螺孔，核对真实钢销和自攻螺钉，去除支撑。主键、滚轮和侧键均为独立运动件，需要对应轴销及微动；塑料打印件本身不提供真实开关回弹。
2. 先装原主键/中键微动、USB转接板及滚轮编码器组件。滚轮载架横销从保留O3通道装入；在侧键帽遮挡路径之前完成。
3. 将两颗侧键微动和SIDE_IO_PCB安装到载架，完成焊接与绝缘。两个端部PCB座使用拟定M1.2固定，中座承托。
4. 托架目标落位是+X耳顶面，以两颗M2×5从耳下向上固定。直线从下向上是否被安装耳挡住，见insertion_attempts.json；不能把直线受阻的路径写成可执行装配步骤。倾斜绕耳的完整路径目前未证明。若叠H转接件，置于耳下并重新核算螺钉长度。
5. 侧键先斜插卡舌，再摆入铰链端，从顶面窗口插入Ø1×5.5销。顶入视线和完整斜插路径是不同检查；后者目前UNVERIFIED。
6. 安装H电子组件、线束、电池、开关和天线，核对光路及每个插头的装拆空间。D方案不能依据占位板直接拆装真实供体。
7. 贴0.8脚贴后实测镜头光学基准。调侧键PET垫片，核对全行程不会先碰微动外壳，再做通断试验。

这是拟定装配顺序，不是完成实物装配的记录。所有未知板型、螺纹、线材弯曲半径和胶层厚度均待验证。
''')
    write('SIDE_KEY_FUNCTION.md',f'''# 侧键动作与功能

铰轴：SF(29,45)、SR(29,70)，沿Z。名义止挡6.80°/6.37°。推杆端点刚体旋转向内约0.6003/0.6001 mm；零间隙且PT=0.5时名义触发角5.625°/5.280°。

文档名义0.35间隙必须调整。原平压盘和垫片的倾转干涉已归档，当前改为Ø3、高0.6、R2.175圆顶压盘和0.33mm随形垫片，显示0.02残余间隙。新结构全行程对微动矩形壳体的相交样本有 **{len(actfail)}** 条，详见原始JSON；未经实测不能声称“每次必然触发”。

Omron D2F-01F官方资料：OF上限0.74N、PT上限0.5mm、OT下限0.25mm、MD上限0.12mm、OP5.5±0.3mm。这些是开关规格，不是成品侧键的实测力度。参考 https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2f.pdf 。

实物功能 **UNVERIFIED**：键面中点、近铰端、远端各按10次，记录触发/复位、侧向摩擦、晃动及误触。未获得真实FP/OP/TTP前不得假定制造公差。

另提供side_force_estimate.json：理想杠杆力矩计算表明，靠近铰轴的按压位置可能需要很大的力，不能把0.74N开关OF直接写成整只侧键力度。例如SF在Y45.2、离轴仅0.2mm处，理想计算约19.4N；中点约0.74N。该模型不含摩擦和曲面法向变化，必须通过实物验证并考虑缩小可按区域或后续调整铰轴位置。
''')
    write('TUNING_LOG.md','''# 侧键实物调试记录 · 未执行

| 项目 | SF | SR |
|---|---|---|
| 微动实际型号/批次 | 待测 | 待测 |
| FP / OP / TTP | 待测 | 待测 |
| 无垫片静止间隙 | 待测 | 待测 |
| PET厚度、调整后间隙 | 待测 | 待测 |
| 触发后余量及压盘/外壳间隙 | 待测 | 待测 |
| 中点10次触发/复位 | UNVERIFIED | UNVERIFIED |
| 近铰端10次触发/复位 | UNVERIFIED | UNVERIFIED |
| 远端10次触发/复位 | UNVERIFIED | UNVERIFIED |

记录真实结果后再更改状态，不能用CAD姿态替代通断试验。
''')
    write('INTERNAL_COMPONENTS_SIMULATION.md','''# 电子包络、力学与功能边界

H模型分别包含传感器板、PAW3950包络、匹配镜头包络、RF/MCU板、充电/电源器件、电池与插头、线束、USB-C、开关及天线参考。它们不是已选定/已测量零件。D方案仍为ATK A1 Plus未确认供体板的占位，不含虚构板孔。

目标400–6400DPI、2.4GHz低延迟1kHz、宏、LOD、两侧键/中键、开关、充电和不含sync技术，均需主板、固件、接收器及软件共同落实。当前没有完成PCB电路或固件，状态UNVERIFIED。

12小时满功率续航按 C_mAh >= 12 × I_average_mA / usable_fraction 校核。若可用比例0.75，平均10/15/20/25mA分别需要160/240/320/400mAh。18×22×6只是外形包络，不能从尺寸推断容量；容量不够时必须改电池、功耗或布局。

镜头轴垂直鼠标垫。当前包络下镜头最低Z7.8、脚贴粘贴面Z5.2、脚贴0.8，镜头包络最低点至垫面为3.4mm；文档“3.1”与该尺寸链不一致。实际焦距取决于镜头规定的光学基准，不能将包络底面当作已认证焦平面。

FEM使用独立网格/载荷脚本，材料E1500MPa、ν0.35；r3新增曲率细化。直接求解在本机两次触发低内存保护；分离式ITERATIVE CHOLESKY的梁校验通过，但整壳在615.3秒后因系统可用内存低于512MiB而停止，当时该求解任务峰值占用约0.471GiB，并非触及其4GiB上限。完整原始输入及日志留在本地，公开摘要见reports/l2_r3/fem_status.json与fem_resource_summary.json。三档最终BODY刚度≥原版尚未证明；不调整载荷或材料以凑参考值。

托架5N应力、安装耳预紧应力、实际开关力、真实光学高度和无线性能尚未通过。打印试握反馈记录握宽、顶掌、手指拖地、滚轮/侧键触达、抬鼠稳定性，再决定下一轮修改。
''')
    write('SLICE_REPORT.md',f'''# 单盘切片

真实切片器：PrusaSlicer 2.9.6。255×155mm床面是3D45配置假设，PLA、0.4mm喷嘴、0.20mm层高，模型不缩放。提供3MF，不发布可直接发送给未知打印机的G-code。

总耗材 **{sliced.get('total_filament_g','UNVERIFIED')} g**；预计 **{sliced.get('time','UNVERIFIED')}**。

方向：BODY保持装配Z朝上，原外缘最低面落床；主键与侧键保持Z朝上；托架平底朝下；滚轮绕Y转90°使轴竖直；滚轮载架平放。支撑开启，包括主键悬垂触发柱/铰链、BODY横梁和顶壳、侧键推杆/卡舌、滚轮轴端及载架悬垂。细小配合面去支撑后必须检查和修整。

零件间距至少12mm，给支撑底部和2mm外缘brim留出空间；第一次8mm排布出现切片路径冲突，已重新排布。各零件尺寸、放置位置、嵌入配置及按挤出角色估重见 [slice_summary.json](../../reports/l2_r3/slice_summary.json)。同一盘高度不同可能影响小件冷却，实际打印机需重切片。
''')
    write('README.md','''# Quietmirror L2-r3 交付目录

当前状态INCOMPLETE。先读SECOND_CHECK、INTERFERENCE_REPORT和SIDE_KEY_FUNCTION，再选择打印试验件。FINAL_ACCOUNTING提供CAD质量和真实切片结果。历史r2复核仍保留于handoff/l2_r2。
''')
    write('RELEASE_NOTES.md',f'''# Quietmirror L2 r3 — INCOMPLETE

此版本是预发布：{'; '.join(a+' '+b for a,b,c in gates if b not in ['PASS','PASS_CAD_ESTIMATE','PASS_SAMPLED'])}。不能当作已认证装配、无线功能或实物侧键通过的版本。

按新r3方案重建原R3.2：保留六孔与五脚基准，改杠杆侧键和可拆载架，主键局部减薄加筋、滚轮改辐条结构。提供H整机、D供体占位、分件STEP/STL、可编辑源、FreeCAD装配和单盘3MF，以及实际CAD六视图、内部图和独立检查数据。

{table(['门槛','结果','证据'],gates)}

打印件PA12估重{mass:.3f}g；PLA切片{sliced.get('total_filament_g','UNVERIFIED')}g，{sliced.get('time','UNVERIFIED')}。两者不含相同的支撑/材料假设，整机质量未确认。

保留CERN-OHL-P-2.0和原NOTICE署名。历史版本未删除。

L2-r3-bundle.zip是模型与视图包；源码、方案和完整报告同时位于仓库，GitHub自动提供的Source code压缩包包含全部仓库文件。不要将模型包当作完整源码归档。
''')
    # Preserve the previous landing pages before switching the current entry.
    archive=ROOT/'handoff/archive/l2_r2';archive.mkdir(parents=True,exist_ok=True)
    for n in ['README.md','REPRODUCE.md']:
        dest=archive/('ROOT_'+n)
        if not dest.exists():shutil.copy2(ROOT/n,dest)
    (ROOT/'README.md').write_text(f'''# Quietmirror L2-r3 · INCOMPLETE 预发布

右手指握轻量化鼠标的机械试验版本。当前采用2026-10-18 r3方案，延续R3.2真实模型，保留六个顶孔、五脚平台和原主键/滚轮接口。新侧键是可拆载架上的两只杠杆键。

![实际CAD六视图](views/l2_r3/L2_r3_H_SIX_VIEWS_SHEET.png)

## 下载与查看

- [H完整装配 STEP](models/L2_r3/FULL_ASSEMBLY_H.step) / [FreeCAD装配](models/L2_r3/FULL_ASSEMBLY_H.FCStd)
- [D供体占位装配](models/L2_r3/FULL_ASSEMBLY_D_PLACEHOLDER.step)
- [单盘打印3MF](models/L2_r3/L2_r3_H_ALL_PARTS_SINGLE_PLATE.3mf) / [逐件STEP与STL](models/L2_r3/parts)
- [参数化源文件](cad/l2_r3) / [复现说明](REPRODUCE.md) / [版本发布页](https://github.com/Quietmirror/Quietmirror-L2/releases/tag/L2-r3)
- [当前方案原文](specs/Quietmirror_L2_r3_FINAL_Build_and_Release_2026-10-18.md) / [独立复核](handoff/l2_r3/SECOND_CHECK.md) / [干涉报告](handoff/l2_r3/INTERFERENCE_REPORT.md)

BODY包围盒约88.236×66.096×25.564mm；最高Z30.564、外缘最低Z5.0。沿用已有基准，没有根据近似AR手长再次等比放大。装配脚贴0.8mm时垫面Z4.4，BODY最高点离垫约26.164mm。

打印件CAD体积{total:.3f}mm³，PA12密度1.01时约{mass:.3f}g。真实PLA切片耗材{sliced.get('total_filament_g','UNVERIFIED')}g、时间{sliced.get('time','UNVERIFIED')}。支撑、填充和材料差异见[核算](handoff/l2_r3/FINAL_ACCOUNTING.md)。

## 验收状态

{table(['项目','状态','说明'],gates)}

本版仍需解决报告中的间隙/运动/侧键调节问题，三档刚度及实物功能未认证。H电子件是估计包络；D仍是用户所称ATK A1 Plus未确认供体。PAW3950不代表统一主板；1k无线、宏、LOD、充电和12h续航均未被CAD验证。

## 设计思路与试验

以连续指肚接触面和原有夹持带为外形约束，减重集中在原开放骨架、主键背面和滚轮。侧键隐藏传力筋与键帽曲面相接，压盘、止挡、卡舌和钢销分别承担触发、限位及定位；功能配合和一般避让间隙分开检查。

打印后记录握宽、顶掌、手指拖地、滚轮和侧键触达、抬鼠稳定性。装入钢销/微动后再评估按键动作，不用未通电塑料件代替真实点击与回弹试验。

## 历史和许可

[r2复核](handoff/l2_r2/README.md)、[r1复核](cad/l2_r1/README.md)、原cad/rebuild_r3_2和releases目录均保留。新CAD/文档延续本项目CERN-OHL-P-2.0；参考来源与署名见[NOTICE](NOTICE.md)。本版没有引入商业厂商CAD。
''',encoding='utf8')
    (ROOT/'REPRODUCE.md').write_text('''# L2-r3 复现

Python3.12、CadQuery2.8/OCP、NumPy、SciPy、Trimesh、VTK、Pillow、Gmsh4.15.2、FreeCAD1.1.4、PrusaSlicer2.9.6。Windows下设置PYTHONUTF8=1或使用python -X utf8执行脚本。工具链保存在本机_support，不上传二进制或缓存。更换路径时修改_support/enter-env.ps1与各工具路径。

依次运行：prepare_sources.py → side_module.py → build_body.py → remaining_parts.py → surface_mesh.py → electronics_assembly.py → additional_checks.py → validate.py → functional_checks.py → slice_plate.py → native.py（FreeCADCmd）→ render.py → trial_and_plate_views.py → mesh_metrics.py → run_staged_fem.py → write_report.py。每步检查退出码和报告。全部位于cad/l2_r3，重型任务使用4GiB Job限制、单线程及低优先级串行运行。Windows进程保护器随源码提供于cad/l2_r3/guard.py，只管理自己启动的子进程；系统可用内存低于512MiB时中止任务并记录原因。

bootstrap.py用于首次接入本机Downloads附件，不是新机器重放的必要步骤。源方案已保存specs。缺失作者r3参考文件已声明，不通过伪造目录绕过。

CAD构造在源码层取消旧座，原R3.2不变。原始CadQuery STL在少数BSpline接缝不封闭，surface_mesh.py从相同STEP曲面生成共边三角网格，并要求单连通/封闭/方向一致，未补洞。后续几何修改必须重新运行网格和检查。

native.py输出命名B-rep组件的可编辑FreeCAD文件，参数由Python/JSON控制；不是有完整草图历史和已解算装配约束的工程树。打印3MF不缩放，嵌入通用PLA配置，实际打印机需重新确认。

原R3.2输入来自固定基准提交和仓库保留文件。models/L2_r3/inputs/R32_BASELINE.FCStd保存原版命名B-rep；首次重放先用FreeCADCmd执行cad/l2_r3/restore_inputs.py，恢复缺失的exports/rebuild_r3_2/assembly/*.step，已存在文件不覆盖。FEM中间网格、求解日志及临时G-code留在_support/work，不进入发布仓库。

Python实际依赖版本见cad/l2_r3/requirements.txt。在项目根目录建立_support/venv并安装这些依赖，将Gmsh、FreeCAD、PrusaSlicer放到各脚本声明的_support/tools版本目录。先创建_support/work/l2_r3、reports/l2_r3、models/L2_r3/parts和reference目录；使用QUIETMIRROR_ROOT指向项目根目录。原母面参考已在exports/l2_r2_diagnostic/support_reference，旧参数和metadata保留于cad/rebuild_r2及reports/rebuild_r3_2。不要将bootstrap.py对本机Downloads的接入步骤当作必要依赖。

发布流程：prepare_model_bundle.py冻结模型和视图；write_report.py完成报告后，prepare_publication.py生成文本提交清单和全体文件校验表。GitHub工作流仅逐字校验并展开已测产物，不在CI里声称重新建模。l2-r3分支展开后经PR合并，main上的工作流创建INCOMPLETE预发布和附件。版本状态由本地实测报告确定，CI成功不等于机械验收通过。
''',encoding='utf8')
    print('Reports assembled from measured results; status INCOMPLETE',flush=True)
if __name__=='__main__':main()
