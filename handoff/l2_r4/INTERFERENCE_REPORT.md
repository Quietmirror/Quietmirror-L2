# L2-r4 干涉与间隙复核

状态：**CAD_COMPLETE / HARDWARE_PENDING**。

单位为 mm；+X 为拇指侧，−Y 为前端，+Z 向上。脚贴粘贴面 Z=5.2，估计脚贴厚度0.8，鼠标垫平面 Z=4.4。

精确BRep结果只证明声明的形状与已采样姿态；AABB仅用于排除不可能相交的候选，不作为精确最小距离。所有打印件、硬件和线束均有原始检查，功能配合仅在明确的轴孔、接触面、座面及螺纹区局部分解。

| 项目 | 结果 | 证据 |
| --- | --- | --- |
| G1 | COMPLETED | solids.json, mesh_self_intersections.json, mesh_units_and_volume.json, foot_planes.json, critical_wall_sections.json, surface_normal_wall_samples.json, BODY_C19.json |
| G2 | COMPLETED | functional_static_contacts.json, all_printed_hardware_intersections.json, hardware_intersections.json |
| G3 | COMPLETED | component_pairs.json, wire_component_clearances.json, reserved_space_checks.json |
| G4 | COMPLETED | six_window_samples.json |
| G5 | COMPLETED | main_and_wheel_motion_raw.json, side_functional_motion.json, wheel_continuous_rotation.json |
| G6 | COMPLETED | assembly_routes_final.json, key_insertion_exact.json, assembly_access.json, D7_exterior_containment.json |
| G7 | COMPLETED | donor_envelope.json, native_roundtrip.json |
| G11 | COMPLETED | side_kinematics_independent.json, side_actuation_force_and_tuning.json, side_functional_motion.json, D7_exterior_containment.json |

## 仍未通过的静态项

当前报告没有未通过项；报告缺失或版本失配仍会阻止最终门槛通过。

## 运动采样

| 组 | 姿态数 | 结论 |
| --- | --- | --- |
| LEFT_KEY | 25 | True |
| RIGHT_KEY | 25 | True |
| WHEEL_CARRIER | 23 | True |
| SIDE_FRONT_KEY | 33 | True |
| SIDE_REAR_KEY | 33 | True |

完整曲线见 views/l2_r4 中运动图，原始数据在 reports/l2_r4。超过物理止挡的0.3°诊断姿态保留原始接触体积；只把指定止挡区域接触归类为功能限位，其他部位仍须保持净空。

## 线束与预留区

线束检查记录数：672。预留区检查记录数：261。电池本体要求0.5mm，走线要求0.2mm；服务区和光路检查实体侵入，天线禁区检查导电件侵入。预留区不作为实体元件计算普通间隙。

最薄壁不以随机采样值冒充全局证明。关键壁、铰节、止动耳、螺孔边距有单独截面表；表面法线弦长采样中的极小值可能落在圆角或自由边，必须结合截面与切片检查。详细见 critical_wall_sections.json、surface_normal_wall_samples.json。
