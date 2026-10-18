"""Publish the completed independent precheck, preserving failing findings."""
from pathlib import Path
import json, re, shutil, zipfile
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'reports/l2_r1';H=ROOT/'handoff';W=ROOT/'_support/work/independent'
def read(n):return json.loads((R/n).read_text(encoding='utf8'))
def write(p,t):p.write_text(t.strip()+'\n',encoding='utf8')

def main():
    k1=read('K1_volume.json');k7=read('K7_surface_coordinates.json');k8=read('K8_K10_arithmetic.json');k9=read('K9_document_layout.json');fem=read('K3_independent_R32_2.4.json');k5=read('K5_cavity_material_components.json');k6=read('K6_source_openings.json');beam=[read('K2_beam_2.4.json'),read('K2_beam_1.6.json')]
    table='\n'.join(f"| {r['name']} | {r['document_k_N_per_mm']:.2f} | {r['k_N_per_mm']:.5f} | {r['deviation_percent']:+.3f}% | {'数值在 ±3% 内' if abs(r['deviation_percent'])<=3 else '超出 ±3%'} |" for r in fem['results'])
    assert all(r['force_balance_passed'] and r['moment_balance_passed'] for r in fem['results'])
    write(H/'SECOND_CHECK.md',f'''
# L2 最终方案：独立复核

日期：2026-10-18。结论：**REVIEW_COMPLETE_WITH_REQUIRED_CORRECTIONS；未通过原文全部前置条件，整体交付仍为 INCOMPLETE。**

本轮落实用户“按新方案执行，先独立复核”的步骤。采用指定 R3.2 提交 `f1b1090931d717117287ea2b79c2e14ddc234937`；不改写现有 R3.3，也不把本次诊断件作为新鼠标发布。

所有检查脚本位于 [cad/l2_r1](../cad/l2_r1/)，仅调用 CAD、数值计算及求解器库；没有导入文档作者的几何/FEM 函数。基准尺寸和形状来自归档源代码、STEP 和 FCStd，保留原 [许可证](../LICENSE) 与 [署名](../NOTICE.md)。

## K1–K10

| 项目 | 文档值/要求 | 独立复核 | 偏差与结论 |
|---|---|---|---|
| K1 九个打印件体积 | 18506.6761 mm³，±0.5 | {k1['total_volume_mm3']:.6f} mm³；PA12 {k1['mass_pa12_g']:.6f} g | {k1['difference_mm3']:+.6f} mm³，通过。九件均为有效单一实体 |
| K2 解析梁 | 误差 <5%；作者报告 <1.5% | 2.4 / 1.6 mm 网格误差 {beam[0]['relative_error_percent']:.3f}% / {beam[1]['relative_error_percent']:.3f}% | 两档通过；两档均核查合力、力矩平衡 |
| K3 八个基线工况 | 与文档数值 ±3% | 八个均完成，2项在数值容差内，6项超出；见下表 | **不能标记原作者复现通过**：原文缺少若干载荷区、约束点及刚度定义。独立输入和结果可复现 |
| K4 Y54 横梁切断 | 约 X±11.5–13.5 | Y54/Z23 截线断口 X=±11.3–13.7；Y53/Z23 约±11.525–13.475 | BRep 确认切断；不能把近似坐标写成固定精确范围 |
| K5 依赖蒙皮的内构件 | Y67.5 横梁及中心枢纽，要求完整排查 | 按原始内腔边界去除蒙皮后，得到 {k5['count']} 个有效几何连通组 | 文档列举不完整；还包括四个主键固定铰座、后部传感器安装区等。原始 BODY 仍是一个有效实体，12组不表示原壳有12个悬浮件 |
| K6 孔洞来源 | O1/O2约26.0/16.7 mm³，O3未知，O4约2.1 | O1/O2/O4在六孔之外的附加切除为25.96049/16.69565/2.14302 mm³；O3为滚轮钢销通道 | 三处体积及位置一致；O3必须保留。见 [孔洞处理表](OPENINGS_RESOLUTION.md) |
| K7 外侧曲面X | 表中32个点，±0.05 | 直接与原始BSpline支撑面求交，最大误差 {max(abs(r['difference_mm']) for r in k7['rows']):.5f} mm | 32/32通过；不能据此证明键帽运动/装入可行 |
| K8 侧键杠杆 | 季长点力比1.74/1.75；偏心0 | 按键帽边缘量1/4长度：2.35955/2.33684；Y居中，但Z偏心−0.9 mm | 力比定义及“偏心”标注必须修正。转角6.56243°/6.20627°及末端行程1.29143/1.28649 mm与文档近似值相符 |
| K9 托架及障碍间隙 | 固定件/电子包络≥0.5 mm | 按列出的构件形成3个分离实体；后腿距底板1.104 mm；PCB到传感器耳0.200 mm；3处0.300 mm | **不通过**。后腿到脚贴支撑0.59120 mm通过；所有数值见 [K9 JSON](../reports/l2_r1/K9_document_layout.json) |
| K10 最终质量 | 约17.36 g；CAD实测替换 | 逐项预算−1319.3 mm³，得到17.35925 g | 预算算术通过；新增连接筋、圆角、安装件及最终整件尚未建成，最终CAD质量**待测** |

## K3 数值与证据范围

单位：N/mm。E=1500 MPa、ν=0.35；五脚Uz约束，另3个面内约束。实际网格84309节点、45780个C3D10实体单元；全部8步完成，合力及力矩平衡均通过。峰值作业内存约1.154 GiB。

| 工况 | 文档k | 独立k | 差异 | 比较 |
|---|---:|---:|---:|---|
{table}

独立刚度定义为 `k=F_norm²/(f·u)`；对向夹持 `F_norm=4 N`。载荷按二次三角形积分分配到中边节点。精确选面范围、约束节点与面积在 [K3输入](../reports/l2_r1/K3_inputs_2.4.json)，结果和力平衡在 [K3结果](../reports/l2_r1/K3_independent_R32_2.4.json)。文档未提供的选择已明确写在独立脚本内，不能视为与原作者完全相同的工况。

初次曲面投影的二次网格出现负雅可比，CalculiX退出201；没有使用失败结果。随后采用直边中节点二次单元并优化一次网格，完成计算。它近似真实曲面，后续最终壳体仍需网格收敛。本轮未重新计算文档缺失的P0/P1细网格数据，亦未宣称14.89 g在所有可能设计中均不可实现。

原始 `.geo/.inp/.dat/.sta`、Gmsh/CCX日志在 `_support/work/independent_fem/`。独立脚本可以重新生成，失败日志保留。解析梁采用线弹性理论对照，不是对该大位移梁的实体试验。

## 几何与硬件边界

- 五脚平台下表面均为 Z≈5.1999999 mm（CAD容差），极差小于1e−12 mm，确认名义Z5.2共面。
- K9诊断省略了尚未定义中心位置的底板减重窗和端子槽；删除这些材料不能使分离的支腿/止挡重新连接。702.749 mm³是该**未开完整窗口**诊断托架的体积，不能与640 mm³预算直接作最终误差判定。
- K5的12组来自“去除原始蒙皮后的材料”这个明确集合；每组包围盒和体积已保存，未将小组随意删除。主键铰座和滚轮铰座的受力必须纳入后续模型。
- 传感器继续为PAW3950目标；镜头基准距离、供体板形和孔位仍未实测。文档不能替用户将“ATK A1 Plus”改成F1 PRO；D方案保持待确认。
- 微动仍是估计包络。0.60总行程减0.05间隙，仅得到名义0.55 mm压下，不能单凭PT上限/OT下限证明每一颗实物的触发和止挡安全。

## 产物及下一步入口

- [参数修正记录](PARAMETERS_CORRECTED.md)：确认错误、可实施修正方向及仍待实测的参数。
- [孔洞处理表](OPENINGS_RESOLUTION.md)：逐项来源和保留/回填决策。
- [几何诊断STEP](document_side_layout_UNCORRECTED.step)：仅用于查看分离位置，不用于打印。
- [参数化复核数据](../cad/l2_r1/parameters_reviewed.json)。

![侧键托架诊断](../views/l2_r1/K9_side_carrier_diagnostic.png)

![横梁截面](../views/l2_r1/K4_cross_tie_sections.png)

本次完成独立复核阶段。正式鼠标几何、H/D装配版、最终STL/STEP/3MF、运动和装入检查、最终质量及S8刚度验收仍未完成，不能将本报告或诊断STEP标为最终可打印版。
''')
    openings='\n'.join(f"| {r['opening']} | {r['fastener']} | {r['additional_cut_outside_six_windows_mm3']:.5f} | 停止生成旧侧键M2工具通道，在保留六孔边界的前提下恢复母壳 |" for r in k6['openings'] if 'fastener' in r)
    write(H/'OPENINGS_RESOLUTION.md',f'''
# R3.2 孔洞来源与 L2 处理决定

独立依据：[K6数据](../reports/l2_r1/K6_source_openings.json)，[独立复核代码](../cad/l2_r1/independent_check.py)。检查对象为指定R3.2提交，不是R3.3。

| 编号 | 源特征 | 六孔之外附加切除 mm³ | 决定 |
|---|---|---:|---|
{openings}
| O3 | 滚轮载架钢销贯穿/装入通道，轴Y50/Z19、Ø2.35 | 不以回填体积判断 | **保留**，不得当外观残孔封住 |
| PH1 | 旧前侧键捕获销，XY=(26.99173,50)，Ø1.72 | 待最终母面重建 | 删除旧销后恢复母壳，保留新的杠杆铰链孔 |
| PH2 | 旧后侧键捕获销，XY=(27.70980,65)，Ø1.72 | 待最终母面重建 | 同上 |

O1/O2/O4的源代码链：`mechanics.py`侧键M2调用 → `fasteners.py:m2_set`的半径2.15、长度38的工具通道 → R3.2 `rebuild_body`应用切除。不是未经确认的“微动从顶部放入开口”。

O3由 `wheel_mechanism.py` 的 `cuts.append(cylinder(1.175,82.,(-41,py,wz),(1,0,0)))` 生成，并由 `mechanics.py` 的同轴 `pin_paths` 防止新增骨架重新堵孔。左右侧均存在相应功能通道。实际负X侧外边界约X−31.027…−29.998、Y48.825…51.175、Z17.825…20.175。

六孔本身保持R3.2定义。O1/O2/O4有部分区域与原六孔重叠；独立复核先从母皮切除中扣除六孔，才得到25.96049/16.69565/2.14302 mm³。不能把整根圆柱与母皮的交集全部回填，否则会缩小原六孔。

此表是已确定的建模决策；本阶段未改变原BODY。正式重建后需重新检查缝合、实体数、体积和网格，不宣称当前已经完成回填。
''')
    write(H/'PARAMETERS_CORRECTED.md','''
# L2 参数修正记录

状态：**PRECHECK_CORRECTIONS_RECORDED；正式模型待落实及重新验证。** 本文件不把修正建议伪装成通过的CAD。

| 问题 | 复核证据 | 后续采用的修正/约束 |
|---|---|---|
| 24GB进程上限大于本机内存 | 物理内存15.78GiB | 本机计算默认4GiB Job硬上限、单线程串行、低优先级；只影响本项目进程。工具复用D盘目录联接，缓存/日志位于新工作区 |
| K3不能完整复现原表 | 8工况实际求解，6项差异超3%；缺少精确载荷和刚度定义 | 保留原表与本次结果，不调低门槛、不把独立工况偷换成同一工况。后续比较必须使用一致选面、约束、刚度公式，并附收敛；原作者严格复现需补充输入/载荷定义 |
| 托架为3个实体 | 后腿离底板1.104mm，后止挡亦分离 | 增设前后腿至底板的连续桥，以及后止挡根部连接；保证正体积搭接及至少1.6mm承力厚度，计入质量，重新做底部装入和脚撑避让 |
| 前腿只在底板边缘很窄处接触 | 前腿最左X25.331，底板最右25.5 | 不能以“距离为0”当作充分承力连接。前桥从底板内延至支腿，避让Y<41.6的主键铰座；未建桥前不放行 |
| 开关/止挡及前开关/主键铰座为0.3mm | 三对BRep间隙0.300 | 目标≥0.5。初始修正：两开关向−X移0.20mm，前/后按钮尖X25.62/26.12；后挡墙同步向−X移0.20，避免产生新穿模。推杆长度由实际内表面和0.05间隙重算，不能只改开关 |
| 侧键板与传感器耳仅0.2mm | BRep距离0.200 | 初始修正：PCB下表面Z13.0→13.3、上表面18.5→18.8，保持板高；再验证端子、安装桥和电池。仍为估计包络 |
| 侧键板缺固定连接 | 板至后挡墙1.3mm，未给支撑 | 增加避开端子、传感器耳的局部安装座/连接桥，质量单独统计；不能让其悬空 |
| “四分之一键长”力比错误/定义不清 | 从键帽边缘量得到2.35955/2.33684 | 固定采用从靠铰链的键帽端部量1/4全长定义，并明确按压力位置；中点比1.0、缝端约0.465/0.466 |
| “偏心0”缺轴向限定 | Y位置在键面中点；Z17.5对16.6 | 标注Y偏心0、Z偏心−0.9mm，检查铰链弯矩/扭矩。暂保留原推杆高度，不能直接宣称无偏心 |
| 0.6行程与另一处7.1°/6.7°不一致 | 纯Y力臂给6.56243°/6.20627° | 按实际铰轴X、推杆X及刚体旋转求压下量，触发角和硬止挡角分别报告；钢销轴X/Z范围必须成为参数 |
| 微动PT/OT不足以确定安全止挡 | 名义压下0.55mm；实物自由点/动作点未知 | 用实际微动的FP/OP/TTP、公差和垫片校准；不把OT最小值误当所有实物共同最大允许量，不承诺真实点击/回弹 |
| O3被列作来源未知 | 确认为滚轮载架钢销通道 | 保留孔和钢销装入路径；只取消已废弃的侧键工具通道、捕获销孔 |
| K5只列两个内结构不完整 | 去蒙皮后12个几何连通组 | 额外保留/核查四个主键铰座及后部传感器安装区等；删除Y54梁不能连带删除中心滚轮支撑 |
| 原型圆孔与全局活动间隙混用 | Ø1.05孔/Ø1.0销仅径向0.025mm | 轴承配合必须列为单独功能配合并验证打印/铰孔工艺；普通运动表面继续≥0.2/FDM≥0.3，不能一概称全部满足 |
| 17.36g被误解为实测 | 预算精确和−1319.3mm³→17.35925g | 正式CAD逐件积分后替换。新增桥、PCB固定、加强圈和圆角都进入质量账，允许如实报告预算偏差 |
| 供体名称替换 | 用户原称ATK A1 Plus，实际板未确认 | 保留DONOR_ID_PENDING_USER_CONFIRMATION / PCB_GEOMETRY_UNVERIFIED / FIT_NOT_CERTIFIED；不采用附件声称的“用户已确认F1PRO”推断 |
| 缺真实镜头图纸却要求最终S5值 | 3.1mm为估计 | 保留±0.5调节设计；没有真实图纸/实测就标UNVERIFIED，不生成假装配尺寸 |
| Dremel机型和床尺寸 | 用户采用了方案中的255×155mm切片目标，但未实测打印机 | 后续使用该目标床尺寸生成真实切片，标注为配置假设，不声称实际设备已确认 |
| 原文“所有更轻设计都达不到” | 只提供有限候选及部分网格结果 | 改为“已列候选未证明达到目标”；不是全设计空间不可能性的证明 |

Omron依据：[D2F官方数据手册](https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2f.pdf)，针柱型PT≤0.5mm、OT≥0.25mm；仍需区分器件规格与壳体驱动行程。有限元工具链依据：[Gmsh手册](https://gmsh.info/doc/texinfo/)、[CalculiX 2.22手册](https://www.dhondt.de/ccx_2.22.pdf)。

这里记录了可推进的几何修正方向。尚未生成最终模型，尚未证明安装顺序、连续运动、S8刚度及实物装配全部通过。
''')
    params=dict(version='L2_R1_INDEPENDENT_REVIEW',baseline_commit='f1b1090931d717117287ea2b79c2e14ddc234937',units='mm',geometry_release=False,review_status='REVIEW_COMPLETE_WITH_REQUIRED_CORRECTIONS',final_acceptance=False,foot_plane_z=5.2,shell_nominal_thickness=1.8,roof_windows='R3.2 original six',document_budget_pa12_g=k8['budget_pa12_g'],side=dict(front=dict(y=[44.2,56.3],hinge_y=45,plunger_y=50.25,z=[15.5,19.5],plunger_z=16.6,suggested_switch_shift_x=-.2),rear=dict(y=[58.1,70.8],hinge_y=70,plunger_y=64.45,z=[15.5,19.5],plunger_z=16.6,suggested_switch_shift_x=-.2),minimum_electronic_clearance=.5,proposed_pcb_bounds=[15.2,16.2,44,70,13.3,18.8],requires_connected_carrier_bridges=True),donor='ATK A1 Plus as user named; unconfirmed; no substitution',hardware_fit_certified=False,author_fem_reproduction_passed=False)
    write(ROOT/'cad/l2_r1/parameters_reviewed.json',json.dumps(params,ensure_ascii=False,indent=2))
    shutil.copy2(W/'document_side_layout_UNCORRECTED.step',H/'document_side_layout_UNCORRECTED.step')
    write(ROOT/'cad/l2_r1/README.md','''
# L2 独立复核脚本

入口报告：../../handoff/SECOND_CHECK.md。所有脚本仅导入标准库及CAD/数值库，不导入旧建模或FEM检查函数。R3.2源文件仅用作数据与结构来源核对。

1. 从指定Git提交导出`cad`、相关reports、R3.1/R3.2 FCStd与STEP归档，按handoff/PROVENANCE.md设置工作区。
2. 执行 `_support/enter-env.ps1`，重型作业经 `_support/run_guarded.ps1`。
3. `independent_check.py restore`恢复72个独立组件；依次执行`baseline`、`arithmetic`、`surface`、`openings`、`connectivity`、`layout`。
4. `independent_fem.py beam_pair`校验工具链；`independent_fem.py body --size 2.4`生成并求解八工况，记录精确载荷选择与约束。2.0/1.6整壳收敛不是本次已完成项目。
5. `render_checks.py`生成实际CAD检查图；`write_review.py`整理报告和复核包。

窗口、载荷和基准几何数据保留R3.2出处。诊断STEP不是可打印成品；`parameters_reviewed.json`包含待落实的修正值，`geometry_release=false`。

依赖：Python 3.12、CadQuery 2.8、OCP、NumPy、SciPy、Matplotlib、VTK、Gmsh 4.15.2、CalculiX 2.22；使用项目已有D盘工具。本次不安装系统组件。
''')
    write(ROOT/'README.md','''
# Quietmirror L2 R1 — 独立复核阶段

已采用2026-10-17新方案并完成2026-10-18独立复核。状态：**REVIEW_COMPLETE_WITH_REQUIRED_CORRECTIONS / INCOMPLETE**。

先读 [SECOND_CHECK.md](handoff/SECOND_CHECK.md) 和 [PARAMETERS_CORRECTED.md](handoff/PARAMETERS_CORRECTED.md)。正式H/D装配模型、最终打印STL/3MF以及最终验收尚未生成。现有R3.3和原工程未覆盖。

本目录基于指定R3.2提交导出，并保存原有CERN-OHL-P-2.0许可证及NOTICE。工具通过D盘目录联接复用；新缓存、日志、报告在本目录。
''')
    included=[ROOT/'README.md',ROOT/'LICENSE',ROOT/'NOTICE.md']
    included+=list((ROOT/'cad/l2_r1').glob('*'))+list(R.glob('*.json'))+list((ROOT/'views/l2_r1').glob('*.png'))+list(H.glob('*.md'))+list(H.glob('*.step'))+list((ROOT/'specs').glob('*.md'))
    included += [ROOT/'_support/enter-env.ps1',ROOT/'_support/run_guarded.ps1',ROOT/'_support/guard.py']
    pack=H/'Quietmirror_L2_Independent_Review_2026-10-18.zip'
    included=[p for p in included if p.is_file() and p.name!='review_package_checks.json']
    links=[]
    for p in [ROOT/'README.md',H/'SECOND_CHECK.md',H/'PARAMETERS_CORRECTED.md',H/'OPENINGS_RESOLUTION.md',ROOT/'cad/l2_r1/README.md']:
        for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
            if '://' not in link:
                assert (p.parent/link).resolve().exists(),(p,link)
                links.append(link)
    checkfile=R/'review_package_checks.json'
    write(checkfile,json.dumps(dict(archive=str(pack),files=len(included)+1,relative_links_checked=len(links),relative_links_pass=True,fem_force_and_moment_balance_pass=True,original_project_modified=False,final_model_delivered=False,complete_review=True),indent=2))
    included.append(checkfile)
    with zipfile.ZipFile(pack,'w',zipfile.ZIP_DEFLATED) as z:
        for p in included:
            if p.is_file():z.write(p,p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(pack) as z:assert z.testzip() is None;count=len(z.namelist())
    assert count==len(included)
    print(pack,count,flush=True)
if __name__=='__main__':main()
