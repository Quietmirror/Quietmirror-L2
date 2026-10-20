# Quietmirror L2 r4

**CAD_COMPLETE / HARDWARE_PENDING**

侧键托架在生成 BODY 时一体成形，开关背挡拆分为两件可装入零件，键帽改为直线装入。交付包含独立组件 STEP/FCStd、9 个打印件、单盘及 F2 试验 3MF、可编辑源码、原始数值报告和真实模型视图。

| 门槛 | 结论 | 关键实测/仿真数据 |
| --- | --- | --- |
| G1 | COMPLETED | 9/9 单一有效实体；9/9 闭合网格；自相交面 0 |
| G2 | COMPLETED | 静态分类 369 项；未解决 0；硬件逐对 3570 项 |
| G3 | COMPLETED | 电池最小净空 0.600 mm；线束 672 项；预留区侵入 0 项 |
| G4 | COMPLETED | 六孔各 200 边界点 + 1000 棱柱点；未分类失败 0 |
| G5 | COMPLETED | LEFT_KEY: 25 姿态；RIGHT_KEY: 25 姿态；WHEEL_CARRIER: 23 姿态；SIDE_FRONT_KEY: 33 姿态；SIDE_REAR_KEY: 33 姿态 |
| G6 | COMPLETED | 四件路线 836 姿态；键帽直推 82 姿态；工具可达 4 项 |
| G7 | COMPLETED | H 独立组件 94；D 状态 DONOR_PENDING |
| G8 | COMPLETED | 18 个实际求解；最低 R3.2 刚度比 104.41% |
| G9 | COMPLETED | S1=True；S2=True；S3=True；S4=True；S5=True；S6=True；S7=True；S8=True；S9=True |
| G10 | COMPLETED | PA12 密度估计 17.796 g；实际单盘切片 36.04 g / 5h 18m 13s |
| G11 | COMPLETED | 压盘覆盖余量 {'SIDE_FRONT_KEY': 0.09820000000000004, 'SIDE_REAR_KEY': 0.13830000000000003}；PET 厚度范围 [0, 0.7] mm；外向止挡 {'SIDE_FRONT_KEY': 0.0, 'SIDE_REAR_KEY': 0.0} |

电子布局采用C17自制编码器转接板参考轮廓和14×20×6mm估计电池；原18×22×6mm电池尚未找到通过路线。所选电池包络体积减少29.29%，容量和12小时续航均未验证。真实供体主板仍为DONOR_PENDING。

![实际六视图](https://raw.githubusercontent.com/Quietmirror/Quietmirror-L2/L2-r4/views/l2_r4/L2_r4_H_SIX_VIEWS_SHEET.png)

## 参考差异和证据范围

精确值仅对应声明的模型与离散姿态；封闭网格、线弹性模拟和参考电子包络均不等于实物装配/打印强度/电子性能认证。

根部刚度偏差来自正文与作者脚本加载区间不同，夹持和粗网格指压B偏差通过匹配工况的作者 V2 几何控制计算调查，比较包含几何引起的网格变化。完整数值与修正理由见 handoff/l2_r4/INTERNAL_COMPONENTS_SIMULATION.md 和 TUNING_LOG.md。

## HARDWARE_PENDING

1. 实物侧键：贴膜调整、通断测试、手感
2. 实测按压力
3. D2F-01F 实物的 FP / OP / TTP
4. PAW3950 实际镜头高度
5. D 方案供体型号确认和主板测绘（DONOR_PENDING）
6. 无线、续航、DPI、宏等功能验证
7. 打印实物的称重和试装

保留 CERN-OHL-P-2.0 与 NOTICE 署名。L2-r3 tag、Release、作者证据分支和全部历史提交保持保留。
