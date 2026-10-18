# L2 r2 诊断几何

这些 STEP 用于核对方案文字中的连接和间隙，**不是最终打印件或装配认证**。全部以毫米保存，导出后已重新导入检查有效性。

- `R2_CARRIER_DIAGNOSTIC.step`：明确补充桥、下包连接环和 PCB 座位置后的一体托架。未开完整减重窗、端子槽，也没有已验证的固定/装入结构。
- `R2_SIDE_LAYOUT_DIAGNOSTIC.step`：上述托架、两颗微动本体包络和 SIDE_IO_PCB，共四个组件。
- `R2_COLLISION_REGIONS.step`：与保留的主键铰座、低侧壁以及后 PCB 耳的相交区域。
- `FRONT/REAR_EAR_SOURCE_REFERENCE.step`：按原源码数值独立重建的 PCB 耳，已与真实 R3.2 BODY 核对。
- 其余参考 STEP 为局部障碍物或元件包络。`support_reference` 保存上轮独立恢复的母壳内外面，用于复核程序重放。

请结合[详细复核](../../handoff/SECOND_CHECK.md)及[参数修正](../../handoff/PARAMETERS_CORRECTED.md)阅读。几何的单一连通性通过，不代表间隙、承压、完整运动或电子实物装配通过。
