"""Write evidence-derived V0.6 summary, print notes and assembly limitations."""
from pathlib import Path
import json,subprocess
ROOT=Path(__file__).resolve().parents[1];rp=ROOT/'reports/v06'
def read(n):return json.loads((rp/n).read_text(encoding='utf8'))
def write(path,text): (ROOT/path).write_text(text,encoding='utf8')

def main():
    c=read('cad_metrics.json');v=read('validation.json');g=read('geometry_checks.json');sl=read('slice_summary.json');l=read('vent_layout.json');rt=read('3mf_roundtrip.json')
    xyz=c['dimensions_xyz_mm'];mass=sl['material_by_category_g'];time=sl['footer']['estimated printing time (normal mode)'];total=sl['footer']['filament used [g]'];rows=[]
    for variant in ('ATK_A1_PLUS','PAW3950_CUSTOM'):
        e=read(variant+'_layout.json')
        collisions=[x for x in e['physical'] if x['shell_overlap_mm3']>.01 or x['caps_overlap_mm3']>.01];pairs=[x for x in e['component_overlaps'] if not x['intended_interface']]
        rows.append(f"## {variant}\n\n独立电子示意体 {len(e['physical'])} 件；壳体/侧键显著体积干涉 {len(collisions)} 项；非预期组件干涉 {len(pairs)} 项。阈值 0.01 mm³；小于此阈值不代表有生产装配公差。\n\n")
        for a in collisions:rows.append(f"- {a['name']}：与壳体 {a['shell_overlap_mm3']:.4f} mm³、与侧键 {a['caps_overlap_mm3']:.4f} mm³。需要调整件尺寸/位置或壳体。\n")
        for a in pairs:rows.append(f"- {a['a']} / {a['b']}：{a['overlap_mm3']:.4f} mm³，未解决，不能算完成适配。\n")
        for a in e['reservations']:
            if a['name']=='antenna_keepout_EST':rows.append(f"\n天线估计净空与壳体相交 {a['shell_overlap_mm3']:.4f} mm³；与电子件相交："+('；'.join(f"{h['part']} {h['volume_mm3']:.4f} mm³" for h in a['hits']) or '无')+'。这不是射频实测。\n')
        rows.append('\n允许接口：滚轮与轴、编码器与轴、电源开关滑块与本体、电池引线端点与电池。模型使用实体包络表示这些接口，仍须设计真实孔和接触面。电池服务净空包括电池、光学净空包括镜头、主键行程净空可能接近固定试握面，这些关系不能当作互不相交的独立物体。\n\n')
    write('reports/v06/ASSEMBLY_CHECKS.md','# V0.6 · 装配检查结论\n\n检查对象是模型内估计体，不是实际 ATK /PAW3950 板。模型尺寸表在 [电子参数 JSON](../../cad/electronics_v06.json)。\n\n'+''.join(rows)+'''## 为解决已发现干涉所做的布局调整

滚轮轴从 V0.5 的 Z17.5 降为 Z16.3 mm，固定试握件和两种电子示意同步调整。编码器改为 **4×6×7 mm 的可用空间目标**，尚未选到或验证真实编码器；若供体编码器更大，应改变滚轮/板/壳体布局。两主键开关沿 Y 向前 2 mm 以避开侧键板；充电区向内移动；供体 MCU 区域与天线区域分开；自定义板之间留出层间/平面间距。

下一轮仍需解决：真实板边界与孔位、安装托架、螺柱、上下盖闭合、主键弹性与行程、滚轮轴承/编码器支撑、侧键回位、USB 固定、线束固定和插拔路径。原板不能搬动的零件可能使这套布局不可行，需要改布局或壳体尺寸。

本轮没有完成连续装入路径、跌落/夹持强度、电池温升、固件、宏、RF/延迟或12小时续航测试。详见 [完整电子方案](ELECTRONICS.md)。
''')
    archive=ROOT/'README_V0.5.md'
    if not archive.exists():archive.write_bytes(subprocess.check_output(['git','show','ee4740639524cfde4e8b4c8cb39321150638cf51:README.md']))
    summary=f'''# Quietmirror · 右手指握鼠标

**当前 V0.6：除左侧双侧键及其接口外，外壳与底部沿中轴镜像；取消底部外伸托边，收窄后壳外围实面。本轮交付纯试握、ATK A1 Plus 主板示意、PAW3950 半组装主板示意三版。V0.1–V0.5 全部保留。**

![三个实际模型](views/v06/10_three_variants.png)

[全部历史版本](HISTORY.md) · [整个项目 ZIP](https://github.com/Quietmirror/github/archive/refs/heads/main.zip) · [设计与验证](reports/v06/DESIGN.md) · **[功能、续航和电子方案详解](reports/v06/ELECTRONICS.md)**

## 三个版本下载

| 版本 | 模型 | 用途与边界 |
|---|---|---|
| **纯试握模具 FIT** | **[STL](exports/v06/quietmirror_fingertip_V0.6_FIT.stl)** · [STEP](exports/v06/quietmirror_fingertip_V0.6_FIT.step) · [打印 3MF](exports/v06/quietmirror_fingertip_V0.6_PRINT.3mf) | 单一可打印实体，主键/侧键/滚轮固定；“模具”指手握外形样件，并非注塑阴模 |
| **ATK A1 Plus 替板示意** | **[彩色装配 STEP](exports/v06/quietmirror_V0.6_ATK_A1_PLUS_ESTIMATED.step)** · [多对象观察 3MF](exports/v06/quietmirror_V0.6_ATK_A1_PLUS_ESTIMATED_VIEW_ONLY.3mf) | 用户所称供体的估计空间布局；未确认型号、传感器、实板尺寸和固件能力 |
| **PAW3950 半组装板示意** | **[彩色装配 STEP](exports/v06/quietmirror_V0.6_PAW3950_CUSTOM_ESTIMATED.step)** · [多对象观察 3MF](exports/v06/quietmirror_V0.6_PAW3950_CUSTOM_ESTIMATED_VIEW_ONLY.3mf) | 分布式主控/RF/传感器板参考布局；不是已打样或已工作的电路 |

电子场景中的主板、电池等是独立物体，**不要整场景合并打印**。配套 [ATK 净空 STEP](exports/v06/quietmirror_V0.6_ATK_A1_PLUS_ESTIMATED_CLEARANCES.step)、[PAW3950 净空 STEP](exports/v06/quietmirror_V0.6_PAW3950_CUSTOM_ESTIMATED_CLEARANCES.step) 用于检查空间。

[开侧键孔壳体 STL](exports/v06/quietmirror_fingertip_V0.6_SHELL.stl) / [STEP](exports/v06/quietmirror_fingertip_V0.6_SHELL.step) · [前侧键 STL](exports/v06/side_button_1_V0.6_PRINT.stl) / [STEP](exports/v06/side_button_1_V0.6_PRINT.step) · [后侧键 STL](exports/v06/side_button_2_V0.6_PRINT.stl) / [STEP](exports/v06/side_button_2_V0.6_PRINT.step)。独立键帽还没有真实点击/回位验证。

可编辑源：[生成器](cad/build_v06.py)、[外形参数](cad/parameters_v06.json)、[逐孔生成](cad/vent_layout_v06.py)、[电子生成器](cad/electronics_v06.py)、[电子尺寸/摆位](cad/electronics_v06.json)、[复现方法](cad/PARAMETERS_V0.6.md)。

## 外形与减重

- **外部对称**：侧键以外，包括底筋、五脚、USB-C 开口和电源开关孔均按 X=0 镜像。取消旧右侧防拖地托边，尾脚收进外壳，底筋裁齐外形投影。本轮按新要求重新设计底部，不沿用 V0.5 的 Z≤6 mm 冻结约束。
- **12 个后壳孔**，4—3—4—1 镜像排列；外缘沿壳体轮廓，孔间直筋目标 2.2 mm，外围目标 2.4 mm。22 对相邻孔最短间距约 2.2 mm；尾部两个极短分区交汇圆角节点更宽，约 5.43 mm。侧键受力区保留局部加固，不能称“每一处都等宽”。
- 后壳外轮廓 D58.5–88.5 mm 的投影采样：到最近孔的距离最小 **{g['perimeter_rib']['min_mm']:.2f} mm**，中位 **{g['perimeter_rib']['median_mm']:.2f} mm**；节点处更宽。前部按键/侧键受力区不纳入此项。
- 后肩两段较陡的窄筋增加左右镜像的 **Ø2 mm 内侧补筋**，维持外表面孔间窄筋，不靠削薄关键受力处减重。内侧补筋会进入少量孔边投影：H05/H07 的边缘网格射线有 10/9 条遇到补筋，所有孔中央净开口的贯通检查通过。指肚主接触面保持完整。
- 实际尺寸，长×宽×高：**{xyz[1]:.3f}×{xyz[0]:.3f}×{xyz[2]:.3f} mm**。90×62×28 mm 是名义试握参数；自由曲面末端存在离散/放样偏差，切片器按实际包围盒核对。
- 前端中轴充电孔 **13.4×6.4 mm**；底部中心开关孔 **6×3 mm**。均为估计接口，待真实连接器/开关确认。

![V0.5 与 V0.6](views/v06/11_comparison.png)

## 已完成的验证与打印估计

FIT / SHELL / 两个独立侧键均为有效单实体，STL 封闭、单连通、法线一致，自相交面数 0。五脚 Ø8.8 mm，45 个脚底采样均在 Z=0。最终 FIT 在侧键区域之外的镜像面距离最大 **{g['symmetry']['final_fit_max_mirror_distance_mm']:.3f} mm**，是网格离散核对，不是假定全体都对称。

常规壳面 **{v['wall_check']['samples_taken']}** 个法向样本，最薄 **{v['wall_check']['min_mm']:.3f} mm**；窄筋另取 **{g['web_normal_chords']['count']}** 个样本，最薄 **{g['web_normal_chords']['minimum_mm']:.3f} mm**。有限采样不等于连续最薄壁或强度认证；FIT 侧键固定桥仍有局部 1.2 mm 特征。CAD 体积 **{c['volume_mm3']/1000:.3f} cm³**，STL 体积 **{v['mesh']['volume_mm3']/1000:.3f} cm³**。

0.4 mm 喷嘴、0.2 mm 层高、4 壁、20% gyroid、PLA 1.24 g/cm³，五脚朝下、仅热床贴合支撑、4 mm 裙边：**本体 {mass['model_g']:.3f} g，支撑 {mass['support_g']:.3f} g，总耗材 {total} g，约 {time}**。最终 3MF 不加载外部 INI 重切片，16 项设置一致；未实物打印、称重或夹持强度测试。详见 [打印说明](slicing/V0.6_PRINTING.md)、[网格/壁厚数据](reports/v06/validation.json)、[对称/孔/筋/底部检查](reports/v06/geometry_checks.json)。

## 电子目标与建议

两种方案都以 **400–6400 DPI、无线 1K、低延迟、宏、LOD、左右键/滚轮中键/双侧键、电源开关与 USB-C 充电**为验收目标；Motion Sync 等可选同步增强关闭。供体若不支持这些配置，单纯换壳不能补齐。未确认 ATK A1 Plus 的传感器，更没有假定它使用 PAW3950。

≥12 h 持续满性能的预算为：500 mAh ×75%÷30 mA = **12.5 h**。500 mAh 的容量与 26×30×6 mm 包络都是估计；需要真实电池、满性能持续电流和实际续航测试，**不是已达标承诺**。全部功能矩阵、镜头尺寸链、充电架构及待测清单见 [详细电子说明](reports/v06/ELECTRONICS.md)，干涉结果见 [装配检查](reports/v06/ASSEMBLY_CHECKS.md)。

**推荐下一步用 FreeCAD 继续真实装配**：导入 STEP，放入实测 PCB/镜头/电池，建立固定、行程和间隙。JSON/Python 仍保留外壳参数；STEP 不自动携带完整参数历史。本轮未安装建模软件，已提供交换模型。

[斜视](views/v06/01_isometric.png) · [俯视](views/v06/02_top.png) · [左侧](views/v06/03_left_side.png) · [右侧](views/v06/05_right_side.png) · [底视](views/v06/04_bottom.png) · [充电口](views/v06/06_front_charge.png) · [孔形图](views/v06/12_vent_layout.png) · [ATK 内部](views/v06/07_isometric.png) · [PAW3950 内部](views/v06/08_isometric.png) · [试握反馈](reports/v06/FIT_FEEDBACK.md)

## 来源与历史

原创代码与几何采用 [CERN-OHL-P-2.0](LICENSE)。[开源文件审阅与借鉴](references/REFERENCE_REVIEW.md)、[Fenrir 形态参考](references/FENRIR_REFERENCE.md)、[NOTICE](NOTICE.md) 保留。没有复制商业 CAD，也没有沿用 Kotinos 的 HSK Pro 孔位。V0.5 说明归档到 [README_V0.5.md](README_V0.5.md)。

手长约 230 mm、张开跨度约 190 mm 仍为照片 AR 近似值；190 mm 不是掌宽或握宽，未按手长等比例放大鼠标。掌宽、指节长度、实际握姿和本轮舒适度均待测。
'''
    write('README.md',summary)
    design=summary.replace('](views/','](../../views/').replace('](cad/','](../../cad/').replace('](exports/','](../../exports/').replace('](slicing/','](../../slicing/').replace('](reports/v06/','](').replace('](references/','](../../references/').replace('](HISTORY.md)','](../../HISTORY.md)').replace('](LICENSE)','](../../LICENSE)').replace('](NOTICE.md)','](../../NOTICE.md)').replace('](README_V0.5.md)','](../../README_V0.5.md)')
    write('reports/v06/DESIGN.md',design.replace('# Quietmirror · 右手指握鼠标','# V0.6 · 设计思路、三版模型与验证'))
    write('slicing/V0.6_PRINTING.md',f'''# V0.6 打印说明

打印文件：[FIT STL](../exports/v06/quietmirror_fingertip_V0.6_FIT.stl) 或 [带配置 3MF](../exports/v06/quietmirror_fingertip_V0.6_PRINT.3mf)。电子场景 VIEW_ONLY 不能作为整件打印板。

毫米、100%比例，长×宽×高 {xyz[1]:.3f}×{xyz[0]:.3f}×{xyz[2]:.3f}。五脚底面朝热床，Z=0；不要缩放来套入旧尺寸。切片器的包围盒结果在 [slicer_model_info](../reports/v06/slicer_model_info.txt)。

已用 PrusaSlicer 2.9.6 实际切片：0.4喷嘴、0.20层高、4壁、5顶/底层、20% gyroid、PLA 1.75/1.24 g/cm³、210°C喷嘴/60°C床。支撑采用 snug、仅从热床、45°阈值、Z间隙0.2、XY间隙0.35、3层界面；4 mm brim。打印前改成真实打印机与耗材配置。配置是估算用途，不附未知打印机可直接执行的 G-code。

支撑主要位于主键内侧、滚轮及其支架下、后壳顶面、侧键固定件下和充电口上沿。建议从开放底部与后孔分段移除支撑，不强扭2.2 mm窄筋。避免沿薄边撬动侧键；孔口和接触边缘去毛刺。

本体 {mass['model_g']:.3f} g，支撑 {mass['support_g']:.3f} g，裙边 {mass['adhesion_g']:.3f} g，总耗材 {total} g，{time}。这是切片估计；未实际打印/去支撑/称重。最终3MF无外部INI重切片，总重 {rt['embedded_3mf_estimate']['grams']} g、{rt['embedded_3mf_estimate']['time']}，16项设置一致，允许重复切片产生的小幅路径差异。

![最终切片层图](../views/v06/09_slice_layers.png)

独立侧键文件已摆为限位边朝下；其重量和时间见 [分件切片](../reports/v06/separate_parts_slice.json)。SHELL/独立侧键与FIT是不同选择，不要叠印。SHELL删除固定滚轮与支架，用于继续装配设计，不能把没有支撑的电子示意零件视为已经装牢。
''')
    write('reports/v06/FIT_FEEDBACK.md','''# V0.6 试握记录

手部数据仍是230 mm腕到中指尖、190 mm张开跨度的照片近似值；不是掌宽。先记录打印机、材料、方向、缩放、去支撑与脚贴厚度。

| 项目 | 记录 |
|---|---|
| 有效握宽 | 夹持点距前端位置、偏宽/偏窄、拇指及无名指压力点 |
| 顶掌 | 静止/移动/抬鼠时尾部是否碰掌；是否希望缩短或降低 |
| 手指拖地 | 取消托边后，无名指/小指是否拖垫，哪个位置最明显 |
| 滚轮触达 | 中指/食指滚动是否需改变握姿；本版轴降低1.2 mm后的感觉 |
| 双侧键 | 前后键触达、误碰、需移动拇指的距离 |
| 抬鼠稳定 | 低速、快速转向和反复抬鼠是否打滑；是否夹得更用力 |
| 窄筋与边缘 | 是否压手、毛刺、明显弹性或裂纹；去支撑是否困难 |
| 充电口/开关 | 插头胶壳触达、底部操作空间；示意接口不能代替实测插拔 |

本轮主键/侧键/滚轮固定，不评价真实点击力度、回弹和编码器手感。发现裂纹或强烈局部压痛后停止用力试握，记录照片与位置再改模型。没有以 AR 近似值伪造掌宽或指节数据。
''')
    print('Release documentation generated from saved verification reports',flush=True)
if __name__=='__main__':main()
