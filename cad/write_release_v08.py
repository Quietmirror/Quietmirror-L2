"""V0.8 release prose derived from verified saved CAD and slicer results."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
RP=ROOT/'reports/v08'
def read(n):return json.loads((RP/n).read_text(encoding='utf8'))
def write(p,t):(ROOT/p).write_text(t,encoding='utf8')

def main():
    c=read('cad_metrics.json');v=read('validation.json');g=read('geometry_checks.json');sl=read('slice_summary.json');b=read('base_trim.json')
    assert v['topology_pass'] and v['rigid_motion_pass'] and not v['static_intersections'] and all(a['pass_check'] for a in v['insertion_paths'])
    es={n:read(n+'_layout.json') for n in ('ATK_A1_PLUS','PAW3950_CUSTOM')}
    assert all(e['static_and_sampled_motion_pass'] for e in es.values())
    mass=sl['plate_estimate'];xyz=c['parts'][0]['dimensions_xyz_mm'];vol=sum(a['volume_mm3'] for a in c['parts'])/1000
    tip=min(a['full_press_tip_to_body_mm'] for a in v['front_key_clearance'])
    summary=f'''# Quietmirror · 右手指握鼠标

**当前 V0.8：局部内收底框，主键恢复原宽度并保持短长度，前沿开放；双侧键前移并改为 Fenrir 方向的贴合曲面。机械试按版与两种电子示意版同步更新，V0.1–V0.7 全部保留。**

![V0.8 实际模型](views/v08/01_isometric.png)

**[完整项目 ZIP，包含所有历史版本](https://github.com/Quietmirror/github/archive/refs/heads/main.zip)** · [历史版本](HISTORY.md) · [装配与打印](reports/v08/ASSEMBLY.md) · [电子空间与未完成项](reports/v08/ELECTRONICS.md)

## 这次改动

| 部位 | V0.8 的具体处理 |
|---|---|
| 底部外伸框架 | 使用平面轮廓内收 **0.7 mm**、前后边界各内退 **0.8 mm** 限定原底框，仅修掉超出边界的部分，共 **{b['removed_framework_mm3']:.3f} mm³**；没有整体缩放鼠标 |
| 左右主键 | 从上一版 16×27 mm 恢复为 **23×27 mm**，即保留 V0.6 的 23 mm 原宽度、保留 V0.7 的 27 mm 短长度；两键镜像，指肚面不开孔 |
| 主键前沿 | 连续曲面键帽位于框架上方；前沿框架上缘退至 Z=11.8 mm。前端 D≤2 mm 区域在下压 0.4 mm 后，与壳体最小距离 **{tip:.3f} mm** |
| 侧键位置 | 柱塞中心由前端 D39.5/53.5 mm 移至 **D36.5/50.5 mm**，整体前移 3 mm；高度随外侧曲面调整 |
| 侧键外形 | 一条 **26.6×4.8 mm** 的微斜曲面带分成两个独立键，中央名义间隔 **1.4 mm**；沿母壳曲面形成，外凸仅 **0.35 mm**，触感边 R0.3 mm |
| 顺滑侧面 | 将侧键固定导向退入壳内，去掉外侧方块式台阶；保留连续侧壳，右侧没有侧键开口 |
| 内部让位 | 给主键柱塞肩部增加竖直装入槽；对前侧键挡片和侧键托架做局部让位，保留导向止挡面和托架安装柱承力面 |
| 镂空 | 保留 12 个后壳孔轮廓，前部按更宽主键重新生成 **{g['holes']['front_profiles']} 个镜像孔轮廓**；安装开口可能连通，不能把刀具轮廓数当作完全独立孔数 |

“原宽度”按本项目 V0.6 的 23 mm 理解。机身名义长 90、最大宽 62、握宽 54、高 28 mm，仍是试握假设；没有从 230 mm 手长/190 mm 张开跨度推算掌宽，也没有按手长整体放大。

![宽度前后对比](views/v08/09_comparison.png)
![贴合曲面侧键](views/v08/03_left_side.png)

## 下载三个版本

| 版本 | 下载 | 当前用途 |
|---|---|---|
| **完整机械试握/试按套件** | **[打印 3MF](exports/v08/quietmirror_V0.8_PRINT_PLATE.3mf)** · **[20 个 STL/STEP 分件](exports/v08/print/)** · [装配 STEP](exports/v08/quietmirror_V0.8_MECHANICAL_ASSEMBLY.step) · [观察 3MF](exports/v08/quietmirror_V0.8_MECHANICAL_VIEW_ONLY.3mf) | 打印后另装五枚示例轻触开关，试验五键点击/回位；轮体可转、支架可下压。没有实物测试 |
| **ATK A1 Plus 估计布局** | [STEP](exports/v08/quietmirror_V0.8_ATK_A1_PLUS_ESTIMATED.step) · [观察 3MF](exports/v08/quietmirror_V0.8_ATK_A1_PLUS_VIEW_ONLY.3mf) · [净空 STEP](exports/v08/quietmirror_V0.8_ATK_A1_PLUS_CLEARANCES.step) | 未取得真实供体 CAD；估计板包络保留 36×50×1.2 mm，重排高度和周边部件以避让 |
| **PAW3950 半组装板估计布局** | [STEP](exports/v08/quietmirror_V0.8_PAW3950_CUSTOM_ESTIMATED.step) · [观察 3MF](exports/v08/quietmirror_V0.8_PAW3950_CUSTOM_VIEW_ONLY.3mf) · [净空 STEP](exports/v08/quietmirror_V0.8_PAW3950_CUSTOM_CLEARANCES.step) | 分板空间目标，尚无电路、正式安装结构或固件 |

**电子场景是单独配置：移除 5 个试按托架、5 个挡片和 1 个弹片，明确预留给正式电子安装结构。** 这些 11 个机械试验件仍在完整打印套件中。电子场景内剩余 9 个塑料件、5 个开关位置示例及 13 个电子包络，已检查它们之间的静态和采样行程干涉；正式 PCB/开关固定、编码器与轮轴的连接尚未设计，不能把示意配置直接当成可装电子的成品。

只有 **PRINT_PLATE.3mf / print/** 用于打印。`placed/` 和 `VIEW_ONLY` 保留装配位置，含非打印硬件；`CLEARANCES` 是预留空间。[先打印校准件](exports/v08/calibration/)。

![三个版本的实际模型](views/v08/12_three_variants.png)

## 检查结果及证据边界

| 检查 | 保存产物的实际结果 |
|---|---|
| 20 个塑料件 | 每件 CAD 有效且单实体；STL 单连通、封闭、法线一致，自相交面数 0 |
| 静态相交 | 20 个塑料件两两检查，未发现超过 0.01 mm³ 的体积相交；另检查五个开关示例的静止配合 |
| 五键行程 | 每键 9 个位置，共 45 个位置，0–0.4 mm 内未发现超过阈值的刚性穿插 |
| 侧键与主键 | 活动组纵向区间至少间隔 **{v['main_to_front_side_longitudinal_gap_mm']:.3f} mm**；主键沿 Z、侧键沿 X 运动不会缩小该纵向间隔 |
| 装入次序 | 先预装滚轮组，再装左键、右键、前侧键、后侧键；每条路径 31 个位置，与壳体和此前已装入件一起检查，全部通过 |
| 滚轮旋转 | 连续圆环外包络 Ø15 / 内孔 Ø3.5 / 宽5.2 mm 与固定件及弹片无刚性相交，另检查 3 个旋转相位 |
| 弹片 | 默认与齿峰外包络留 0.05 mm 名义间隙；段落感需实物调预压，未做弹性或寿命仿真 |
| 五脚与功能区域 | 五脚 45 点共面 Z=0；五个脚贴台、传感器及电源开关下部区域与 V0.7 的布尔对称差均小于 0.001 mm³ |
| 底部变化 | Z≤5.4 mm 与 V0.7 的对称差 **{v['base_symmetric_difference_mm3']:.6f} mm³**，属于本次授权的局部框架修整 |
| 壳面厚度 | 普通壳面 {g['normal_wall']['count']} 个法向样本，最小 **{g['normal_wall']['minimum_mm']:.3f} mm**；这不是全局最薄壁证明 |
| 镜像 | 排除侧键及内部安装区后，BODY 采样镜像偏差最大 **{g['symmetry']['body_max_mirror_distance_mm']:.3f} mm**；两主键最大 **{g['symmetry']['main_key_max_mirror_distance_mm']:.3f} mm** |
| 电子场景 | 两个配置各 13 个实体包络与保留机构及其采样运动未发现超过 0.01 mm³ 的相交；不证明供体适配或电路可用 |

“未发现穿模”仅对应上述模型、阈值和采样方法。按键行程/装入路径为离散采样，没有连续运动求解；实际摩擦、打印误差、螺钉头、开关预压、强度和寿命尚未实测。导向、止挡和安装面允许设计接触，不把零距离接触误称为体积穿插。

小零件仍有有意薄壁：弹片0.8 mm、轴端导孔旁0.65 mm、垫片孔边0.8 mm、挡片沉头窝余厚约0.55 mm。需单独试印和试拧，不能由普通壳面的厚度统计推定它们已通过强度验证。

[完整几何与行程报告](reports/v08/validation.json) · [壁厚和对称报告](reports/v08/geometry_checks.json) · [包装检查](reports/v08/package_checks.json) · [底框修整边界](reports/v08/base_trim.json)

## 打印与耗材

壳体实际长×宽×高为 **{xyz[1]:.3f}×{xyz[0]:.3f}×{xyz[2]:.3f} mm**。20 个塑料件总 CAD 体积 **{vol:.3f} cm³**，不含开关、螺钉、电池、主板及脚贴。

使用 PrusaSlicer 2.9.6，0.4 mm 喷嘴、0.2 mm 层高、4 壁、20% gyroid、PLA 1.24 g/cm³，对实际打印 3MF 切片。模型 **{mass['model_g']:.2f} g**，支撑 **{mass['support_g']:.2f} g**，裙边 **{mass['adhesion_g']:.2f} g**，总耗材 **{mass['total_g']:.2f} g**，约 **{mass['time']}**。打印 3MF 不依赖额外 INI 重切，8 项配置由 G-code 回读核对；换成自己的打印机配置后再打印。[切片结果](reports/v08/slice_summary.json)

BODY 五脚朝下，横向导向/桥接和曲面下方需要可从底部清理的支撑；主键触感面朝上；滚轮侧面平放、轴孔朝上；小零件使用 `print/` 内朝向。完整辅料、螺钉和装配步骤见 [ASSEMBLY](reports/v08/ASSEMBLY.md)。0.4 mm 是结构最大空行程，不是示例开关许可行程；点击回位需另装和调校真实开关。

## 视图、编辑与下一步

[俯视](views/v08/02_top.png) · [侧视](views/v08/03_left_side.png) · [底视](views/v08/04_bottom.png) · [正视](views/v08/06_front.png) · [爆炸图](views/v08/07_exploded.png) · [内部机构](views/v08/08_internal.png) · [电子包络](views/v08/)

实际源为 **CadQuery/OpenCascade 实体建模**：[生成器](cad/build_v08.py)、[机构](cad/mechanisms_v08.py)、[尺寸参数](cad/parameters_v08.json)、[电子参数](cad/electronics_v08.json)、[完整复现步骤](cad/PARAMETERS_V0.8.md)。

推荐后续将分件 STEP 导入 FreeCAD 做装配约束，围绕实测 PCB、编码器和开关继续搭建。其装配工作台提供固定、滑动和转动关节，见 [官方装配文档](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Assembly_Workbench.md)。[导入宏](cad/open_v08_in_FreeCAD.FCMacro)只导入命名实体；本机未运行验证，不会自动恢复 CadQuery 历史树或生成已求解关节。

试握记录：握宽、顶掌、无名指/小指拖地、指肚是否碰孔边、主键长度、侧键与滚轮触达、抬鼠稳定性；试按另记录回位、卡滞、误触、轮轴晃动和中键行程。

电子功能目标仍为400–6400 DPI、2.4 GHz/1 kHz、宏、LOD、五键和滚轮、无可选 Sync 增强、开关与充电、满性能续航至少12 h。主板/固件/接收器未实现或测试这些功能，PAW3950 也不代表固定主板尺寸。待测尺寸和功耗预算详见 [电子说明](reports/v08/ELECTRONICS.md)。

V0.1–V0.7 原模型、代码、图与报告保留，上一版首页另存 [README_V0.7.md](README_V0.7.md)。[历史文件核对](reports/v08/history_preservation.json) · [本轮实际参考](references/V0.8_REFERENCE_NOTES.md) · [许可证](LICENSE) · [署名](NOTICE.md)。
'''
    write('README.md',summary)
    design=summary
    for folder in ('views/','exports/','reports/','cad/','references/'):
        design=design.replace(']('+folder,'](../../'+folder)
    for f in ('HISTORY.md','README_V0.7.md','LICENSE','NOTICE.md'):
        design=design.replace(']('+f+')','](../../'+f+')')
    write('reports/v08/DESIGN.md',design)
    old=(ROOT/'reports/v07/ELECTRONICS.md').read_text(encoding='utf8')
    retained=old[old.index('## 包络与功能目标'):].replace('为了避开试按机构，新版电池空间目标缩为','本版继续保留电池空间目标')
    lines=['# V0.8 电子配置、检查与待完成接口\n\n两种方案仍是估计包络，未取得供体 PCB 实测数据，不是假定 ATK A1 Plus 使用 PAW3950。\n\n']
    lines.append('## 与机械试按配置的区别\n\n电子场景明确省略 5 个 TRAY、5 个 RETAINER、1 个 DETENT_LEAF，共 11 个试验夹具。留下9个塑料外形/活动件、5个示例开关位置和13个电子实体包络。省略件完整列在 layout.json；完整20件机械套件仍保留。**最终PCB/开关固定、轮轴与编码器耦合、中键下压兼容接口均待设计，电子场景没有可用的最终安装结构。**\n\n')
    lines.append('## 本轮布局调整\n\nATK主板估计36×50×1.2 mm尺寸不变，中心Z降至5.4 mm，并调整传感器/镜头示意高度；不意味着供体可以任意移动元件或切板。传感器光学尺寸链尚未成立。编码器4×6×7 mm包络移至X=-10.9、D=14、Z=13.3 mm，轮轴耦合未完成；侧键板移至X=-20、D=58、Z=10.3 mm。自制板方案保留分板概念。电源拨杆从示意壳体让位孔伸出，二者没有实体体积重叠。\n\n')
    for n,e in es.items():
        clear=read(n+'_clearances.json');ant=next(a for a in clear['reservations'] if a['name']=='antenna_clearance_EST')
        lines.append(f"## {n}\n\n静态实体相交：{len(e['component_intersections'])}；电子实体对保留机械件的静态和8个非零行程位置检查通过（阈值0.01 mm³）。这只说明本组估计包络的排布，不保证实际零件能装入。\n\n")
        lines.append('天线预留区与电子实体的相交：'+('；'.join(h['part']+f" {h['volume_mm3']:.3f} mm³" for h in ant['component_hits']) or '未发现超过阈值的相交')+'。预留区不能替代真实天线厂商净空要求或射频测试。\n\n')
        optical='ATK光学区目前也包含估计主板与传感器的一部分，不能据此认定光路已畅通' if n=='ATK_A1_PLUS' else '光学区包含镜头包络，但仍未完成真实镜头到鼠标垫的尺寸链'
        lines.append('其他净空是用途包络：电池维护区包含电池和插头，USB插头区包含接口；'+optical+'。线束盒未布真实导线、未求弯曲半径或拆装轨迹。\n\n')
        lines.append(f"[布局检查]({n}_layout.json) · [六类参考净空]({n}_clearances.json)\n\n")
    lines.append(retained)
    write('reports/v08/ELECTRONICS.md',''.join(lines))
    h=(ROOT/'HISTORY.md').read_text(encoding='utf8').replace('V0.5、V0.6、V0.7**','V0.5、V0.6、V0.7、V0.8**').replace('V0.7 没有覆盖旧模型。','V0.8 没有覆盖旧模型。')
    h=h.replace('[当前说明](README.md) · [分件 STL/STEP](exports/v07/','[归档说明](README_V0.7.md) · [分件 STL/STEP](exports/v07/')
    if '## V0.8 平顺侧键与前端开放' not in h:
        h+='''
## V0.8 平顺侧键与前端开放

主键恢复23 mm原宽并保持27 mm短长度，前沿框架退开；侧键前移3 mm并贴随侧壳曲面，底框局部收边。修正内部让位，并按静止、按压、转动和顺序装入进行检查。电子示意单独替换11个试按夹具，最终安装接口待设计。

[当前说明](README.md) · [分件 STL/STEP](exports/v08/print/) · [打印 3MF](exports/v08/quietmirror_V0.8_PRINT_PLATE.3mf) · [机械 STEP](exports/v08/quietmirror_V0.8_MECHANICAL_ASSEMBLY.step) · [ATK 示意](exports/v08/quietmirror_V0.8_ATK_A1_PLUS_ESTIMATED.step) · [PAW3950 示意](exports/v08/quietmirror_V0.8_PAW3950_CUSTOM_ESTIMATED.step) · [所有视图](views/v08/) · [历史核对](reports/v08/history_preservation.json)。
'''
    write('HISTORY.md',h)
    print('V0.8 release documentation written')

if __name__=='__main__':main()
