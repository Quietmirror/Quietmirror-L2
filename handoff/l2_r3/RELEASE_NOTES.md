# Quietmirror L2 r3 — INCOMPLETE

此版本是预发布：G2 INCOMPLETE; G3 INCOMPLETE; G4 INCOMPLETE; G5 INCOMPLETE; G6 INCOMPLETE; G7 INCOMPLETE; G8 3D_FEM_BLOCKED; G9 INCOMPLETE; G11 UNVERIFIED。不能当作已认证装配、无线功能或实物侧键通过的版本。

按新r3方案重建原R3.2：保留六孔与五脚基准，改杠杆侧键和可拆载架，主键局部减薄加筋、滚轮改辐条结构。提供H整机、D供体占位、分件STEP/STL、可编辑源、FreeCAD装配和单盘3MF，以及实际CAD六视图、内部图和独立检查数据。

| 门槛 | 结果 | 证据 |
|---|---|---|
| G1 | PASS | 8 个打印件；CAD 单实体、自相交和封闭网格见 solids.json |
| G2 | INCOMPLETE | 打印件 28/28 对；穿模 0 对；不足目标间隙 1 对 |
| G3 | INCOMPLETE | 最终装配包络检查 248 对，其中 3 项未满足通用阈值；作者 62 项原始证据未提供 |
| G4 | INCOMPLETE | O3 贯通：True；原六孔多边形保留，最终曲面边界等价性未完整证明 |
| G5 | INCOMPLETE | 5/5 组打印件运动穿模记录 0；微动壳体/滚轮随动组件 0；运动最小间隙曲线未认证 |
| G6 | INCOMPLETE | Ø2钢销顶部探针已检查；载架直线上装最大重叠 212.250 mm³，此路径不能使用，倾斜装入未证明 |
| G7 | INCOMPLETE | H 为估计包络；D 假设板 1 处相交，不能宣称真实供体适配 |
| G8 | 3D_FEM_BLOCKED | 整壳迭代求解在615.3秒后因系统可用内存低于512MiB被保护器中止（任务峰值0.471GiB，未触及4GiB上限）；三档刚度比较未完成，小梁误差−1.635%不能替代整壳结论。 |
| G9 | INCOMPLETE | S1/S2/S3/S5/S6/S9 提供相应证据；S4 实际按压力、S7 预紧/托架应力和 S8 刚度未完成认证 |
| G10 | PASS_CAD_ESTIMATE | CAD 17138.856 mm³；PA12 密度 1.01 时 17.310 g；切片 35.91 g |
| G11 | UNVERIFIED | 键帽/垫片对壳体包络的行程干涉记录 0；实物微动、PET 调整和通断未测 |


打印件PA12估重17.310g；PLA切片35.91g，4h 50m 28s。两者不含相同的支撑/材料假设，整机质量未确认。

保留CERN-OHL-P-2.0和原NOTICE署名。历史版本未删除。

L2-r3-bundle.zip是模型与视图包；源码、方案和完整报告同时位于仓库，GitHub自动提供的Source code压缩包包含全部仓库文件。不要将模型包当作完整源码归档。
