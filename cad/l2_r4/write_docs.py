"""Publish Chinese handoff text from measured reports without inventing passes."""
import json
from pathlib import Path
from gate_accounting import assess,HARDWARE_PENDING
ROOT=Path(__file__).resolve().parents[2];RP=ROOT/'reports/l2_r4';OUT=ROOT/'handoff/l2_r4';MODELS=ROOT/'models/L2_r4'
def read(n,default=None):
    p=RP/n;return json.loads(p.read_text(encoding='utf8')) if p.exists() else ({} if default is None else default)
def write(name,text):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf8')
def fmt(x,d=3):return '未取得' if x is None else f'{float(x):.{d}f}'
def table(headers,rows):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(str(v) for v in r)+' |\n' for r in rows)+'\n'
def main():
    a=assess();OUT.mkdir(exist_ok=True);state=a['status'];mass=read('CAD_mass.json');sl=read('slice_summary.json');act=read('side_actuation_force_and_tuning.json');g8=read('fem/G8.json');s7=read('fem/S7.json');inv=read('assembly_inventory.json');routes=read('assembly_routes_final.json').get('sequence',[])
    pending='\n'.join(f'{i+1}. {p}' for i,p in enumerate(HARDWARE_PENDING))
    cell_revision=read('battery_envelope_revision.json')
    cell_dimensions=cell_revision.get('selection',{}).get('dimensions_mm',[18,22,6])
    cell_size_text='×'.join(str(v) for v in cell_dimensions)
    common='单位为 mm；+X 为拇指侧，−Y 为前端，+Z 向上。脚贴粘贴面 Z=5.2，估计脚贴厚度0.8，鼠标垫平面 Z=4.4。\n\n'
    design=f'''# Quietmirror L2-r4 设计说明\n\n当前门槛结论：**{state}**。最终是否可发布以 [GATES.md](GATES.md) 和 [FINAL_ACCOUNTING.json](FINAL_ACCOUNTING.json) 的实际结果为准。\n\n{common}
## 目标与保留项

延续 R3.2 的紧凑指握外形、原六个三角窗口、底部外轮廓与五个共面圆点脚贴。侧键是右手拇指侧的例外；主键外露宽度与已定长度不再扩大。主键前缘开放，触感面与外壳线条连贯。内部中键端子孔的局部修正另列，历史版本和许可证均保留。

手长230mm、张开跨度190mm只是原始照片AR近似值；跨度不是掌宽，模型没有按手长等比放大。当前外形来自已有R3.2工程，不将90×62×31mm的早期试握假设冒充当前成品尺寸。当前逐件包围尺寸见 [solids.json](../../reports/l2_r4/solids.json)；装配后全机尺寸见六视图。

## 托架与刚度

旧独立侧键托架的整块装入路径被框架阻挡。r4在生成BODY的源码步骤中建立一体底板、局部腹板和挡柱，再将开关背挡拆成SF_RETAINER、SR_RETAINER。新增Ø2下横梁、两根Ø2.4铰座竖撑，原Y67.5横梁改为r1.5。所有新增件都通过母面裁切，不随意改变外部握持曲线。

实际复核还发现作者坐标中的隐藏铰耳露出母面、原螺钉孔边距不足、螺丝刀通道冲突和插装线路遗漏了已装开关端子。每项修正及失败结果保留在 [TUNING_LOG.md](TUNING_LOG.md)。作者参考几何用于对照，最终打印BODY始终来自可编辑生成源码。

载架沿用C18修正：在Y34.2..36.2局部将底面从Z10.4抬至10.6，保持Z12.2上座面与1.60mm名义厚度。该轮改动解决+4.4°点击姿态对固定支座的0.22743mm非功能间隙不足；当轮复测为0.41763mm，只减去2.47974mm³材料。轮轴和板上座面未移动，最终完整角度复核仍以当前G5数据为准。

C19在源码生成中键托架时，削平伸入微动外壳角部的横梁球形端帽；原始相交体积为0.006686mm³，高于0.001mm³判据。三处中键端子孔从1.2×2.0扩大到1.8×2.7，解决原0.25mm非功能间隙不足。微动本体、螺栓轴线和压杆高度没有通过移动来规避干涉。该改动包含底部内侧的端子孔，因此仅声明经差分核对的五脚局部区域、Z≤5.1低位区域和底部外轮廓保留，不把整个底部称为逐点未改。修正量与局部接触核对见 [BODY_C19.json](../../reports/l2_r4/BODY_C19.json)，其余门槛均绑定重建后的BODY重验。

打印件最终体积为{fmt(mass.get('total_volume_mm3'))}mm³，相比附件约17684mm³参考值差{fmt((mass.get('total_volume_mm3') or 0)-17684)}mm³（{((mass.get('total_volume_mm3') or 0)/17684-1)*100:+.3f}%）。差异来自铰耳隐藏、挡板端子槽、侧键连接筋及载架让位等已记录修正；附件参考量本身是近似值。不能把此差异当作实际整机减重。

## 侧键动作

键帽取消远端卡舌，沿−X直线装入。实际铰轴X=27.5，前后Y=45.3/69.7；这是使钢销和铰耳完全藏入现有母面的明确修正。竖直钢销Ø1×5.5，打印参考孔Ø1.05。压盘Ø2.6，内部有独立的外向止动耳和向内行程挡柱。C7调整内部铰节和止动耳高度；后续实测又要求小幅缩短触感面边缘、抬高下缘并增加内侧挡柱让位。最终侧键尺寸由side_module.py参数和实际模型报告确定，不能把早期未通过的外形写成保留不变。

静止状态的轻微余量靠实测PET加胶总厚度调整；模型使用0.33mm名义膜片，提供0–0.70mm调整目标。0.01mm步进只是厚度选择计算，不代表FDM打印精度，也不代表任意胶层能达到该厚度。按钮、压盘和壳体的精确离散检查与整件原始相交结果同时保存。

## 电子布局与接口

H为半组装PAW3950的估计包络：传感器板、封装及镜头、RF/MCU板、天线净空、电池及插头、USB-C板、开关、滚轮编码器及其转接板、侧键焊线各自独立。不能把PAW3950型号当成主板统一尺寸，也不能从板框推断固件或接收器功能。目标是400–6400DPI、无线1000Hz、宏、LOD、两侧键、滚轮中键、开关、USB-C充电、无sync技术和持续12h工作。

D仍指用户称为“ATK A1 Plus”的待确认供体。未擅自换成其他ATK型号。D_MAX_BOARD_ENVELOPE是指定板层高度、板厚和净空下的保守连续可用区；孔位域表示允许布孔的区域，不是真实主板钻孔数据。它不能证明未知供体能直接装入；微动、编码器、传感器位置不匹配时需要转接结构或改变布局。

12h续航按容量≥12×平均电流/可用比例估算。可用比例0.75时，10/15/20/25mA分别要求160/240/320/400mAh；当前{cell_size_text}mm电池包络不等于任何已验证容量。原18×22×6mm估计包络在已尝试搜索中未得到合格拆装路线，因此备选包络必须单独通过静态、全姿态拆装和最终电子检查。历史电池参数保留，所选尺寸、体积变化和来源写在 [battery_envelope_revision.json](../../reports/l2_r4/battery_envelope_revision.json)。19×23×7mm原服务预留区和原插头位置继续保留。光学轴线垂直鼠标垫；镜头底面几何高度不等于真实焦平面高度。

## 数据范围与开源来源

当前包含{inv.get('independent_components','未取得')}个独立组件、9个打印件。可编辑源为 [cad/l2_r4](../../cad/l2_r4)，参数与特征从R3.2/L2-r3继承；FreeCAD文件是独立可编辑实体集合，不声称有完整原生草图约束或动力学关节。正式实物装配建议继续在FreeCAD等外部CAD中测绘真实PCB、补足尺寸链与公差，再打印试装。

R3.2基准固定为Quietmirror/github@f1b1090931d717117287ea2b79c2e14ddc234937，L2-r3发布基准为1ac9de778af0e704daacded23a4eaf46aed9949a；r4作者包固定为f637118455159515a200e6e0f35c0eea1c7d1633。原olliebella、Kotinos、paw3395-pcb及Fenrir引用和实际文件复用关系沿用仓库NOTICE；本轮实际输入是这些已保存的R3.2/L2-r3源文件与r4作者证据包，不冒称重新检查过所有上游最新文件。保留 [CERN-OHL-P-2.0许可证](../../LICENSE)、[NOTICE](../../NOTICE.md) 和 [本轮署名说明](../../cad/l2_r4/ATTRIBUTION.md)。

## 实物待验证项

{pending}
'''
    write('DESIGN_RATIONALE.md',design)
    contacts=read('functional_static_contacts.json');mainmo=read('main_and_wheel_motion_raw.json',[]);sidemo=read('side_functional_motion.json',[]);wires=read('wire_component_clearances.json');reserves=read('reserved_space_checks.json',[])
    text=f'# L2-r4 干涉与间隙复核\n\n状态：**{state}**。\n\n'+common
    text+='精确BRep结果只证明声明的形状与已采样姿态；AABB仅用于排除不可能相交的候选，不作为精确最小距离。所有打印件、硬件和线束均有原始检查，功能配合仅在明确的轴孔、接触面、座面及螺纹区局部分解。\n\n'
    text+=table(['项目','结果','证据'],[[n,g['status'],', '.join(g['evidence'])] for n,g in a['gates'].items() if n in ['G1','G2','G3','G4','G5','G6','G7','G11']])
    text+='## 仍未通过的静态项\n\n'
    failures=[r for r in contacts.get('rows',[]) if not r['passed']]
    text+=table(['A','B','原始间隙','原始相交体积','分类'],[[r['raw']['a'],r['raw']['b'],fmt(r['raw']['gap_mm'],6),fmt(r['raw']['overlap_mm3'],6),r['classification']] for r in failures]) if failures else '当前报告没有未通过项；报告缺失或版本失配仍会阻止最终门槛通过。\n\n'
    text+='## 运动采样\n\n'+table(['组','姿态数','结论'],[[g['group'],len(g['samples']),g['passed']] for g in mainmo]+[[g['part'],len(g['samples']),g['passed']] for g in sidemo])
    text+='完整曲线见 views/l2_r4 中运动图，原始数据在 reports/l2_r4。超过物理止挡的0.3°诊断姿态保留原始接触体积；只把指定止挡区域接触归类为功能限位，其他部位仍须保持净空。\n\n'
    text+='## 线束与预留区\n\n'+f"线束检查记录数：{len(wires.get('rows',[]))}。预留区检查记录数：{len(reserves)}。电池本体要求0.5mm，走线要求0.2mm；服务区和光路检查实体侵入，天线禁区检查导电件侵入。预留区不作为实体元件计算普通间隙。\n\n"
    text+='最薄壁不以随机采样值冒充全局证明。关键壁、铰节、止动耳、螺孔边距有单独截面表；表面法线弦长采样中的极小值可能落在圆角或自由边，必须结合截面与切片检查。详细见 critical_wall_sections.json、surface_normal_wall_samples.json。\n'
    write('INTERFERENCE_REPORT.md',text)
    text='# L2-r4 装配顺序与可达性\n\n'+common
    text+='1. 核对打印件与实物开关，清理支撑、孔和端子槽；先给两颗侧键开关焊接COM/NO线。\n2. 依次装入SR开关、SF开关、SR挡板、SF挡板。SF开关会经过SR挡板位置，顺序不能互换。\n3. 从底部拧入带参考垫圈的两颗M2×5自攻螺钉，固定挡板。\n4. 按实测尺寸调整推杆PET膜，将两键帽沿−X直推到位，再从顶窗插入竖直钢销。\n5. 装配主键、滚轮载架组和H电子件；电池与插头按下方已验证的可拆模块顺序操作。\n6. 接通电路后才进行通断、手感、回弹、无线和充电测试；这些没有被CAD仿真代替。\n\n'
    text+='## 四件从底部装入的路线\n\n'+table(['零件','体素姿态数','精确转折点/落座','结果'],[[r['part'],r['voxel_poses'],'见JSON逐点数值',r['raw_pass']] for r in routes])
    for r in routes:
        text+=f"### {r['part']}\n\n相对最终位置的偏移和yaw：\n\n```json\n"+json.dumps(r['executed_waypoints'],ensure_ascii=False)+'\n```\n\n'
        text+=' '.join(f'![{r["part"]} {i}](../../views/l2_r4/ASSEMBLY_{r["part"]}_{i}.png)' for i in range(1,6))+'\n\n'
    battery=read('battery_service_path.json');plug=read('battery_plug_access.json')
    text+='## 电池与插头\n\n'+f"电池路线通过：{battery.get('passed',False)}；插头工具接近通过：{plug.get('passed',False)}。\n\n"
    for i,step in enumerate(battery.get('service_sequence',[])):text+=f'{i+1}. {step}\n'
    text+='\n实际姿态、最小距离和保留障碍物见 [battery_service_path.json](../../reports/l2_r4/battery_service_path.json)。不能从静态放入结论推断装拆可行，也不能在实物中弯折电池来绕过框架。\n'
    write('ASSEMBLY_SEQUENCE.md',text)
    text=f'# L2-r4 内部结构与运动模拟\n\n状态：**{state}**。\n\n## G8 整壳刚度\n\nC3D10二阶四面体；E=1500MPa，ν=0.35；五脚Uz固定，两个局部点约束面内刚体自由度。CalculiX默认SPOOLES直接法，三个网格档串行运行。每次求解记录可用内存、峰值RSS、真实日志以及力/力矩平衡。\n\n'
    text+=table(['工况','网格mm','刚度N/mm','R3.2基准','比值','作者偏差','平衡'],[[r['case'],r['size_mm'],fmt(r['stiffness_N_per_mm']),fmt(r['baseline_N_per_mm']),f"{100*r['ratio']:.2f}%",f"{100*r['author_difference_fraction']:+.2f}%",r['equilibrium_pass']] for r in g8.get('rows',[])])
    text+='作者根部加载脚本使用Y35..42，正文指定35.5..42.5；本轮采用正文，独立重算R3.2同定义基准，并取其与原表的较大值。相同最终网格只改变加载区的控制求解用于解释根部差异。夹持差异另用作者V2几何控制件重算；几何控制件不属于打印版本。差异调查原始证据见 fem/REFERENCE_R32_ROOT_PROTOCOL.json 与 fem/AUTHOR_GEOMETRY_DIFFERENCE.json。\n\n'
    text+='## S7 侧键5N与螺钉预紧\n\n挡柱施加5N，每颗螺钉采用20N参考预紧。20N是明确的工程假设，不是已知拧紧扭矩换算；模型为线弹性等效面力，没有声称完成摩擦接触、螺纹滑牙或层间破坏预测。整壳和侧框区域P95均需≤10MPa，挡板另查预紧与微动反力。\n\n'
    text+=table(['零件','工况','网格mm','整体P95 MPa','侧框P95 MPa','通过'],[[r['part'],r['case'],r['size_mm'],fmt(r['global_p95_MPa']),fmt(r.get('side_frame_region',{}).get('p95_MPa')),r['passed']] for r in s7.get('rows',[])])
    text+='## S3/S4 侧键行程与理想杠杆力\n\n根据D2F-01F官方OF最大值0.74N、PT最大值0.5mm计算，实际FP/OP/TTP仍待测。各接触点力臂用实际几何坐标定义，未机械套用作者示例中含糊的“中点”数值。\n\n'
    text+=table(['键','触点','Y坐标mm','理想力N','按压行程mm'],[[k['part'],p['location'],fmt(p['y_mm']),fmt(p['ideal_force_N']),fmt(p['tangential_inward_travel_mm'])] for k in act.get('keys',[]) for p in k['force_positions']])
    text+='\n[Omron D2F官方数据表](https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2f.pdf)。该力值不含摩擦、打印弹性、实际预压和装配偏差。其余S1–S9状态逐项见GATES和FINAL_ACCOUNTING。\n'
    write('INTERNAL_COMPONENTS_SIMULATION.md',text)
    text=f'# L2-r4 真实切片报告\n\n状态：{sl.get("status","未取得")}。PrusaSlicer 2.9.6，PLA密度1.24g/cm³，0.4mm喷嘴、0.2mm层高，原尺寸不缩放，255×155mm参考床，organic支撑只从打印床起。\n\n'
    text+=f"CAD聚合物体积：{fmt(mass.get('total_volume_mm3'))}mm³；按PA12 1.01g/cm³：{fmt(mass.get('total_PA12_g'))}g；实心PLA密度估计：{fmt(mass.get('total_solid_PLA_g'))}g。\n\n真实单盘切片耗材：{sl.get('total_filament_g','未取得')}g；时间：{sl.get('time','未取得')}。上述数值不包含电池、主板、钢销、螺钉等实际整机质量。\n\n"
    text+=table(['件名','绕X','绕Y','实际切片质量g','实际切片时长','消息'],[[r['name'],r.get('rotation_x_deg',0),r.get('rotation_y_deg',0),r['total_filament_g'],r['time'],'; '.join(r.get('slicer_messages',[])) or '未返回警告'] for r in sl.get('per_part',[])])
    text+='BODY朝向为脚贴面向下；实际最下缘Z=5.0，脚贴粘贴面Z=5.2，所以排盘时最低边缘先落床，脚贴面比床面高0.2mm。这个首层细节保留原底部几何，实物试印时须核对粘贴面平整度及支撑清理。内部Z12.1附近横隔板由底部开口伸入的有机支撑承托。左右键和侧键保留装配坐标朝向；挡板绕X90°以前Y端落床，滚轮绕Y90°以轴线垂直打印床。具体支撑耗材和范围由真实G-code类型统计，不将“可切片”当作实物强度或支撑可拆证明。\n\n'
    text+=f"最小排盘包围矩形间距：{fmt(sl.get('minimum_xy_bounding_rect_gap_mm'))}mm。单盘3MF重新打开后对象数和尺寸复核：{sl.get('plate_roundtrip',{})}。\n\n"
    text+='![单盘](../../views/l2_r4/PRINT_PLATE.png)\n\n3MF使用Dremel 3D45床面大小作为配置假设，未提供可直接送机的专用G-code。真实打印前须核对机器、材料、孔径补偿、支撑可拆性和首层接触。F2试验件单独保存在SIDE_MODULE_F2_TRIAL.3mf，不替代默认侧键验收。\n'
    write('SLICE_REPORT.md',text);(MODELS/'SLICE_REPORT.md').write_text(text.replace('../../views/','../../views/'),encoding='utf8')
    readme=f'''# Quietmirror L2-r4\n\n**{state}**\n\n右手指握轻量鼠标的参数化机械设计。所有数值都区分CAD、有限离散验证和真实硬件验证；未知供体/主板/镜头参数保持明确估计。\n\n![六视图](../../views/l2_r4/L2_r4_H_SIX_VIEWS_SHEET.png)\n\n- [设计思路与版本修正](DESIGN_RATIONALE.md)\n- [门槛总表](GATES.md) / [完整JSON](FINAL_ACCOUNTING.json)\n- [干涉复核](INTERFERENCE_REPORT.md) / [装配顺序](ASSEMBLY_SEQUENCE.md)\n- [结构模拟与差异调查](INTERNAL_COMPONENTS_SIMULATION.md) / [切片报告](SLICE_REPORT.md)\n- [可编辑源码](../../cad/l2_r4) / [完整模型与打印件](../../models/L2_r4)\n- [所有调整记录](TUNING_LOG.md)\n\n## 试握与装配反馈\n\n依次记录夹持宽度、是否顶掌、无名指/小指是否拖地、主键/侧键/滚轮触达、抬鼠稳定性、侧键是否误触、轮轴是否松旷、支撑清理与孔销装配情况。先确认外形与刚性，再对实物开关进行贴膜调整和触发验证。\n\n## 硬件待验证\n\n{pending}\n'''
    write('README.md',readme)
    home=f'''# Quietmirror L2-r4

**{state}**

右手指握轻量鼠标的可编辑机械设计。r4将侧键托架与BODY一体生成，保留原六孔、底部外轮廓与五个脚贴平台；中键内部端子孔作局部净空修正。两件独立挡板、直推式杠杆侧键和钢销支持后续实物装配。电子元件均明确标为估计包络。

![实际模型六视图](views/l2_r4/L2_r4_H_SIX_VIEWS_SHEET.png)

## 下载和复现

- [完整H装配 STEP](models/L2_r4/FULL_ASSEMBLY_H.step) / [FreeCAD FCStd](models/L2_r4/FULL_ASSEMBLY_H.FCStd)
- [九件单盘打印3MF](models/L2_r4/L2_r4_H_ALL_PARTS_SINGLE_PLATE.3mf) / [逐件STL与STEP](models/L2_r4/parts) / [F2侧键试验件](models/L2_r4/SIDE_MODULE_F2_TRIAL.3mf)
- [D供体可用板域](models/L2_r4/D_MAX_BOARD_ENVELOPE.step) / [参数化源码和复现说明](cad/l2_r4/README.md)
- [G1–G11门槛总表](handoff/l2_r4/GATES.md) / [全部数值与版本身份](handoff/l2_r4/FINAL_ACCOUNTING.json)
- [设计思路](handoff/l2_r4/DESIGN_RATIONALE.md) / [装配顺序](handoff/l2_r4/ASSEMBLY_SEQUENCE.md) / [干涉报告](handoff/l2_r4/INTERFERENCE_REPORT.md)
- [结构有限元](handoff/l2_r4/INTERNAL_COMPONENTS_SIMULATION.md) / [真实切片和方向](handoff/l2_r4/SLICE_REPORT.md) / [所有修正记录](handoff/l2_r4/TUNING_LOG.md)

9件打印件的CAD聚合物体积为{fmt(mass.get('total_volume_mm3'))}mm³，按PA12密度1.01g/cm³估计{fmt(mass.get('total_PA12_g'))}g。真实PLA单盘切片{sl.get('total_filament_g','未取得')}g、{sl.get('time','未取得')}，包含支撑等耗材；不是装好电子件后的整机重量。

## 电子方案与证据范围

H采用PAW3950半组装主板的参考包络，C17编码器转接板是自制板形假设。所选电池包络为{cell_size_text}mm；原18×22×6mm估计包络的有限搜索尚未找到合格拆装路线。电池缩小不代表容量已知或12小时续航达标。D供体仍为用户称为ATK A1 Plus的待确认型号；没有编造真实PCB孔位。

精确CAD结果对应报告中声明的模型与有限离散姿态，不等于连续运动证明、实物公差或电子功能认证。打印后反馈握宽、顶掌、手指拖地、滚轮/侧键触达与抬鼠稳定性，再测试实物按键和电子功能。

## HARDWARE_PENDING

{pending}

## 历史与许可

[L2-r3预发布记录](https://github.com/Quietmirror/Quietmirror-L2/releases/tag/L2-r3)、[r3文档](handoff/l2_r3)、[r2复核](handoff/l2_r2/README.md)、[r1复核](cad/l2_r1/README.md)及R3.2源文件均保留。原始工程另见[Quietmirror/github](https://github.com/Quietmirror/github)。沿用[CERN-OHL-P-2.0](LICENSE)、[NOTICE](NOTICE.md)和[本轮实际来源说明](cad/l2_r4/ATTRIBUTION.md)。
'''
    (ROOT/'README.md').write_text(home,encoding='utf8')
    brief=[]
    for n,g in a['gates'].items():
        m=g['metrics'];value=g['summary']
        if n=='G1':value=f"{m['valid_single_solids']}/9 单一有效实体；{m['closed_meshes']}/9 闭合网格；自相交面 {m['self_intersecting_faces']}"
        elif n=='G2':value=f"静态分类 {m['static_pairs']} 项；未解决 {m['unresolved_static']}；硬件逐对 {m['hardware_pairs']} 项"
        elif n=='G3':value=f"电池最小净空 {fmt(m['battery_minimum_gap_mm'])} mm；线束 {m['wire_checks']} 项；预留区侵入 {m['reserved_invasions']} 项"
        elif n=='G4':value=f"六孔各 200 边界点 + 1000 棱柱点；未分类失败 {sum(r['unclassified_samples'] for r in m['windows'])}"
        elif n=='G5':value='；'.join(str(r.get('group',r.get('part')))+': '+str(r['poses'])+' 姿态' for r in m['main_wheel']+m['side'])
        elif n=='G6':value=f"四件路线 {m['loose_part_poses']} 姿态；键帽直推 {m['cap_translation_poses']} 姿态；工具可达 {m['access_checks']} 项"
        elif n=='G7':value=f"H 独立组件 {m['H_components']}；D 状态 {m['D_status']}"
        elif n=='G8':value=f"{m['solves']} 个实际求解；最低 R3.2 刚度比 {100*(m['minimum_ratio'] or 0):.2f}%"
        elif n=='G9':value='；'.join(k+'='+str(v) for k,v in m['simulations'].items())
        elif n=='G10':value=f"PA12 密度估计 {fmt(m['PA12_g'])} g；实际单盘切片 {m['slicer_total_PLA_g']} g / {m['slicer_time']}"
        elif n=='G11':value=f"压盘覆盖余量 {m['coverage_min_mm']}；PET 厚度范围 {m['film_range_mm']} mm；外向止挡 {m['outward_stop_angles_deg']}"
        brief.append([n,g['status'],value])
    release=f'# Quietmirror L2 r4\n\n**{state}**\n\n侧键托架在生成 BODY 时一体成形，开关背挡拆分为两件可装入零件，键帽改为直线装入。交付包含独立组件 STEP/FCStd、9 个打印件、单盘及 F2 试验 3MF、可编辑源码、原始数值报告和真实模型视图。\n\n'
    release+=table(['门槛','结论','关键实测/仿真数据'],brief)
    release+=f'电子布局采用C17自制编码器转接板参考轮廓和{cell_size_text}mm估计电池；原18×22×6mm电池尚未找到通过路线。所选电池包络体积减少29.29%，容量和12小时续航均未验证。真实供体主板仍为DONOR_PENDING。\n\n'
    release+='![实际六视图](https://raw.githubusercontent.com/Quietmirror/Quietmirror-L2/L2-r4/views/l2_r4/L2_r4_H_SIX_VIEWS_SHEET.png)\n\n'
    release+='## 参考差异和证据范围\n\n'+a['evidence_limit']+'\n\n根部刚度偏差来自正文与作者脚本加载区间不同，夹持偏差通过三档作者 V2 几何控制计算区分了几何影响。完整数值与修正理由见 handoff/l2_r4/INTERNAL_COMPONENTS_SIMULATION.md 和 TUNING_LOG.md。\n\n'
    release+='## HARDWARE_PENDING\n\n'+pending+'\n\n保留 CERN-OHL-P-2.0 与 NOTICE 署名。L2-r3 tag、Release、作者证据分支和全部历史提交保持保留。\n'
    write('RELEASE_NOTES.md',release)
    print('WROTE_DOCS',state,flush=True)
if __name__=='__main__':main()
