"""Write release documentation using measured V0.5 artifacts and reports."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'reports/v05'
def read(name):return json.loads((R/name).read_text(encoding='utf8'))
v=read('validation.json');c=read('cad_metrics.json');b=read('bottom_preservation.json')
sl=read('slice_summary.json');rt=read('3mf_roundtrip.json');sep=read('separate_parts_slice.json')
vent=read('vent_verification.json');layout=read('vent_layout.json');cmp=read('comparison_slice.json')
mass=sl['material_by_category_g'];foot=sl['footer'];dim=v['mesh']['dimensions_xyz_mm'];wall=v['wall_check'];web=vent['web_normal_chords']
baseproof='；'.join(f"{a['variant']}：旧减新 {a['old_minus_new_mm3']:.6f} / 新减旧 {a['new_minus_old_mm3']:.6f} mm³" for a in b['comparisons'])
download='''| 文件 | 用途 |
|---|---|
| **[一体试握 STL](exports/v05/quietmirror_fingertip_V0.5_FIT.stl)** · [STEP](exports/v05/quietmirror_fingertip_V0.5_FIT.step) | 一个连通实体；主键、侧键与滚轮触感件固定 |
| **[带切片配置的 3MF](exports/v05/quietmirror_fingertip_V0.5_PRINT.3mf)** | 毫米、100%比例、五脚朝下；使用前选择实际打印机 |
| [开侧键窗口 SHELL STL](exports/v05/quietmirror_fingertip_V0.5_SHELL.stl) · [STEP](exports/v05/quietmirror_fingertip_V0.5_SHELL.step) | 配合下列独立键帽；主键和滚轮仍固定 |
| [前侧键 STL](exports/v05/side_button_1_V0.5_PRINT.stl) · [STEP](exports/v05/side_button_1_V0.5_PRINT.step) | 内侧限位边朝下的打印部件 |
| [后侧键 STL](exports/v05/side_button_2_V0.5_PRINT.stl) · [STEP](exports/v05/side_button_2_V0.5_PRINT.step) | 同形部件，安装高度不同 |
| [壳体与两键帽装配 STEP](exports/v05/side_button_assembly_V0.5.step) | 三实体的装配位置，不用于叠印 |
| [主生成器](cad/build_v05.py) · [孔形生成器](cad/vent_layout_v05.py) · [参数 JSON](cad/parameters_v05.json) | 可编辑 CadQuery 源码；[参数与复现](cad/PARAMETERS_V0.5.md) |
| [16 个电子估计包络 STEP](exports/v05/electronic_envelopes_V0.5_ESTIMATES.step) | 估计尺寸和摆位，不参与打印，不代表装配已验证 |
'''
readme=f'''# Quietmirror · 右手指握鼠标

**当前 V0.5：后壳从 6 孔增加到 10 孔，孔间筋收窄为 2.2 mm，孔形随轮廓调整、左右镜像排列。V0.1–V0.5 全部保留。**

沿用 V0.4 的 Fenrir 方向外形：低前端、向后缓升主键和短低尾部。本轮只改后壳孔阵，单孔大小维持原来尺度，边缘孔分别收形，孔间筋更均匀。图为实际交付 STL 的渲染。

![V0.4 与 V0.5 实际俯视比较](views/v05/10_comparison.png)

**[全部历史版本](HISTORY.md)** · **[一次下载整个项目 ZIP](https://github.com/Quietmirror/github/archive/refs/heads/main.zip)**

## 当前模型下载

{download}
GitHub 文件页使用 **Download raw file** 下载。FIT 和 SHELL 是两种选择，不要叠在同一位置打印。整个项目下载包含生成器依赖的历史底部 STEP。

## 孔形和细筋具体变化

| 项目 | V0.4 | V0.5 |
|---|---|---|
| 孔数与排列 | 6，3—3 | **10，3—4—3 交错镜像排列** |
| 单孔面积，XY 投影 | 每孔 {vent['old']['single_hole_area_mm2']:.2f} mm² | **{vent['new']['area_range_mm2'][0]:.2f}–{vent['new']['area_range_mm2'][1]:.2f} mm²**；平均 {vent['new']['mean_area_mm2']:.2f} |
| 孔间筋 | 旧报告尖角基形最小 3.0 mm；实际圆角孔最小 {vent['old']['rounded_cutter_minimum_gap_mm']:.1f} mm | **19 对相邻孔最短平面间距均为 2.200 mm** |
| 孔形 | 等形圆角六边孔 | 中央较完整，肩部、侧缘和尾部孔单独裁形；孔角 R1.0 |
| 本体 PLA 切片估重，使用同一配置 | {cmp['old_model_g']:.3f} g | **{mass['model_g']:.3f} g**，减少 {cmp['model_saving_g']:.3f} g /{cmp['model_saving_percent']:.2f}% |
| 尺寸，长×宽×高 | 约 90×62×28 mm | **{dim[1]:.3f}×{dim[0]:.3f}×{dim[2]:.3f} mm** |
| 底部与五脚 | V0.3 冻结底部 | **整个 Z≤6 mm 区域不变** |

孔阵来自共享边界的分区，再对每个分区内缩 1.1 mm、做 R1.0 圆角；不是把所有孔缩小，也不是等距复制同一六边形。相邻直边因此保留一致筋距。多孔交汇节点、外围承力边框仍更宽，不能把 2.2 mm 理解为全表面任意方向都等厚。

![实际孔形与筋宽图](views/v05/14_vent_layout.png)

**对称范围**：主壳轮廓、左右主键、滚轮中心和后壳孔阵以 X=0 镜像。沿用先前右手设计，左侧两个拇指键及冻结的右侧托边仍单侧保留，**完整 FIT 实体并非全特征镜像对称**。孔阵左右镜像差面积小于 1e-8 mm²；保存后的上壳曲面另做 5,000 点镜像距离采样，最大约 {vent['symmetry']['crown_max_mirrored_surface_distance_mm']:.3f} mm，属于 STL 曲面离散误差范围。

## 已完成的核对

- FIT、SHELL、两个独立键帽：每件 STEP 有效且为一个实体；STL 封闭、单连通、法线一致，自相交面数 0。
- FIT {v['mesh']['faces']:,} 个三角面；五脚各测 9 点，共 45 点均在 Z=0。脚贴平台 Ø8.8 mm，参考约 Ø7–7.5 mm 同厚圆点脚贴。
- 常规壳面 {wall['samples_taken']} 个法向样本，最小 {wall['min_mm']:.3f} mm；另在细筋上检查 {web['count']} 点，最小 **{web['minimum_mm']:.3f} mm**，没有低于 1.6 mm 的样本。有限采样不是连续全表面最薄壁或强度认证；FIT 侧键固定桥仍有局部 1.2 mm 特征。
- 保存后的 FIT / SHELL 对冻结底部做双向布尔差：**{baseproof}**。
- 10 孔在上壳上的贯通射线检查通过，开孔与侧键加固座体积相交为 0；侧键配合间隙和离散装入路径均重新核对。
- CAD 体积 {v['step']['volume_mm3']/1000:.3f} cm³；STL 体积 **{v['mesh']['volume_mm3']/1000:.3f} cm³**，差 {v['volume_mesh_step_relative_error']*100:.3f}%。不把积分体积直接冒充耗材重量。

**打印估算**：0.4 mm 喷嘴、0.2 mm 层高、4 周壁、20% gyroid、PLA 密度 1.24。五脚朝下，贴合支撑（snug）仅从热床生成，4 mm 裙边。本体 **{mass['model_g']:.3f} g**，支撑 {mass['support_g']:.3f} g，总耗材 **{foot['filament used [g]']} g**，约 **{foot['estimated printing time (normal mode)']}**。最终 3MF 无外载 INI 重切片，16 项设置一致。尚未实物打印、去支撑、称重或测试夹持刚度。

**[详细设计思路](reports/v05/DESIGN.md)** · **[打印说明](slicing/V0.5_PRINTING.md)** · [孔形/筋宽/对称原始数据](reports/v05/vent_verification.json) · [几何验证](reports/v05/validation.json) · [试握反馈](reports/v05/FIT_FEEDBACK.md)

## 其他视图与电子边界

[斜视](views/v05/01_isometric.png) · [俯视](views/v05/02_top.png) · [左侧](views/v05/03_left_side.png) · [右侧](views/v05/05_right_side.png) · [底视](views/v05/04_bottom.png) · [尺寸](views/v05/07_dimensions.png) · [侧键分解](views/v05/11_side_buttons_exploded.png) · [侧键装入位置](views/v05/12_side_buttons_fitted.png) · [内部包络](views/v05/06_envelopes.png)

手长约 230 mm、张开跨度约 190 mm 来自照片 AR 近似测量。190 mm 不是掌宽或握宽，没有按手长整体缩放；掌宽、指节、实际握姿待测。90×62×28 mm /有效夹持约 {v['grip_width_samples'][1]['outer_span_mm']:.2f} mm 仍是试握假设。

电子目标仍为 PAW3950、2.4 GHz 无线 1000 Hz、左右键、中键/滚轮、两个拇指键。候选供体仅记为用户所称 **“ATK 蜻蜓 A1 Plus”**，型号、传感器版本、PCB 与孔位待确认。PAW3950 不代表统一主板；无线 1K 依赖主板、固件和匹配接收器。

16 个包络均保留尺寸依据与“估计”标注；电池、侧键板、主键机构、USB-C、天线等布局尚有待解决的干涉。光轴沿 Z，镜头高度待真实 PCB /镜头/底面/脚贴尺寸链确认。**当前是固定试握件与侧键接口原型，不是已能装电子元件的替换壳。** [电子包络、干涉和待测清单](reports/v05/ELECTRONICS.md)

## 来源与历史

原创源码、几何采用 [CERN-OHL-P-2.0](LICENSE)。已实际检查的 olliebella、Kotinos、paw3395-pcb 文件、结构借鉴和上游许可证见 [开源参考审阅](references/REFERENCE_REVIEW.md)。未沿用 HSK Pro 板孔位。

Fenrir 只使用实际查看过的 [官方外形图片](references/FENRIR_REFERENCE.md) 作形态参考，未取得或复制商业 CAD /STL；本轮在原创 V0.4 外壳上调整孔阵。商业图片保留外链，许可证不由本项目覆盖。[NOTICE](NOTICE.md)

V0.1–V0.4 的模型、专用源码、参数、图和验证报告全部保留。V0.4 README 另存 [README_V0.4.md](README_V0.4.md)，旧版可从 [HISTORY](HISTORY.md) 或提交历史取得。
'''
(ROOT/'README.md').write_text(readme,encoding='utf8')
holes='\n'.join(f"| {h['id']} | {h['seed_xd_mm'][0]:g}, {h['seed_xd_mm'][1]:g} | {h['width_mm']:.3f}×{h['length_mm']:.3f} | {h['area_mm2']:.3f} |" for h in layout['holes'])
design=f'''# V0.5 设计思路、孔形和证据

## 设计目标

用户要求孔间平面筋更窄，孔大小大致保留、数量增加，各孔随外壳裁形、筋宽更均匀，并保持布局对称。本版保留 Fenrir 方向的 V0.4 上壳轮廓、主键与滚轮位置、侧键接口及 Z≤6 mm 冻结底部，只修改后壳开孔。

“对称”按主壳、主键和孔阵的左右镜像实现；先前要求的右手拇指键、右托边继续保留。它们使完整 FIT 实体有功能性不对称，本项目不把整件冒称为全镜像设计。若需要所有附件也镜像，应另开底部版本，因为右托边属于冻结区域。

## 为什么采用 3—4—3 和不同孔形

旧版 6 个等形孔之间存在较宽的实面，简单等比放大孔容易先碰到肩部或尾部。本版采用三个交错分区：前排 3、中排 4、后排 3。中央孔较完整，中排最外两个孔顺着肩部拉长，尾部两个外侧孔斜收，顶部外侧孔为侧键座留出边缘空间。单孔面积 {vent['new']['area_range_mm2'][0]:.3f}–{vent['new']['area_range_mm2'][1]:.3f} mm²，对比原来 {vent['old']['single_hole_area_mm2']:.3f}；平均增大约 5.5%，没有靠把孔缩成密集小蜂窝增加数量。

步骤：对镜像的种子点做 Voronoi 半平面分区；裁入沿肩部和尾部设置的边界；每个分区向内退让 1.1 mm；生成真实 R1.0 CAD 圆弧；右侧孔成形后精确镜像到左侧；最后沿 Z 切穿上壳。孔角圆弧降低尖角，三向交汇节点自然较宽。外围边框承担夹持与侧键传力，保留比孔间筋更宽的余量。

孔阵边界由可编辑的六个右侧站位定义，前端位于距前 48 mm，尾端 79.5 mm，经过内缩后孔口约在距前 49.1–78.4 mm。它是为本版外壳和侧键避让设置的设计边界，不是用照片反推的精确模具尺寸。

![CAD 孔形与筋宽](../../views/v05/14_vent_layout.png)

| 孔编号 | 种子 X,D /mm | 圆角孔外接宽×长 /mm | XY 面积 /mm² |
|---|---|---|---:|
{holes}

编号从前排左到右、再向后。D 是距前端正距离，实际模型 Y=-D。宽长是实际圆角轮廓包围框，不是统一标称圆直径。所有原始轮廓点和邻接关系见 [vent_layout.json](vent_layout.json)。

## 筋宽与对称怎么核对

19 对真正相邻的分区逐对计算圆角孔轮廓间距离，范围 {layout['adjacent_web_range_mm'][0]:.6f}–{layout['adjacent_web_range_mm'][1]:.6f} mm。V0.4 旧报告的 3.0 mm 是尖角基形最小距；重新测量实际圆角切刀后最小为 {vent['old']['rounded_cutter_minimum_gap_mm']:.3f} mm。新版本的 2.2 mm 使用实际圆角轮廓，避免混用口径。

孔阵与镜像的平面差面积 {vent['symmetry']['planar_symmetric_difference_mm2']:.3e} mm²，属于数值误差。保存后上壳 STEP 转网格，5,000 点镜像后的最近曲面距离最大 {vent['symmetry']['crown_max_mirrored_surface_distance_mm']:.5f} mm，99分位 {vent['symmetry']['crown_percentile_99_mm']:.5f} mm；这是有限网格采样，不是解析曲面重合定理。10 孔共 {sum(a['ray_count'] for a in vent['hole_through_checks'])} 条内部垂直射线均穿过上壳孔口，未检测到未切穿点。

开孔与两个侧键加固座相交体积为 0，最近距离约 {c['design']['vent_guide_checks'][0]['minimum_cutter_distance_mm']:.3f} /{c['design']['vent_guide_checks'][1]['minimum_cutter_distance_mm']:.3f} mm。该距离是切刀到座体的空间距离，不能当作该处壁厚或强度；常规壳厚和孔间细筋厚度另行采样。

## 几何、最薄特征与底部

| 检查 | 保存后实际结果 |
|---|---|
| FIT 外接尺寸 XYZ /mm | {dim[0]:.6f}×{dim[1]:.6f}×{dim[2]:.6f} |
| FIT STEP | 有效，单实体；体积 {v['step']['volume_mm3']:.3f} mm³ |
| FIT STL | {v['mesh']['faces']:,} 面；封闭、单连通、法线一致、自相交 0；体积 {v['mesh']['volume_mm3']:.3f} mm³ |
| CAD /网格体积差 | {v['volume_mesh_step_relative_error']*100:.4f}%；保留测量差异 |
| 常规壳面法向厚度 | {wall['samples_taken']} 点，最小 {wall['min_mm']:.5f}，中位 {wall['percentiles_mm'][2]:.5f} mm |
| 孔间细筋法向厚度 | {web['count']} 点，最小 {web['minimum_mm']:.5f}，中位 {web['median_mm']:.5f} mm |
| 两组中小于 1.6 mm 的样本 | 0 |
| 局部固定小桥 | FIT 侧键固定桥名义 1.2 mm，保持原版；不是活铰链 |
| 侧键内限位边 | 名义厚 1.6 mm；键面边缘 R1.1 |
| 五脚平面 | 45 个检查点均为 Z=0，平台 Ø8.8 mm |
| SHELL 和两个键帽 | 各自 CAD 单实体有效、STL 单连通封闭、自相交 0 |

常规壁厚采样避开开孔边缘；另在 19 条孔间共享边界的 1/4、1/2、3/4 处检查 57 个法向弦厚度，专门覆盖细筋。两者都是有限点采样，不能声称连续全局最薄处全部大于 1.6 mm；边缘圆角和原有 1.2 mm 固定桥单列。没有做有限元、疲劳、跌落、实物夹持或扭转试验。

底部继续直接取 V0.3 STEP 的 Z≤6 mm 完整区域，包含五脚、外围与斜筋、传感器框、右托边、滚轮根部及下壳带。冻结区域检查：**{baseproof}**。Z=6 上下 0.01 mm，39 个站位外边变化最大 {b['skirt_joint']['max_sampled_outer_edge_change_mm']:.6f} mm。既有 0.6 mm 高过渡边及其顶部小台阶保留。

STL 线性偏差设置 0.02 mm、角度 0.15 rad。仅焊接近重复顶点和清除退化/重复面，没有补洞或丢弃组件来通过验证。所有验证针对导出的文件。[几何原始数据](validation.json) · [底部原始数据](bottom_preservation.json) · [孔与细筋原始数据](vent_verification.json)

## 侧键与电子空间

沿用窗口 12×6.6 mm、键面 10.8×5.4、限位边 13.2×6.2×1.6；前/后侧键中心距前 33/47，Z16.5/18.8。独立件与壳体静态相交为 0，最近间隙约 0.300 /0.217 mm。两条从底部送入、内向外就位的离散路径分别 48/57 个采样位置，相交为 0；没有连续扫掠或实物装配验收。FIT 把两键固定成同一个实体。

开孔变化不解决电子尺寸缺失。16 个估计包络重新与新壳求交，仍需实测“ATK 蜻蜓 A1 Plus”的供体身份、PCB、镜头、滚轮/编码器、侧键板、电池/插头、USB-C、电源开关与天线规范。主键和滚轮固定占位不能当作可动机构。[电子尺寸和干涉](ELECTRONICS.md) · [侧键路径](side_button_insertion.json)

## 切片与试握

同一最终 V0.5 配置重切 V0.4 与 V0.5，本体估重 {cmp['old_model_g']:.3f} →{mass['model_g']:.3f} g，减重 {cmp['model_saving_g']:.3f} g /{cmp['model_saving_percent']:.2f}%。本轮初始树状支撑报告了分支生成警告，因此交付配置改为贴合支撑（snug）；最终 FIT、SHELL、键帽和 3MF 重切片日志未再出现该警告。

本体 {mass['model_g']:.3f} g，支撑 {mass['support_g']:.3f} g，裙边 {mass['adhesion_g']:.3f} g，总 {foot['filament used [g]']} g /{foot['estimated printing time (normal mode)']}。3MF 单独重切为 {rt['embedded_3mf_estimate']['grams']:.2f} g /{rt['embedded_3mf_estimate']['time']}，保留实际差异。[打印说明](../../slicing/V0.5_PRINTING.md) · [同配置对比](comparison_slice.json)

重点试握：握宽、顶掌、无名指/小指拖地、滚轮/侧键触达、抬鼠稳定性；本轮另观察细筋是否发软、扭转、硌指和孔口去支撑是否容易。减薄后刚度必须由实物反馈验证。[反馈表](FIT_FEEDBACK.md)

## 版本和来源

本轮改动的几何参数只有 ventilation；version /notes 为记录字段。V0.1–V0.4 专用文件保持原内容，V0.4 README 归档，原 V0.4 切片结果不覆盖。原创代码和几何采用 CERN-OHL-P-2.0，沿用 [开源审阅记录](../../references/REFERENCE_REVIEW.md)、[Fenrir 图片参考说明](../../references/FENRIR_REFERENCE.md) 与 [NOTICE](../../NOTICE.md)。
'''
(R/'DESIGN.md').write_text(design,encoding='utf8')
printing=f'''# V0.5 打印说明

推荐 [FIT STL](../exports/v05/quietmirror_fingertip_V0.5_FIT.stl) 或 [3MF](../exports/v05/quietmirror_fingertip_V0.5_PRINT.3mf)。实际切片器尺寸 {dim[0]:.3f}×{dim[1]:.3f}×{dim[2]:.3f} mm、一个连通部件；100%比例、按毫米导入。独立键帽已按内侧限位边贴床摆正。

五个脚贴面朝下、Z=0。0.4 mm 喷嘴、0.2 mm 层高、4周壁、20% gyroid、5层顶底、PLA 1.24 g/cm³。210°C 喷嘴/60°C 热床是估算值，按实际打印机和材料配置调整。

使用 **贴合支撑 snug，仅从热床生成**，45°阈值、Z间隙0.2、XY间隙0.35、3层支撑界面、4 mm 裙边。初始有机树状支撑出现分支生成警告，最终改用此配置并重新验证。内部顶壳、轮轴和斜撑、固定侧键限位边等需要支撑，从开放底部去除。细筋和底筋是永久结构，不要当作支撑剪掉。[实际刀路图](../views/v05/09_slice_layers.png)

| 文件 | 本体 g | 支撑 g | 裙边 g | 总耗材 g | 时间 |
|---|---:|---:|---:|---:|---|
| FIT | {mass['model_g']:.3f} | {mass['support_g']:.3f} | {mass['adhesion_g']:.3f} | {foot['filament used [g]']} | {foot['estimated printing time (normal mode)']} |
'''
for a in sep['parts']:printing+=f"| {a['name']} | {a['model_g']:.3f} | {a['support_g']:.3f} | {a['adhesion_g']:.3f} | {a['total_g']:.2f} | {a['time']} |\n"
printing+=f'''
以上分件各自独立切片，不能直接作为同板打印的联合估时。模型 {sl['model_layers']} 层；含支撑中间层共 {sl['extrusion_z_planes_count']} 个挤出 Z 高度。PrusaSlicer 2.9.6。最终 3MF 不另加载 INI 重切片为 {rt['embedded_3mf_estimate']['grams']:.2f} g /{rt['embedded_3mf_estimate']['time']}，16项设置一致，与 STL+INI 差 {rt['difference']['grams']:.2f} g /{rt['difference']['time_seconds']} 秒。

3MF是通用估算配置。打开后选择实际打印机、喷嘴、热床范围和起止代码，再生成机用文件。仓库不提供可直接给未知机型执行的 G-code。

主键和滚轮固定，不要掰动；FIT侧键连接桥局部 1.2 mm，不是可反复弯折的铰链。清理 R1 孔口毛刺及下缘过渡，避免磨低五个脚贴基面。贴五个同厚 Ø7–7.5 mm 圆点脚贴后，放在平板检查晃动。独立键帽从底部送入再向外就位，临时用可移除胶带在内侧防掉；当前无回弹或真实开关机构。

没有实物打印、称重、变形或强度试验。[试握反馈表](../reports/v05/FIT_FEEDBACK.md) · [精简 INI](V0.5_PLA_0.4_0.20_ESTIMATE.ini) · [完整 INI](V0.5_PLA_0.4_0.20_FULL.ini) · [切片记录](../reports/v05/slice_summary.json) · [3MF 重切片](../reports/v05/3mf_roundtrip.json)
'''
(ROOT/'slicing/V0.5_PRINTING.md').write_text(printing,encoding='utf8')
print('Wrote README, DESIGN and PRINTING from V0.5 final data')
