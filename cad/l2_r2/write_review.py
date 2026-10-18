"""Assemble the r2 independent-review handoff from measured JSON evidence."""
from pathlib import Path
import json,shutil

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'reports/l2_r2';HAND=ROOT/'handoff'
def read(n):return json.loads((OUT/n).read_text(encoding='utf8'))
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s.strip()+'\n',encoding='utf8')
def fmt(v,n=3):return f'{v:.{n}f}'

def main():
    k9=read('K9_r2_layout.json');contact=read('K9_r2_contact_audit.json');k8=read('K8_K10_r2_arithmetic.json')
    mesh=read('K3_mesh_summary.json');groups=read('K5_r2_disposition.json');datum=read('DATUM_and_stack.json')
    coarse=read('K3_r2_baseline_2.4.json');fine=read('K3_r2_baseline_1.6.json')
    summary=dict(plan='r2_2026-10-18',review_status='REVIEW_COMPLETE_WITH_REQUIRED_CORRECTIONS',
        final_delivery_status='INCOMPLETE',production_geometry_modified=False,
        baseline_commit='f1b1090931d717117287ea2b79c2e14ddc234937',
        K3=dict(pass_2p4=sum(x['within_document_3_percent'] for x in coarse['results']),
                pass_1p6=sum(x['within_document_3_percent'] for x in fine['results']),total=8,
                all_balance_passed=all(x['force_and_moment_balance'] for x in mesh['levels']),accepted=False),
        K5='12 groups classified; production deletion not performed',K6='source actions confirmed; production reconstruction pending',
        K8='arithmetic and definitions confirmed; actual pivot and switch response unverified',
        K9=dict(connected_valid_solid=True,all_clearances_passed=False,
                rear_leg_vs_retained_ear_overlap_mm3=contact['ears'][1]['leg_vs_ear_intersection_mm3']),
        K10=dict(budget_g=k8['budget_pa12_g'],final_measured_g=None),
        donor='ATK A1 Plus as named by user; DONOR_ID_PENDING_USER_CONFIRMATION / PCB_GEOMETRY_UNVERIFIED / FIT_NOT_CERTIFIED')
    write(OUT/'review_summary.json',json.dumps(summary,ensure_ascii=False,indent=2))
    parameters=dict(active_plan='specs/Quietmirror_L2_FINAL_Plan_2026-10-17.md',
        review_overlay='handoff/PARAMETERS_CORRECTED.md',units='mm N MPa',
        immutable_baseline='R3.2 f1b1090931d717117287ea2b79c2e14ddc234937',
        surface=dict(original_six_windows=True,skin_mm=1.8),
        reference_datums=dict(foot_glue_z=5.2,outer_edge_z=5.0,default_skate_thickness=.8,
            planar_ear_land_z=10.75,rounded_ear_arm_max_z=10.8,
            front_ear_center=[27.331028099073382,43.,9.5],rear_ear_center=[28.60429589691332,66.,9.5],
            rear_document_leg_y=66.8,adapter_thickness=None,adapter_top_z=None),
        side_switches=dict(SF=dict(bounds=[18.5,25,41.85,54.65,13.7,19.5],tip=[25.62,50.25,16.6]),
            SR=dict(bounds=[19,25.5,56.05,68.85,13.7,19.5],tip=[26.12,64.45,16.6])),
        side_pcb=dict(bounds=[15.2,16.2,44,70,13.3,18.8],terminal_layout=None,retention_layout=None),
        force_ratios=k8['keys'],carrier_diagnostic_assumptions=k9['assumptions'],
        required_corrections=['full-footprint ear contact instead of point height','route front bridge and collar around retained main hinge',
            'shape bridges and legs against actual inner-wall clearance','separate intended switch seating from extension clearance',
            'define rear-switch reaction support','solve adapter stack before screw length',
            'reconcile mesh and surface selectors before accepting FEM baseline'],
        final_print_release=False)
    write(ROOT/'cad/l2_r2/parameters_reviewed.json',json.dumps(parameters,ensure_ascii=False,indent=2))
    table='\n'.join(f"| {a['name']} | {a['document_k_N_per_mm']:.2f} / {a['k_N_per_mm']:.5f} | {a['deviation_percent']:+.3f}% | {b['document_k_N_per_mm']:.2f} / {b['k_N_per_mm']:.5f} | {b['deviation_percent']:+.3f}% |" for a,b in zip(coarse['results'],fine['results']))
    mesh_table='\n'.join(f"| {a['mesh_mm']:.1f} | {a['nodes']} | {a['elements']} | {a['mesh_volume_mm3']:.3f} | {a['mesh_volume_vs_BRep_percent']:+.3f}% |" for a in mesh['levels'])
    max_step=max(abs(v) for v in mesh['changes'][-1]['k_change_percent'])
    gtable='\n'.join(f"| {r['id']} | {r['name']} | {r['volume_mm3']:.5f} | {r['action']} |" for r in groups['parts'])
    ctable='\n'.join(f"| {' ↔ '.join(r['pair'])} | {r['distance_mm']:.5f} | {r['intersection_mm3']:.6f} | {'通过' if r['passed'] else '不通过'} |" for r in k9['pairs'] if r['kind']=='clearance')
    text=f'''
# Quietmirror L2 r2：独立复核

日期：2026-10-18。**r2 已替代现行方案；本轮复核完成，但全部前置条件未通过，最终模型状态仍为 INCOMPLETE。**

执行范围是用户确认的“替代现有方案，继续独立复核修正项”。当前[方案原文](../specs/Quietmirror_L2_FINAL_Plan_2026-10-17.md)保留附件内容，已确认的错误和实施约束写入[修正记录](PARAMETERS_CORRECTED.md)，不将原文结论当成复核证据。r1 方案、诊断件、报告、旧压缩包和 R3.2/R3.3 均保留。本轮没有修改生产 BODY 或既有装配文件。

复核只读指定 R3.2 STEP、元数据和源码；几何与 FEM 程序没有导入方案作者的生成/求解函数。复用的是上轮由本项目独立写出的解析、求解器输入和结果读取代码。源代码见 [cad/l2_r2](../cad/l2_r2/)，保留原[许可证](../LICENSE)和[署名](../NOTICE.md)。

## K1–K10

| 项目 | 本文值 / 目标 | 复核值 / 偏差 | 结论 |
|---|---|---|---|
| K1 九件体积 | 18506.678 mm³，±0.5 | 引用 r1：18506.678218；差 +0.000218 | 通过，基准未改 |
| K2 解析梁 | 误差 <5% | 引用同一独立求解链 r1：−1.471% / −1.375% | 通过；不是实物试验 |
| K3 八个基线 | 2.4 / 1.6 mm 与原表 ±3% | 2.4 mm {summary['K3']['pass_2p4']}/8；1.6 mm {summary['K3']['pass_1p6']}/8 在容差内 | **未通过复现门槛**；三档均实际求解，力/力矩平衡通过 |
| K4 Y54 断口 | X≈±11.3–13.7 | 引用 r1 的 BRep 截线 | 已确认；仅删除外臂，保留滚轮枢纽 |
| K5 内部组 | 每组说明保留/删除/加强 | 重新分解 12 组；逐组处理见下 | 分类完成；未把小组误当悬浮件删除 |
| K6 开口 | O1/O2/O4 回填，O3 保留，PH1/PH2 更新 | 与 r1 来源证据一致；O1/O2/O4=25.96049/16.69565/2.14302 mm³ | 修订正确；源码层重建后的验收待做 |
| K7 母面 X | ±0.05 | 引用 r1 32点，最大0.01992 | 通过 |
| K8 力比/偏心/转角 | 距铰点 L/4；Y0/Z−0.9 | SF 1.73554、SR 1.74803；6.56243°/6.20627° | 算术和定义通过；实际触发/止挡未证实 |
| K9 单实体、接触、间隙 | 1实体；固定非接触处≥0.5 | 托架1个有效实体；仍有桥/壁/铰座冲突；后腿嵌入保留 PCB 耳 {contact['ears'][1]['leg_vs_ear_intersection_mm3']:.6f} mm³ | **不通过**，见下 |
| K10 质量 | 17.42 g预算，最终以CAD实测 | 合计−1254.3 mm³ → {k8['budget_pa12_g']:.6f} g | 算术通过；最终整鼠CAD质量待测 |

引用证据：[r1 体积](../reports/l2_r1/K1_volume.json)、[梁2.4](../reports/l2_r1/K2_beam_2.4.json)、[梁1.6](../reports/l2_r1/K2_beam_1.6.json)、[横梁截面](../reports/l2_r1/K4_K5_cross_tie_sections.json)、[孔来源](../reports/l2_r1/K6_source_openings.json)。这些均对应不变的 R3.2，不能移作未来 L2 验收。

## K3：按 r2 选面重新计算

单位 N/mm；每格为“文档 / 复核”。E=1500 MPa，ν=0.35；五脚 Uz 和三个面内约束，夹持等效合力 F=4 N，k=F²/(f·u)。主键根区已改为 Y35–42 / X6–24 及镜像；不再沿用 r1 较小载荷区。载荷、选面面积/中心和约束点均写入 JSON。

| 工况 | 2.4 mm k | 差异 | 1.6 mm k | 差异 |
|---|---:|---:|---:|---:|
{table}

| 网格 mm | 节点 | C3D10 单元 | 网格积分体积 mm³ | 对 BRep 的体积差 |
|---:|---:|---:|---:|---:|
{mesh_table}

最近两档刚度最大变化为 **{max_step:.3f}%**，最细独立网格体积仍比BRep小约1.99%，所以曲面近似与局部收敛问题尚未消除。**这些结果不足以断定作者原表算错**。具体各工况见 [网格摘要](../reports/l2_r2/K3_mesh_summary.json)。这是未改 R3.2 的复现和敏感性检查，没有求解最终 L2，也没有重新构造 P0/P1/P7。不能将其解释为“最终 L2 不够强”或“所有轻量化方案不可行”。

还没有取得方案引用的 `fem3d/fem_variants.py`、`l2_repo_scan/`、作者原网格和求解输入。文档给出的 1.6 mm 基线有307796节点，独立同名网格实际{fine['results'][0]['nodes']}节点，故“同为1.6 mm”不等于同一离散化。使用直中边 C3D10 避开上轮曲面二次网格负雅可比；其均布牵引在仿射三角面上等价于二次形函数积分（角节点权重0，中边各A/3）。屋顶选面用明确的竖向残差<0.35，侧壁用超椭圆水平残差<0.35；后者不能冒充精确母面法向距离。应把作者的具体选面与网格配置补成可重放输入，或在统一、已收敛的独立流程下重新建立基线，不能靠改材料模量或挑载荷区凑数。

每档8工况均成功结束且平衡通过。原始 `.geo/.inp/.dat/.sta` 和求解日志保存在 `_support/work/fem_r2/`；程序、完整数值摘要和守护日志随本轮交付。内存上限4 GiB、单线程、串行；未修改系统设置。

![基线复算](../views/l2_r2/R2_FEM_baseline_comparison.png)

## K5：12个内部连通组逐组处置

集合定义为“原 BODY 与独立复原的母壳内腔相交”。**12组是去除蒙皮后的几何区域，原始 BODY 本身仍是一个实体。**

| 组 | 几何名称 | mm³ | 处理 |
|---:|---|---:|---|
{gtable}

第1组同时含要保留的脚贴、底筋、接口与要删除的旧侧键座，不能整组删除。第2组只能取消 Y54 外臂的生成，保留 X±6/Y47–55 的滚轮枢纽和钢销通路。第9–12组与按原参数独立构造的后中脚/支撑参考几何的交集占比均约100%，应保留；不应以体积小为由清除。所有组的包围盒、有效性和重合比例见 [K5 JSON](../reports/l2_r2/K5_r2_disposition.json)。最终变更后的单实体和网格仍需重验。

## K9：连接恢复，但装配门槛尚未通过

r2只给出了连接桥的截面和范围，未给定完整轮廓。本轮明确采用“桥以支腿Y为中心、宽4、厚1.6”，另加下包0.3的连接环与两个PCB座，作为可复查的具体展开；它是一个**可复现的反例，不表示所有满足r2文字的桥都必然冲突**。原文明确给定的腿径、中心、削平面和Z范围另行独立核对。

导出的托架重新导入后为 **1个有效BRep实体**；10处连接均有正体积搭接。外延、桥、连接环、PCB座的净增量为{k9['added_connection_volume_mm3']:.3f} mm³，接近+65预算。未开完整窗/端子槽的诊断托架为{k9['parts'][0]['volume_mm3']:.3f} mm³，**不能作为最终质量**。

| 对象 | 最小间隙 mm | 相交 mm³ | 对0.5门槛 |
|---|---:|---:|---|
{ctable}

低侧壁参考是原母壳的 Z9–14.5 部分，符合本版低夹持带连续封闭的要求；不是把已删除旧座误算为侧壁。整托架与该参考相交约{contact['pairs'][-1]['intersection_mm3']:.6f} mm³。整托架与未删除旧座的R3.2相交52.2284 mm³、PCB相交5.1062 mm³仅作环境提示，**不作为新L2的最终穿模结论**。

新增详细检查：前腿、前下包连接环到原主键铰座也不足0.5；后微动与后挡墙仍相隔0.5，需定义反力支撑，不能用未定的焊脚刚度替代。微动坐底和PCB座接触没有实体穿模，但应列入有意接触清单；原文“全部外延离微动≥0.5”与当前底面连接做法不能同时按字面验收。

![托架诊断](../views/l2_r2/R2_carrier_layout.png)

![干涉位置](../views/l2_r2/R2_clearance_failures.png)

### 安装耳：不能用一个点的高度定义整面贴合

独立按归档源码重新构造了通用PCB耳，并与实际 BODY 求交：两只参考耳在 BODY 之外的体积均为0。源码是7.6×7.6×2.5盒体、中心Z9.5，加半径1.3的圆弧连接筋；因此平面承台为 **Z10.75**，筋冠最高 **Z10.80**。后耳中心Y66.0，而r2后腿中心Y66.8，必须区分。

- 前腿底面Z10.80：无实体穿模，但只触及圆弧筋最高处，其余平面名义悬空0.05；不是整面承压。
- 后腿底面Z10.525：扣除本轮名义Ø2.4通孔后，仍与保留的PCB耳相交 **{contact['ears'][1]['leg_vs_ear_intersection_mm3']:.6f} mm³**，超出0.001门槛。这一材料不是应删除的旧侧键座。
- 仅把两腿都抬到Z10.80可消除这类高度侵入，但仍不能证明承压面积和预紧合格。应定义贴合耳平面的支承/带让位凹面的转接件，保留旧PCB耳，再检查完整底面与螺栓受力。
- 腿高应按 `12.1 − 实际转接件顶面Z` 计算。若在10.80上叠1.6厚转接件，顶部12.40，已高于底板下表面12.10达0.30；不能只写“M2加长1.6”就算叠装闭合。连腿正高度也要求该叠装厚度<1.30，合理承力厚度还会收紧这个范围。

![安装耳截面](../views/l2_r2/R2_ear_contact_sections.png)

详细证据：[完整底面接触](../reports/l2_r2/K9_r2_contact_audit.json)、[原始局部面探测](../reports/l2_r2/DATUM_and_stack.json)。后者保留文档名义高度以便对照，不代表这些高度已被采纳为正确安装面。

## K8、底面与质量边界

“距铰点L/4”的SF/SR力比为1.735537/1.748031；若从靠铰链的键帽边缘量L/4，则为2.359551/2.336842。Y偏心为0，Z偏心为−0.9。刚体绕竖轴转动的内移量含 `dx·(1−cosθ)+|dy|·sin|θ|`，纯Y估计只在dx=0时严格成立；实际铰轴X/Z、推杆X及微动FP/OP/TTP未定，不能输出实物触发角。5 N反力与0.9 mm的Z偏心对应4.5 N·mm横向弯矩，后续S7须计入，不能只核算平面杠杆比。

实际外缘朝下平面为Z5.0，面积{datum['total_edge_area_mm2']:.6f} mm²。五脚粘贴面继续Z5.2；默认0.8脚贴对应地面Z4.4，外缘净空0.6，算术通过。要求外缘净空≥0.5意味着脚贴厚度≥0.7。镜头光学高度仍须绑定真实镜头基准和脚贴，3.1只是估计。

预算合计为−1254.3 mm³（文档−1255是取整），PA12 ρ=0.00101 g/mm³，约17.424902 g。它不包含已验证的最终窗槽、支承和所有修正体积，不能标注成品重量或切片估重。

本轮不确认电子实物兼容性：H方案是PAW3950目标；D方案保持用户最初命名“ATK A1 Plus”待确认，不采纳附件“用户原写A1 Pro”的历史描述，不替换成F1 PRO。宏、无线1K、DPI、LOD和12小时续航仍属于主板/固件/接收器/电池的后续功能验证。

## 下一阶段入口

先落实[参数修正记录](PARAMETERS_CORRECTED.md)，再做生产几何。正式H/D模型、微动与钢销装入、全行程运动、最终材料/切片质量、S1–S9和最终打印文件仍未完成。本轮完成的是独立复核，不把诊断STEP标为最终可打印鼠标。
'''
    corrections='''
# L2 r2 参数修正记录

状态：**前置复核完成，必须处理以下问题才能进入正式模型验收。** 当前附件原文存档不改写；本表是r2的独立复核补充。

| 编号 | 已确认问题 | 修正 / 后续验收条件 |
|---|---|---|
| C1 | r2后腿Z10.525侵入原PCB耳；前腿10.80只触圆弧筋 | 原平面承台Z10.75、筋冠Z10.80。按完整支承底面设计带让位的转接座；禁止把局部射线高度叫做整面高度。后耳中心Y66.0与腿中心66.8分别参数化。不得删原PCB耳消除冲突 |
| C2 | H转接件未闭合；1.6厚叠装顶面高过底板 | 定义z_adapter_top，再由h_leg=12.1−z_adapter_top求腿高。若用10.80基准，t_H<1.30仅保证正高度；承力、螺钉头/垫片/啮合长度另算。若超出，应改变托架标高或叠装路径，随后重验微动与键帽 |
| C3 | 前桥、腿和下包环都未满足主键铰座间隙 | 用完整铰座而不是只有Y<41.6的圆柱前缘作禁入体。腿/桥/环完整包络离保留铰座≥0.5；重布桥的Y轮廓和安装支点，保证连续承力与M2孔周材料。当前诊断没有给出已通过的新轮廓 |
| C4 | 原削平X29.0/30.1不足以避开侧壁；两桥穿壁 | 用实际内壁的0.5净空约束定桥/腿轮廓，不能只用母壳外表面或恒定X截断。外侧孔周剩余材料很窄，继续削平可能开破M2孔；应同时重新安排支点/转接，不可只硬切薄 |
| C5 | 底板外延与微动0.2/0.0，与“均≥0.5”冲突 | 把有意坐底接触面明确列入允许表，非支承侧面仍≥0.5；若坚持外延全部≥0.5，需阶梯让位并保持正体积连接及规定厚度。不能把未列明的接触静默忽略 |
| C6 | SR微动距统一后挡墙0.5 | 为后微动单独定义与反力方向对应的承压台或台阶、端子槽和定位方式；不得假定未知PCB焊脚即可承受按压力。新增部件不得侵入SF、隔板或PCB |
| C7 | K3两档原表容差未全部通过；独立三档也存在网格敏感性 | 保留所有数值。补齐作者网格、选面函数和输入，或以统一且收敛的独立流程重建R32/P0及最终L2基线；不能通过调整E或挑选载荷区逼近原表 |
| C8 | K8算术已清楚，但实际转动和开关触发行程未定 | 保留Y0/Z−0.9；以实际铰轴X/Z和推杆X求刚体运动、止挡、触发及超程，FP/OP/TTP未测时标UNVERIFIED。钢销配合单列，不套用普通0.5净空 |
| C9 | §2.1要求源码撤销旧刀具，§3.1又写外扩补片 | 选择源码层取消O1/O2/O4和PH1/PH2刀具；六孔边界、O3滚轮销通路保持。生产重建后验单实体、六孔边界、通道、网格及体积，不在成品BODY盲补 |
| C10 | r2文字把供体原名写成A1 Pro，输出目录仍l2_r1 | 供体历史按用户原消息ATK A1 Plus保留，实际型号未确认。新复核资产统一l2_r2目录，保留l2_r1。17.424902 g只作预算，最终由逐件CAD/切片替换 |

已确认可以沿用：六孔及1.8蒙皮；K5逐组保留关系；O3通路保留；K8新的力比定义；微动移−X后的0.5关键间隙；PCB上移后的0.5传感器耳间隙；0.8脚贴对应0.6外缘离地。单一连通托架已能构成，但上述装配问题未因此自动解决。

参数数据：[parameters_reviewed.json](../cad/l2_r2/parameters_reviewed.json)。诊断桥、环、PCB座位置是公开假设，不是已批准的生产尺寸。生产BODY和原接口本轮均未更改。
'''
    opening='''
# L2 r2 开口处置复核

r2对O1/O2/O4、O3、PH1/PH2的来源与上轮独立证据一致。本轮没有执行生产BODY回填，不能把下表“决定”当成已经完成的几何修改。

| 项 | 证据 / 决定 |
|---|---|
| O1 | 旧侧键M2工具通道；六孔外25.960494 mm³；源码取消该刀具 |
| O2 | 同类旧工具通道；六孔外16.695654 mm³；源码取消 |
| O4 | 第三处旧工具通道；六孔外2.143018 mm³；源码取消 |
| O3 | 轴线Y50/Z19、Ø2.35的滚轮钢销装入通道；保留贯通 |
| PH1 | 旧捕获销Ø1.72孔，中心(26.99173,50)；取消旧刀具 |
| PH2 | 旧捕获销Ø1.72孔，中心(27.70980,65)；取消旧刀具 |

O1/O2/O4三处仅六孔以外附加切除合计44.799166 mm³；不是“两个开口”，也不包含所有新侧键开口、夹持带回填和销孔的净变化。六孔边界不得缩小。

§2.1源码取消与§3.1外扩补片措辞不一致，本轮采用前者作为后续重建路径。最终验收：BODY单实体、无无效几何、六孔与基准相同、O3路径可达、体网格成功、全部回填与切除的净体积入账。当前这些最终项均PENDING。

证据：[K6 r2](../reports/l2_r2/K6_r2_crosscheck.json)、[r1源文件定位](../reports/l2_r1/K6_source_openings.json)。
'''
    provenance='''
# L2 r2 来源与修改范围

- 用户2026-10-18确认“替代现有方案，继续独立复核修正项”。新附件已设为specs中的现行方案；r1方案在specs/archive，r1复核原文在handoff/archive/l2_r1。
- 唯一生产几何基准仍为Quietmirror/github提交f1b1090931d717117287ea2b79c2e14ddc234937的R3.2。原D盘工程及R3.3保留。
- r2新文件位于cad/l2_r2、reports/l2_r2、views/l2_r2、exports/l2_r2_diagnostic及handoff/l2_r2。根README和handoff现行入口已切换到r2。
- 新几何为独立复核诊断。没有更改原BODY、接口、脚贴或历史装配模型；没有生成最终L2 STL/3MF。
- 本轮仅读源文件/STEP，独立建立BRep与FEM输入；复用上轮本项目独立程序，不导入方案作者脚本函数。保留LICENSE、NOTICE。
- FEM：Gmsh4.15.2，CalculiX2.22，C3D10直中边，E1500MPa/nu0.35；自适应BRep体积。所有新重型进程4GiB Job上限、单线程、串行，原始计算及日志在_support。
- 方案中引用的作者fem3d/fem_variants.py、扫描复核目录和扫描报告未提供；附件的P0/P1/P7结论没有被本轮重新验证。
- 供体按用户原始名称ATK A1 Plus标待确认；没有替换型号，也没有使用未经实测的主板孔位。
'''
    for name,content in [('SECOND_CHECK.md',text),('PARAMETERS_CORRECTED.md',corrections),('OPENINGS_RESOLUTION.md',opening),('PROVENANCE.md',provenance)]:
        write(HAND/name,content)
        # Versioned snapshot keeps working relative links into the same project.
        write(HAND/'l2_r2'/name,content.replace('(../','(../../'))
    write(ROOT/'README.md','''
# Quietmirror L2 r2 — 独立复核

2026-10-18：r2方案已替代现行方案，独立复核完成。**REVIEW_COMPLETE_WITH_REQUIRED_CORRECTIONS / 最终模型INCOMPLETE。**

[详细复核](handoff/SECOND_CHECK.md) · [参数修正](handoff/PARAMETERS_CORRECTED.md) · [现行方案](specs/Quietmirror_L2_FINAL_Plan_2026-10-17.md) · [版本化r2交付](handoff/l2_r2/) · [r1存档](handoff/archive/l2_r1/)

[r2复核包ZIP](handoff/Quietmirror_L2_R2_Independent_Review_2026-10-18.zip)包含诊断STEP、报告、源码、母面参考和本轮使用的原R3.2 BODY输入。[复现步骤与依赖](REPRODUCE.md)说明如何运行。包内不含最终L2打印模型或求解器二进制。

托架已能构成一个有效实体，微动与PCB的部分间隙修正有效；桥/侧壁/主键铰座、后腿与原PCB耳接触仍不通过。R3.2基线已按r2选面用2.4/2.0/1.6三档独立复算，原表±3%容差未全部通过。原六孔、基准BODY、功能接口和历史版本保留。

本轮目录`exports/l2_r2_diagnostic`是诊断STEP，不是可打印最终鼠标；`cad/l2_r2`提供复核程序，`reports/l2_r2`提供数据，`views/l2_r2`提供实际几何视图。正式H/D装配、最终STL/3MF、S1–S9和切片质量尚未完成。

![托架诊断](views/l2_r2/R2_carrier_layout.png)

基准为Quietmirror/github@f1b1090931d717117287ea2b79c2e14ddc234937的R3.2；保留[CERN-OHL-P-2.0许可证](LICENSE)和[署名](NOTICE.md)。

历史输入：[R3.2 FreeCAD](releases/Fenrir-MiniSE-R3.2/FENRIR_MINISE_R3_2.FCStd) · [R3.1 FreeCAD](releases/Fenrir-MiniSE-R3.1/FENRIR_MINISE_R3_1.FCStd) · [r1完整发布快照](https://github.com/Quietmirror/Quietmirror-L2/tree/67dc936d1928946b9713bc3418b2bda9325b9aa6) · [原项目与R3.3](https://github.com/Quietmirror/github)。这些历史输入没有被本轮诊断件替换。
''')
    write(ROOT/'cad/l2_r2/README.md','''
# r2独立复核重放

工程根目录D:\\Quietmirror_L2。每次先进行PowerShell点加载：`. D:\\Quietmirror_L2\\_support\\enter-env.ps1`。重型进程统一通过`_support/run_guarded.ps1`，MemoryGiB=4，串行，不同时开多个求解/建模任务。

顺序：

1. `geometry_recheck.py`：按r2建立诊断托架、间隙表、12组处置及算术。依赖原始R3.2文件及r1独立复原母面。
2. `contact_recheck.py`：独立复原PCB耳、与实际BODY核对完整底面接触。
3. `fem_recheck.py --size 2.4`、`--size 2.0`、`--size 1.6`分别串行运行。它只复用cad/l2_r1/independent_fem.py的独立网格/求解工具；不导入原作者的FEM函数。
4. `summarize_fem.py`：网格体积、刚度趋势、平衡摘要。
5. `render_review.py`：从诊断STEP和实测JSON绘图。
6. `write_review.py`：生成现行和版本化报告。

示例：
```powershell
. D:\\Quietmirror_L2\\_support\\enter-env.ps1
& D:\\Quietmirror_L2\\_support\\run_guarded.ps1 -Executable $CadPython -Arguments @('D:\\Quietmirror_L2\\cad\\l2_r2\\geometry_recheck.py') -Log 'D:\\Quietmirror_L2\\_support\\logs\\l2_r2_geometry.log' -MemoryGiB 4 -TimeoutSeconds 1800
```

`adopt_plan.py`是本次方案接入记录，通常不需要再次执行。原始附件r1保留于specs/archive，新附件原文在specs；parameters_reviewed.json和handoff/PARAMETERS_CORRECTED.md记录已核实的修正/约束。没有最终生产尺寸或已验证的实物配合。

若换机器，先配置CadQuery/OCP、NumPy、SciPy、VTK、Matplotlib、Gmsh和CalculiX。r1的独立_check.py生成母面参考（也在r2交付support_reference中提供），完整生产基准和依赖由同仓库保留。不要修改源码路径以指向旧工作树的未提交模型。
''')
    for p in (ROOT/'_support/logs').glob('l2_r2_*.guard.json'):
        shutil.copy2(p,OUT/p.name)
    print('r2 reports written; final geometry remains INCOMPLETE',flush=True)

if __name__=='__main__':main()
