# Quietmirror L2-r4

**CAD_COMPLETE / HARDWARE_PENDING**

右手指握轻量鼠标的可编辑机械设计。r4将侧键托架与BODY一体生成，保留原六孔、底部外轮廓与五个脚贴平台；中键内部端子孔作局部净空修正。两件独立挡板、直推式杠杆侧键和钢销支持后续实物装配。电子元件均明确标为估计包络。

![实际模型六视图](views/l2_r4/L2_r4_H_SIX_VIEWS_SHEET.png)

## Dremel 3D45 / PLA 打印交付

已使用 **Dremel 3D Slicer 2.3.2** 完成专用切片与软件校验；实机试印待完成。此次沿用既有 L2-r4 几何，提供整盘和装配姿态两种 STL。

- [3D45 / PLA 完整下载包（预发布）](https://github.com/Quietmirror/Quietmirror-L2/releases/tag/L2-r4-3D45-PLA)
- [九件整盘 STL](models/L2_r4_3D45_PLA/L2_r4_ALL_PARTS_PRINT_PLATE.stl) / [整体装配 STL](models/L2_r4_3D45_PLA/L2_r4_WHOLE_ASSEMBLED_PRINTABLES.stl)
- [Dremel 切片工程 3MF](models/L2_r4_3D45_PLA/L2_r4_3D45_PLA_PLATE.3mf) / [3D45 打印 G-code](models/L2_r4_3D45_PLA/L2_r4_3D45_PLA_PLATE.gcode)
- [详细打印、支撑与装配说明](cad/l2_r4_3d45/README.md) / [实际软件验证报告](models/L2_r4_3D45_PLA/PRINT_VALIDATION.json)

0.4 mm 喷嘴、0.2 mm 层高、PLA 220/45°C；九件共 **35.05 g、约 7 小时 2 分钟、128 层**，含支撑和 brim。整体 STL 是装配预览；实际打印使用整盘文件。没有将电子参考包络作为塑料件一起打印。原生工程不含软件渲染缩略图，下面的预览直接从交付 G-code 绘制。

![3D45实际切片路径](models/L2_r4_3D45_PLA/PRINT_PATH_VERIFIED.png)

## 下载和复现

- [完整H装配 STEP](models/L2_r4/FULL_ASSEMBLY_H.step) / [FreeCAD FCStd](models/L2_r4/FULL_ASSEMBLY_H.FCStd)
- [九件单盘打印3MF](models/L2_r4/L2_r4_H_ALL_PARTS_SINGLE_PLATE.3mf) / [逐件STL与STEP](models/L2_r4/parts) / [F2侧键试验件](models/L2_r4/SIDE_MODULE_F2_TRIAL.3mf)
- [D供体可用板域](models/L2_r4/D_MAX_BOARD_ENVELOPE.step) / [参数化源码和复现说明](cad/l2_r4/README.md)
- [G1–G11门槛总表](handoff/l2_r4/GATES.md) / [全部数值与版本身份](handoff/l2_r4/FINAL_ACCOUNTING.json)
- [设计思路](handoff/l2_r4/DESIGN_RATIONALE.md) / [装配顺序](handoff/l2_r4/ASSEMBLY_SEQUENCE.md) / [干涉报告](handoff/l2_r4/INTERFERENCE_REPORT.md)
- [结构有限元](handoff/l2_r4/INTERNAL_COMPONENTS_SIMULATION.md) / [真实切片和方向](handoff/l2_r4/SLICE_REPORT.md) / [所有修正记录](handoff/l2_r4/TUNING_LOG.md)

9件打印件的CAD聚合物体积为17619.919mm³，按PA12密度1.01g/cm³估计17.796g。原始 r4 通用 PLA 切片为36.04g、5h 18m 13s；它作为历史文件保留。请使用上方新的 3D45 专用打印包。切片质量包含支撑等耗材，不是装好电子件后的整机重量。

## 电子方案与证据范围

H采用PAW3950半组装主板的参考包络，C17编码器转接板是自制板形假设。所选电池包络为14×20×6mm；原18×22×6mm估计包络的有限搜索尚未找到合格拆装路线。电池缩小不代表容量已知或12小时续航达标。D供体仍为用户称为ATK A1 Plus的待确认型号；没有编造真实PCB孔位。

精确CAD结果对应报告中声明的模型与有限离散姿态，不等于连续运动证明、实物公差或电子功能认证。打印后反馈握宽、顶掌、手指拖地、滚轮/侧键触达与抬鼠稳定性，再测试实物按键和电子功能。

## HARDWARE_PENDING

1. 实物侧键：贴膜调整、通断测试、手感
2. 实测按压力
3. D2F-01F 实物的 FP / OP / TTP
4. PAW3950 实际镜头高度
5. D 方案供体型号确认和主板测绘（DONOR_PENDING）
6. 无线、续航、DPI、宏等功能验证
7. 打印实物的称重和试装

## 历史与许可

[L2-r3预发布记录](https://github.com/Quietmirror/Quietmirror-L2/releases/tag/L2-r3)、[r3文档](handoff/l2_r3)、[r2复核](handoff/l2_r2/README.md)、[r1复核](cad/l2_r1/README.md)及R3.2源文件均保留。原始工程另见[Quietmirror/github](https://github.com/Quietmirror/github)。沿用[CERN-OHL-P-2.0](LICENSE)、[NOTICE](NOTICE.md)和[本轮实际来源说明](cad/l2_r4/ATTRIBUTION.md)。
