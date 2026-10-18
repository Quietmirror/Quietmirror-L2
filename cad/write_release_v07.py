"""Publish-facing documentation derived from saved validation and slice data."""
from pathlib import Path
import json,subprocess
ROOT=Path(__file__).resolve().parents[1];RP=ROOT/'reports/v07'
def read(n):return json.loads((RP/n).read_text(encoding='utf8'))
def write(n,s):(ROOT/n).write_text(s,encoding='utf8')
def main():
    c=read('cad_metrics.json');v=read('validation.json');g=read('geometry_checks.json');sl=read('slice_summary.json');mass=sl['plate_estimate']
    assert v['topology_pass'] and v['rigid_motion_pass'] and all(a['pass_check'] for a in v['insertion_paths'])
    xyz=c['parts'][0]['dimensions_xyz_mm'];volume=sum(a['volume_mm3'] for a in c['parts'])/1000
    archive=ROOT/'README_V0.6.md'
    if not archive.exists():archive.write_bytes(subprocess.check_output(['git','show','6c43049426fdda54379b73b59314773750b6ce1b:README.md']))
    summary=f'''# Quietmirror · 右手指握鼠标

**当前 V0.7：缩小左右主键，增加前部镂空；按毒蝰 V3 Pro 的侧键外形方向重新设计细长双侧键。交付 20 件可打印机械试按套件、ATK A1 Plus 示意和 PAW3950 半组装板示意。V0.1–V0.6 全部保留。**

![V0.7 实际模型](views/v07/12_three_variants.png)

**[完整项目 ZIP，含所有历史版本](https://github.com/Quietmirror/github/archive/refs/heads/main.zip)** · [历史版本](HISTORY.md) · **[装配、辅料和打印说明](reports/v07/ASSEMBLY.md)** · [电子限制与功能目标](reports/v07/ELECTRONICS.md)

## 下载这次的三个版本

| 版本 | 文件 | 用途 |
|---|---|---|
| **机械试握/试按套件** | **[打印托盘 3MF](exports/v07/quietmirror_V0.7_PRINT_PLATE.3mf)** · **[20 个分件 STL/STEP](exports/v07/print/)** · [装配 STEP](exports/v07/quietmirror_V0.7_MECHANICAL_ASSEMBLY.step) · [观察 3MF](exports/v07/quietmirror_V0.7_MECHANICAL_VIEW_ONLY.3mf) | 装入五枚示例轻触开关后测试点击和回位；轮体可转动、滚轮架可下压。设计已做几何检查，尚未实物装配 |
| **ATK A1 Plus 主板示意** | [装配 STEP](exports/v07/quietmirror_V0.7_ATK_A1_PLUS_ESTIMATED.step) · [观察 3MF](exports/v07/quietmirror_V0.7_ATK_A1_PLUS_VIEW_ONLY.3mf) · [净空 STEP](exports/v07/quietmirror_V0.7_ATK_A1_PLUS_CLEARANCES.step) | 供体型号、实际板形/孔位/传感器仍未确认；估计整板与新增试按机构有冲突 |
| **PAW3950 半组装板示意** | [装配 STEP](exports/v07/quietmirror_V0.7_PAW3950_CUSTOM_ESTIMATED.step) · [观察 3MF](exports/v07/quietmirror_V0.7_PAW3950_CUSTOM_VIEW_ONLY.3mf) · [净空 STEP](exports/v07/quietmirror_V0.7_PAW3950_CUSTOM_CLEARANCES.step) | 主控、传感器和 RF 分板空间方案；编码器与打印试按机构的接口尚未解决 |

只有 **PRINT_PLATE.3mf / print/** 是打印文件。装配场景含重叠的估计电子包络或非打印开关，不应整场景合并打印。`placed/` 保留装配坐标。[先打印间隙校准件](exports/v07/calibration/)。

## 外形和操作机构

- 左右主键的名义触感区域由 **23 × 41 mm 缩为 16 × 27 mm**，矩形投影面积减少约 **54%**；曲面触感面保留，按键边口增加 0.4 mm 圆角，平面转角 R3 mm。尺寸仍是试握假设。
- 保留 12 个后壳孔的轮廓分区，并在主键释放区域增加 **{g['holes']['front_profiles']} 个镜像减重孔轮廓**。中央增加 **14.2 × 34 mm** 滚轮架装配开口，与主键/滚轮的安装开口连通；不将这些连通开口重复计数为独立孔。接触面不开孔，支撑和安装区保留必要实体。
- 双侧键改为约 **12 × 4.45 mm** 的细长轮廓，名义中心距前端 **39.5 / 53.5 mm**、高度 **15.5 / 16.0 mm**，端部收窄、外缘倒圆。本轮按 Viper V3 Pro 理解“v3p”，没有复制商业 CAD 或按照片臆测实测尺寸。[实际查看资料](references/V0.7_REFERENCE_NOTES.md)
- 五个输入位置各有独立柱塞、导向、可拆挡片及开关托架。打印轮体、3 mm 轴、轴端垫片和滚轮支架可以分开装配；可选 0.8 mm 弹片用于机械段落感。
- **点击和回位需要另装五枚 6 × 6 × 5 mm 轻触开关。** 仅打印件不能评价真实鼠标微动手感；示例开关是机械测试辅料，未指定最终主板开关。滚轮的转动与段落试验不产生电脑滚动信号。
- CAD 最大空行程 **0.4 mm**，示例轻触开关标称行程 **0.25 mm**。装配时必须调校开关高度和限位；不可直接把 0.4 mm 当作开关许可行程。

![主键前后对比](views/v07/09_comparison.png)

## 验证与用料

| 检查 | 实际结果 |
|---|---|
| 20 个塑料件 | 全部有效单实体；STL 单连通、封闭、法线一致；自相交面数 0 |
| 五键运动 | 每键 9 个位置，共 45 个位置检查；0–0.4 mm 内未发现刚性体积干涉 |
| 装入路径 | 四键和滚轮架各 31 个位置；移除挡片、托架和其他活动件后，从规定方向装入，采样检查通过 |
| 滚轮转动 | 使用 Ø15 / 内孔 Ø3.5 × 宽 5.2 mm 的连续圆环外包络检查，与壳体、轴和支架无刚性干涉 |
| 可选弹片 | 有意与齿峰接触，属于弹性段落结构；已记录接触体积，没有做弹性仿真或寿命试验 |
| 底部 | 与 V0.6 在 **Z≤5.4 mm** 的布尔对称差体积 **{v['base_symmetric_difference_mm3']:.6f} mm³**；五脚 45 点仍共面 Z=0 |
| 普通壳面壁厚 | {g['normal_wall']['count']} 个法向样本，最小 **{g['normal_wall']['minimum_mm']:.3f} mm**；不等于全局最薄壁证明 |
| 对称 | 侧键及其安装区域以外，BODY 镜像网格偏差最大 **{g['symmetry']['body_max_mirror_distance_mm']:.3f} mm**；左右主键最大 **{g['symmetry']['main_key_max_mirror_distance_mm']:.3f} mm** |
| 实际壳体尺寸 | 长 × 宽 × 高 **{xyz[1]:.3f} × {xyz[0]:.3f} × {xyz[2]:.3f} mm**；毫米单位、100% 导入 |
| 20 个塑料件 CAD 总体积 | **{volume:.3f} cm³**；不包含另购开关、螺钉、主板、电池和脚贴 |

实际使用 PrusaSlicer 2.9.6 对最终 3MF 切片：0.4 mm 喷嘴、0.2 mm 层高、4 壁、20% gyroid、PLA 1.24 g/cm³。模型 **{mass['model_g']:.2f} g**，支撑 **{mass['support_g']:.2f} g**，裙边 **{mass['adhesion_g']:.2f} g**，总耗材 **{mass['total_g']:.2f} g**，约 **{mass['time']}**。3MF 不加载外部 INI 重切片，8 项关键配置从 G-code 回读一致。它是通用估计配置，需换成实际打印机配置后打印。

没有实物打印、称重、摩擦/手感、强度或电子功能实测。机械试按增加了托架、挡片等零件，本轮没有把整套重量当作最终轻量化鼠标重量。[完整几何报告](reports/v07/validation.json) · [壁厚/对称](reports/v07/geometry_checks.json) · [切片数据](reports/v07/slice_summary.json)

## 外部建模软件建议

**推荐下一阶段用 FreeCAD 的装配工作台继续。** 现在需要围绕真实开关、编码器、PCB 和电池建立固定、滑动、转动约束，并检查预压、回位及装配空间；这些适合参数化 CAD 装配。当前源文件本身使用 CadQuery/OpenCascade 进行实际实体建模，不是从渲染图转成的 STL。

已附 [FreeCAD 导入宏](cad/open_v07_in_FreeCAD.FCMacro)，可在 FreeCAD 中把分件 STEP 导入为命名零件并保存本地 FCStd。**宏未在本机 FreeCAD 中执行验证；STEP 导入不会还原 CadQuery 的参数历史树，宏也不会自动建立已求解关节。** 主要可编辑参数仍在 [parameters_v07.json](cad/parameters_v07.json) 与 [mechanisms_v07.py](cad/mechanisms_v07.py)。

[FreeCAD 官方装配工作台文档](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Assembly_Workbench.md)列有固定、滑动和转动关节。后续先完成试按和实测元件，再做正式装配；不建议在没有真实 PCB 尺寸时反复修改估计孔位。

## 源码、复现与历史

[模型生成器](cad/build_v07.py) · [机构源码](cad/mechanisms_v07.py) · [参数](cad/parameters_v07.json) · [电子源码](cad/electronics_v07.py) · [电子参数](cad/electronics_v07.json) · [复现步骤](cad/PARAMETERS_V0.7.md)

V0.1–V0.6 的模型、源码、参数、图、报告保持原文件。V0.6 当时的首页保存为 [README_V0.6.md](README_V0.6.md)。[历史保留核对](reports/v07/history_preservation.json) · [许可证](LICENSE) · [既有署名](NOTICE.md)。
'''
    write('README.md',summary)
    write('reports/v07/DESIGN.md',summary.replace('](views/','](../../views/').replace('](exports/','](../../exports/').replace('](reports/v07/','](').replace('](references/','](../../references/').replace('](cad/','](../../cad/').replace('](HISTORY.md)','](../../HISTORY.md)').replace('](README_V0.6.md)','](../../README_V0.6.md)').replace('](LICENSE)','](../../LICENSE)').replace('](NOTICE.md)','](../../NOTICE.md)'))
    rows=[]
    for name,label in [('ATK_A1_PLUS','ATK A1 Plus 供体'),('PAW3950_CUSTOM','PAW3950 半组装板')]:
        e=read(name+'_layout.json');clear=read(name+'_clearances.json');rows.append(f'## {label}\n\n')
        for a in e['physical']:
            if a['mechanical_hits']:rows.append('- **'+a['name']+'**：'+ '；'.join(h['part']+f" {h['overlap_mm3']:.3f} mm³" for h in a['mechanical_hits'])+'。\n')
        for a in e['component_intersections']:
            if not a['intentional']:rows.append(f"- {a['a']} / {a['b']}：{a['overlap_mm3']:.3f} mm³。\n")
        ant=next(a for a in clear['reservations'] if a['name']=='antenna_clearance_EST')
        rows.append('\n天线估计净空与电子包络相交：'+('；'.join(h['part']+f" {h['volume_mm3']:.3f} mm³" for h in ant['component_hits']) or '未发现')+'。这不是射频测试。\n\n')
    write('reports/v07/ELECTRONICS.md','''# V0.7 电子空间、冲突与待测数据

两个模型仍然是示意。红色部件表示与本轮机械试按机构存在显著体积相交（阈值 0.01 mm³）。正式电子版需要替换部分试按托架、打印轴/弹片，并按真实开关和编码器重新设计，不能直接把整套试按件和估计板盒一起装入。

'''+''.join(rows)+'''
ATK 方案保留了上一版的 36×50×1.2 mm 估计整板包络；新增托架后该包络无法直接放入。它不是 ATK A1 Plus 的实测板形，也不是允许切割供体 PCB 的加工图。需要确认供体完整型号、实际 PCB 外轮廓、元件高度和不可移动的接口，随后决定改托架、改布局或改壳体。

PAW3950 方案改用前部 20×14×1.2 mm 控制/充电区、18×16×1.2 mm 传感器板和后部 RF 板空间目标；这并不是已布线的电路。静态估计中其主要剩余冲突是编码器包络与打印轴、左键托架及壳体。需要采用真实编码器，重新做轴端、编码器支撑和左键内侧结构；不能通过悄悄缩小未选定元件的包络宣布完成适配。

五个 6×6×5 mm 轻触开关用于机械试按，不指定最终鼠标主板开关。主板安装孔没有从这些开关托架的 M2 孔反推。电子示意场景的 STEP/3MF 不包含已验证的 PCB 固定、焊接和编码器连接。

## 包络与功能目标

主板、传感器和镜头、编码器、侧键板、电池和插头、USB-C、充电区、电源开关分别建模。六个独立净空块覆盖电池拆装、天线、光路、USB 插头与左右线束走廊，保存在各自 CLEARANCES STEP。线束走廊只是预留空间，不是布线结果；与端点部件相交需要结合用途解释。主键和侧键的活动空间另用实际活动 CAD 检查。

| 功能 | 目标 / 当前状态 |
|---|---|
| 分辨率 | 400–6400 DPI；待主板与固件实现和实测 |
| 可选同步增强 | 不使用 MotionSync 等可选 Sync 跟踪增强；必要的 USB/无线通信时序不在此排除范围 |
| 无线报告率 | 2.4 GHz、1000 Hz；需主板、固件、匹配接收器共同实现 |
| 宏、LOD、五键和滚轮 | 作为电子验收目标保留；机械模型没有实现宏、LOD 或 HID 输入 |
| 低延迟 | 待端到端测试，不能根据 1 kHz 或传感器名称直接给出延迟数值 |
| 供电与充电 | 保留底部开关口和前部充电孔；充电保护、电池温升和实际充电电流未验证 |
| 满性能持续运行 | 目标至少 12 h；未做续航测试 |

PAW3950 只是传感器型号，不代表统一主板外形、孔位或 1 kHz 无线能力。ATK 方案没有被替换为 F1、A9、Z1 等其他型号，也没有被假定使用 PAW3950。

## 续航仍是预算，不是结果

暂用 500 mAh 容量目标、75% 可用容量系数和 30 mA 连续工作电流预算：500×0.75÷30 = **12.5 h**。要达到 12 h，平均电流应不超过 **31.25 mA**；如果达到 40 mA，同一电池只有 **9.375 h**，至少约 **640 mAh** 才满足相同预算。

为了避开试按机构，新版电池空间目标缩为 **20×24×6 mm**。**没有确认此包络内可以买到合适的 500 mAh 电池**；容量与外形是两项待验证条件。真实电池放不下、连续电流过高、保护板/插头额外占位时，需要改布局或壳体，不能继续声称满足 12 h。

## 电子装配前必须量到的数据

1. 供体完整型号和 PCB 正反面尺寸、厚度、孔坐标、元件最高点；确认传感器版本。
2. 传感器中心、安装面、镜头型号及其光学参考面；从鼠标垫、脚贴、五脚平台、底筋、镜头到 PCB 的完整 Z 尺寸链。
3. 主键/侧键/中键开关外形、自由高度、触发与释放行程、极限行程；不能把本轮轻触开关参数沿用于供体微动。
4. 编码器高度、轴孔或插槽形状、轴长、固定耳和电气引脚；重新设计轮轴与中键动作配合。
5. 电池实物容量与外形、保护板、插头、引线弯曲和拆装空间；连续工作电流与充电温升。
6. USB-C 接口和线缆插头尺寸、电源开关拨杆、天线位置及厂商净空要求。
7. 宏、LOD、DPI、1 kHz 和接收器配对的固件能力与实际延迟、续航测试。

传感器轴线仍垂直鼠标垫。镜头的示意高度没有完成真实尺寸链；本版不能据此确定传感器光学工作高度。
''')
    history=(ROOT/'HISTORY.md').read_text(encoding='utf8').replace('V0.5、V0.6**','V0.5、V0.6、V0.7**').replace('V0.6 没有覆盖旧模型。','V0.7 没有覆盖旧模型。').replace('[当前说明](README.md) · [源码](cad/build_v06.py)','[归档说明](README_V0.6.md) · [源码](cad/build_v06.py)')
    if '## V0.7 活动试按套件' not in history:history+='''\n## V0.7 活动试按套件

缩小左右主键、增加镜像前孔，细长双侧键；20 个塑料件组成五键及滚轮机械试按套件。V0.6 的 Z≤5.4 mm 底部保留。另附两种电子空间示意，并明确标出未解决冲突。

[当前说明](README.md) · [分件 STL/STEP](exports/v07/print/) · [打印 3MF](exports/v07/quietmirror_V0.7_PRINT_PLATE.3mf) · [机械装配 STEP](exports/v07/quietmirror_V0.7_MECHANICAL_ASSEMBLY.step) · [ATK 示意](exports/v07/quietmirror_V0.7_ATK_A1_PLUS_ESTIMATED.step) · [PAW3950 示意](exports/v07/quietmirror_V0.7_PAW3950_CUSTOM_ESTIMATED.step) · [所有视图](views/v07/) · [历史核对](reports/v07/history_preservation.json)。

V0.7 是机械试按设计，不是实物验证完成的产品；旧版固定触感件的说明仍按各自历史范围理解。
'''
    write('HISTORY.md',history)
if __name__=='__main__':main()
