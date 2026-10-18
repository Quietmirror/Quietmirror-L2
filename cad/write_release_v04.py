"""Publish-facing Chinese documentation from saved validation/slicing reports."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'reports/v04'
def read(name):return json.loads((R/name).read_text(encoding='utf8'))
v=read('validation.json');c=read('cad_metrics.json');b=read('bottom_preservation.json');sl=read('slice_summary.json');rt=read('3mf_roundtrip.json');sep=read('separate_parts_slice.json')
dims=v['mesh']['dimensions_xyz_mm'];wall=v['wall_check'];mass=sl['material_by_category_g'];foot=sl['footer'];modelv=v['mesh']['volume_mm3']/1000;cadvol=v['step']['volume_mm3']/1000
old=json.loads((ROOT/'reports/v03/slice_summary.json').read_text())['material_by_category_g']['model_g']
actual_grip=v['grip_width_samples'][1]['outer_span_mm']
capdist=[x['minimum_shell_distance_mm'] for x in v['side_cap_clearance']]
baseproof='；'.join(f"{r['variant']}：旧减新 {r['old_minus_new_mm3']:.6f} / 新减旧 {r['new_minus_old_mm3']:.6f} mm³" for r in b['comparisons'])
readme=f'''# Quietmirror · 右手指握鼠标

**当前版本 V0.4：参考游狼 Fenrir 的低前端与缓升主键，V0.3 底部不变。V0.1–V0.4 全部保留。**

这是可编辑、可3D打印的右手 fingertip / fingergrip 试握项目。V0.4实际查看了 [Fenrir Pro / Asym 官方图片](references/FENRIR_REFERENCE.md)，重新设计上部轮廓；主键和夹持面保持完整，后壳改为6个较大的圆角六边窗口。图中是实际STL渲染。

![V0.4 实际模型](views/v04/01_isometric.png)

**[全部历史版本与下载表](HISTORY.md)** · **[一次下载整个项目 ZIP，含所有版本](https://github.com/Quietmirror/github/archive/refs/heads/main.zip)**

## 当前版本下载

| 文件 | 用途 |
|---|---|
| **[一体试握 FIT STL](exports/v04/quietmirror_fingertip_V0.4_FIT.stl)** · [STEP](exports/v04/quietmirror_fingertip_V0.4_FIT.step) | 优先试握：主键、滚轮、两侧键固定，一个连通实体 |
| **[带估算配置的 3MF](exports/v04/quietmirror_fingertip_V0.4_PRINT.3mf)** | 脚面朝下、毫米、100%比例、已居中；打开后选择实际打印机 |
| **[开侧键窗口的 SHELL STL](exports/v04/quietmirror_fingertip_V0.4_SHELL.stl)** · [STEP](exports/v04/quietmirror_fingertip_V0.4_SHELL.step) | 配下方两个独立键帽；主键和滚轮仍固定 |
| [前侧键 STL](exports/v04/side_button_1_V0.4_PRINT.stl) · [STEP](exports/v04/side_button_1_V0.4_PRINT.step) | 已按内侧限位边朝下摆好 |
| [后侧键 STL](exports/v04/side_button_2_V0.4_PRINT.stl) · [STEP](exports/v04/side_button_2_V0.4_PRINT.step) | 同形独立部件，安装高度与前键不同 |
| [壳体 + 两键帽装配位置 STEP](exports/v04/side_button_assembly_V0.4.step) | 三个实体的相对位置；不是叠在一起打印的文件 |
| [可编辑 CadQuery 源码](cad/build_v04.py) · [参数 JSON](cad/parameters_v04.json) | [参数、坐标和复现说明](cad/PARAMETERS_V0.4.md)；依赖源码随项目提供 |
| [16个电子估计包络 STEP](exports/v04/electronic_envelopes_V0.4_ESTIMATES.step) | 不参与打印，不代表真实供体尺寸或可装配 |

GitHub文件页可用 **Download raw file** 下载；STL按毫米导入。FIT与SHELL是两种用途选项，不要叠在同一位置打印。

## 这次改了什么

![V0.3 / V0.4 同视角侧面对比](views/v04/10_comparison.png)

| 项目 | V0.3 | V0.4 |
|---|---|---|
| 整体尺寸，长×宽×高 | 约90×62×31 mm | **{dims[1]:.3f}×{dims[0]:.3f}×{dims[2]:.3f} mm** |
| 鼻部壳顶参考高度 | 22 mm | **12 mm**，主键面向后缓升 |
| 壳背峰值位置 | 距前约30 mm | 距前约44 mm；末端继续短低 |
| 固定滚轮顶部 | 31 mm | **25 mm**，上部支撑收进壳内 |
| 后壳窗口 | 10个9×9六边孔 | **6个12×11外接框圆角六边窗口**，名义最小平面筋距3 mm |
| 侧键 | 前后中心Z19.2 | **前Z16.5 /后Z18.8**，纵向仍为距前33/47；键帽同形 |
| 中心夹持截面，距前46 /Z13 | 53.606 mm | **{actual_grip:.3f} mm**；仍是试握假设 |
| 五脚、底筋、传感器框、右托边 | V0.3结构 | **整个Z≤6 mm区域原样保留** |
| PLA本体切片估重 | {old:.3f} g | **{mass['model_g']:.3f} g** |

底部由已交付V0.3 STEP直接提取；上方增加0.6 mm高过渡边，再连接新壳。保存后的FIT和SHELL都做了冻结区域双向布尔差检查：**{baseproof}**。不是只比较五个脚的位置。[底部检查原始数据](reports/v04/bottom_preservation.json)

## 验证与打印估算

- 四个单件（FIT、SHELL、前键、后键）均为有效STEP单实体；STL单连通、封闭、法线一致、自相交0。
- FIT共{v['mesh']['faces']:,}个三角面，五脚各测9点，45点均位于Z=0。脚贴平台Ø8.8，适配约Ø7–7.5的同厚圆点脚贴。
- 常规壳面法向采样{wall['samples_taken']}点：最小{wall['min_mm']:.3f} mm，中位{wall['percentiles_mm'][2]:.3f} mm；不是全表面的连续最薄壁证明。侧键内限位边1.6 mm；FIT固定小桥局部为1.2 mm。
- CAD积分体积约{cadvol:.3f} cm³；打印STL体积{modelv:.3f} cm³，差{v['volume_mesh_step_relative_error']*100:.3f}%。切片重量来自实际刀路，而非把CAD实体体积直接当耗材量。
- 独立键帽与壳体无静态体积相交，最近间隙约{capdist[0]:.3f}/{capdist[1]:.3f} mm；装入路径离散核对记录见报告，仍需实物配合验证。

0.4 mm喷嘴、0.2 mm层高、4周壁、20% gyroid、5层顶底、PLA密度1.24。五脚面朝下，有机支撑仅从热床生成，4 mm裙边。**FIT本体 {mass['model_g']:.3f} g，支撑 {mass['support_g']:.3f} g，含支撑/裙边总计 {foot['filament used [g]']} g，估时 {foot['estimated printing time (normal mode)']}。** 最终3MF另行重切片得到{rt['embedded_3mf_estimate']['grams']:.2f} g；16项关键设置一致。没有实物打印、去支撑、称重或强度试验。

**[详细设计思路与验证](reports/v04/DESIGN.md)** · **[打印说明及分件估算](slicing/V0.4_PRINTING.md)** · [全部几何数据](reports/v04/validation.json) · [试握反馈表](reports/v04/FIT_FEEDBACK.md)

## 视图与侧键

[俯视](views/v04/02_top.png) · [左侧](views/v04/03_left_side.png) · [底视](views/v04/04_bottom.png) · [右侧](views/v04/05_right_side.png) · [尺寸图](views/v04/07_dimensions.png) · [冻结底部单独显示](views/v04/13_frozen_bottom.png)

![侧键部件](views/v04/11_side_buttons_exploded.png)

独立侧键从底部送入内腔，再由内向外放入窗口；内侧限位边防止向外脱落，临时试握可用可移除胶带从内侧防止向内掉落。当前没有弹簧、开关支座或已验证行程，不能评价真实点击力度与回弹。[半透明装配图](views/v04/12_side_buttons_fitted.png)

## 手部与电子装配边界

手长约230 mm、张开跨度约190 mm来自照片的近似AR测量。**190 mm不是掌宽或鼠标握宽**；没有按手长整体缩放，掌宽、指节和实际握姿仍未知。原90×62×31 /约54 mm握宽是试握起点；V0.4把上部降低到约28 mm，必须靠试握反馈判断是否合适。

电子目标仍为PAW3950、2.4 GHz无线1000 Hz、左右主键、中键/滚轮和两侧键。供体仅记为用户所称 **“ATK 蜻蜓 A1 Plus”**，准确型号、传感器版本、PCB和孔位待确认。PAW3950不规定统一板型；无线1K依赖主板、固件和匹配接收器。

本版低前端会影响主键开关和编码器高度；电池、侧键板、USB-C及天线布局也未解决。16个参考框全部按估计标注，没有设置假装配孔。光轴沿Z，真实镜头高度须按PCB、镜头、底面、脚贴的尺寸链确定。**当前文件用于外形和触达试握，尚不能作为可装电子元件的替换壳。**

[电子包络与待测尺寸](reports/v04/ELECTRONICS.md) · [内部包络图](views/v04/06_envelopes.png) · [包络尺寸表](views/v04/08_envelope_layout.png)

## 源码、历史和署名

[复现步骤](cad/PARAMETERS_V0.4.md) · [Python依赖](requirements.txt) · [全部历史版本](HISTORY.md)。V0.4依赖的V0.3底部STEP也已包含在仓库，下载整个项目可直接取得。

原创模型与源码采用 [CERN-OHL-P-2.0](LICENSE)。已查看的olliebella、Kotinos和paw3395-pcb源文件及上游许可证见 [开源参考审阅](references/REFERENCE_REVIEW.md)；没有沿用HSK Pro孔位。Fenrir为商业外形参考，本轮未取得它的CAD/STL，也未复制网格。官网图保留外链和署名；本项目许可证不覆盖它们。[完整NOTICE](NOTICE.md)
'''
(ROOT/'README.md').write_text(readme,encoding='utf8')
design=f'''# V0.4 设计思路与验证

## 1. 目标与保留项

用户要求“参照fenrir-wireless-mouse改进模型，底部不变，并把所有历史版本一并上传”。本轮以 [Fenrir Pro / Asym 的六张实际查看图片](../../references/FENRIR_REFERENCE.md) 为视觉依据，调整上部轮廓。保留主要指肚接触面、平顺侧面、右侧低托边和独立侧键原型；没有对商用品按比例描摹或假设其结构能用同样厚度FDM打印。

前端降低让主键成为向后缓升的触面，壳背最高位置后移约14 mm。保留90 mm底部长度，因此不能同时照搬Fenrir 75/81.7 mm的整机长度。后壳采用更少但更大的六边窗口；孔间、外围和主键后端仍有连续传力材料。主键与侧握区不布密孔。

前/后侧键纵向仍为距前33/47 mm，但中心高度分别从19.2改到16.5/18.8，以避开降低后的上壳内侧。键帽尺寸不变。滚轮顶从31降到25，轮轴与上部斜撑也重新布置；轮架根部保留。

## 2. 底部如何保证不变

源：`exports/v03/quietmirror_fingertip_V0.3_SHELL.step`。冻结整个 **Z≤6 mm** 区域，包含五脚、外围底筋、四条斜筋、传感器框、右托边、轮架根部和下壳带。V0.4仅在冻结平面上方增加0.6 mm过渡边并连接新上壳。底部并非重画的近似件。

对最终保存STEP分别截取同一区域，做旧减新、新减旧、交集体积和范围核对：

- {baseproof}。
- 接口Z=6上下0.01 mm处，39个纵向站位外边变化最大{b['skirt_joint']['max_sampled_outer_edge_change_mm']:.6f} mm；这不是整个曲面的光顺连续性证明。
- 过渡边顶Z=6.6附近保留小台阶，来自底部冻结与上壳略收窄的取舍；试握须检查是否硌指，轻修毛刺不应磨五脚面。
- 五个平台Ø8.8，中心与周边8点共45点均在Z0。贴上脚贴后需检查首层误差和脚贴厚度，数字共面不替代实物共面。

详细机器记录：[bottom_preservation.json](bottom_preservation.json)。底视图能穿过孔看到上壳变化，因而整张底视图不是逐像素相同；冻结部分的实体几何才是比较对象。

## 3. CAD、网格和壁厚

CadQuery源码及JSON均可编辑；STEP是有效B-rep，STL为0.02 mm线性偏差、0.15 rad角度设置导出的毫米网格。焊接容差0.000001 mm，移除退化/重复三角面；没有补洞、丢弃零散实体或通过切片器自动修复掩盖问题。

| 检查 | 结果 |
|---|---|
| FIT尺寸，XYZ | {dims[0]:.6f} × {dims[1]:.6f} × {dims[2]:.6f} mm |
| FIT三角面 | {v['mesh']['faces']:,} |
| FIT/SHELL/两个键帽 | 每件STEP有效、一个实体；STL封闭、一个连通分量、法线一致、自相交0 |
| CAD体积 | {cadvol:.6f} cm³，积分容差参数1e-9 |
| STL体积 | {modelv:.6f} cm³ |
| 两种体积差异 | {v['volume_mesh_step_relative_error']*100:.4f}%，保留实际差异 |
| 常规壳面壁厚 | {wall['samples_taken']}点；最小{wall['min_mm']:.5f}，中位{wall['percentiles_mm'][2]:.5f} mm |
| 小于1.6 mm的常规壳面样本 | {wall['under_1_6_mm']} |
| 独立侧键内限位边 | 名义1.6 mm |
| FIT侧键固定小桥 | **局部1.2 mm**，仅固定触感位置 |
| 孔间平面筋距 | {v['vent_planar_web_mm']:.3f} mm；曲面上实际路径更长，不等于任意方向截面强度 |

壁厚采样沿原始外表面法线，避开底部、端缘、开孔、主键窄缝及侧键过渡附近。边缘附近的斜向短弦不当作法向壁厚。它是有限采样，不是连续全表面最小壁厚证明。没有做有限元、跌落、疲劳或真实夹持刚度测试。

原始记录：[validation.json](validation.json)、[cad_metrics.json](cad_metrics.json)、[切片器尺寸](slicer_model_info.txt)。

## 4. 侧键部件与装入路径

窗口12×6.6；键面10.8×5.4；导向段8.6×3.8；内限位边13.2×6.2×1.6。前/后键与壳体的静态最小间隙分别{capdist[0]:.5f}/{capdist[1]:.5f} mm，布尔相交体积为0。打印误差会改变实际间隙；不得凭这个结果保证直接装入无需修整。

从底部中前开口送入，留在内部空间，先前后定位，再抬至侧键窗口高度，最后向外就位。建议路径按≤1.5 mm间隔做CAD离散相交检查，包含另一键已就位的情况。检查通过也不等于连续扫掠、手指工具可达或实物装配验收。[路径原始结果](side_button_insertion.json)

SHELL+独立键帽是接口原型，内侧可移除胶带临时防掉。没有设计真实弹簧、开关行程、预压或回弹。FIT版仍是一个实体，全部触感部位固定。

## 5. 打印和材料

使用PrusaSlicer 2.9.6实际切片。0.4 mm喷嘴 /0.2 mm层高 /4周壁 /20% gyroid /5层顶底。脚面朝下，仅热床有机支撑，4 mm裙边。FIT本体{mass['model_g']:.3f} g，支撑{mass['support_g']:.3f} g，裙边{mass['adhesion_g']:.3f} g，总计{foot['filament used [g]']} g，{foot['estimated printing time (normal mode)']}。比V0.3本体减少{old-mass['model_g']:.3f} g（{(old-mass['model_g'])/old*100:.1f}%）。

3MF内嵌完整估算配置，导出后不另加载INI重新切片，关键设置16项一致。重量差{rt['difference']['grams']:.2f} g、时间差{rt['difference']['time_seconds']}秒，保留实际差异。[打印说明](../../slicing/V0.4_PRINTING.md)、[刀路图](../../views/v04/09_slice_layers.png)、[3MF核对](3mf_roundtrip.json)

## 6. 试握与下一轮

优先比较握宽、低前端是否自然、壳背是否顶掌、右手指是否拖地、降低后的滚轮/侧键触达，以及抬鼠稳定性。[反馈表](FIT_FEEDBACK.md)

主板、镜头、编码器、侧键板、电池/插头、线束、USB-C、电源开关和天线均有独立估计包络。低前端增加了对主键开关和编码器布局的限制。当前无装配孔、镜头止口或真实光学高度，候选供体“ATK 蜻蜓 A1 Plus”的实际型号和PAW3950身份未确认。[具体干涉与待测尺寸](ELECTRONICS.md)

## 7. 历史版本

V0.1、V0.2、V0.3的模型、版本专用源码、参数、切片报告和图未被覆盖；V0.3原README另存为README_V0.3.md。共享帮助脚本只增加0.4入口，保留旧版本入口。[全部版本与整包下载](../../HISTORY.md)
'''
(R/'DESIGN.md').write_text(design,encoding='utf8')
printing=f'''# V0.4 打印说明

首轮推荐 [FIT一体STL](../exports/v04/quietmirror_fingertip_V0.4_FIT.stl) 或 [3MF项目](../exports/v04/quietmirror_fingertip_V0.4_PRINT.3mf)。模型按毫米、100%比例。切片器实际尺寸{dims[0]:.3f}×{dims[1]:.3f}×{dims[2]:.3f}，识别一个连通部分。

## 方向与配置

五个脚贴粘贴面朝下、Z=0；不要把外壳侧面贴床。0.4 mm喷嘴、0.20 mm层高、4周壁、20% gyroid、5层顶底；PLA密度1.24 g/cm³。210°C喷嘴/60°C热床只是当前估算配置值，按实际耗材和打印机调整。内侧限位边朝下的两个键帽已摆好方向。

有机支撑仅从热床生成、45°阈值，Z间隙0.2、XY间隙0.35、3层支撑界面、4 mm外裙边。需要支撑的位置包括内顶壳、固定轮轴/斜撑、侧键内限位边和低托边；切片器按实际模型生成支撑，见[刀路截面](../views/v04/09_slice_layers.png)。

3MF内含通用估算配置，不是某台打印机的生产配置。打开后选择自己的机型和喷嘴，检查热床范围、起止G-code和支撑，再生成实际机用文件。仓库不发布未知机型可直接执行的G-code。

## 实际切片估算

| 文件 | 本体 g | 支撑 g | 裙边 g | 总耗材 g | 时间 |
|---|---:|---:|---:|---:|---|
| FIT | {mass['model_g']:.3f} | {mass['support_g']:.3f} | {mass['adhesion_g']:.3f} | {foot['filament used [g]']} | {foot['estimated printing time (normal mode)']} |
'''
for item in sep['parts']:
    printing+=f"| {item['name']} | {item['model_g']:.3f} | {item['support_g']:.3f} | {item['adhesion_g']:.3f} | {item['total_g']:.2f} | {item['time']} |\n"
printing+=f'''
PrusaSlicer 2.9.6，{sl['layers']}层。上表各分件独立切片，不等于全部零件放在同一热床的联合估时。最终3MF重切片：{rt['embedded_3mf_estimate']['grams']:.2f} g /{rt['embedded_3mf_estimate']['time']}；与STL+INI估算差{rt['difference']['grams']:.2f} g、{rt['difference']['time_seconds']}秒。没有实物称重。

## 去支撑与验收

从开放底部去除支撑，先区分有机支撑和永久底筋。勿剪五脚连接筋、传感器框或轮架根部；主键和滚轮不能掰动。清理后壳孔口、键面窄缝和底边过渡毛刺，避免打磨五个粘贴基面导致不共面。

侧键窗口和内限位边可能需轻修。独立键帽由底部进入内腔后向外就位，内侧可移除胶带临时防掉；不存在已验证的回弹机构。FIT局部固定桥1.2 mm，不要把它当可反复弯折的活铰链。

贴五个同批同厚Ø7–7.5 mm圆点脚贴后放平板检查晃动，再填写[试握反馈表](../reports/v04/FIT_FEEDBACK.md)。本件仅测试外形、触达和抬鼠稳定性，不用于评价点击力、回弹、滚轮阻尼、无线延迟或电子件重心。

配置：[精简INI](V0.4_PLA_0.4_0.20_ESTIMATE.ini) /[完整INI](V0.4_PLA_0.4_0.20_FULL.ini)；数据：[切片报告](../reports/v04/slice_summary.json) /[分件报告](../reports/v04/separate_parts_slice.json) /[3MF核对](../reports/v04/3mf_roundtrip.json)。
'''
(ROOT/'slicing/V0.4_PRINTING.md').write_text(printing,encoding='utf8')
print('Updated README, DESIGN and PRINTING from final reports')
