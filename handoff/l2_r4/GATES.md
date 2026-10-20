# L2-r4 CAD 门槛总表

状态：**CAD_COMPLETE / HARDWARE_PENDING**

| 门槛 | 结论 | 判据和证据 |
|---|---|---|
| G1 | COMPLETED | 9 个打印件的实体、网格、自相交、尺寸和五脚共面；关键薄壁另列实测截面。 |
| G2 | COMPLETED | 逐对原始结果保留；仅对明确的接触面、轴孔和自攻螺纹区作局部分解。 |
| G3 | COMPLETED | 电池固定间隙、软线 0.2 mm 通道、光学/服务区和天线禁区。 |
| G4 | COMPLETED | 每孔 200 个边界点及 1000 个棱柱点；另查 1000 个顶壳点。有意结构变更与原始占用结果单独列出。 |
| G5 | COMPLETED | 主键、滚轮点击组和两侧键逐姿态精确 BRep 检查；滚动另以包住实际零件的旋转不变包络验证。 |
| G6 | COMPLETED | 微动/挡板体素与精确转折点复核、两键帽每 0.25 mm 直推、顶压钢销及底部螺丝刀可达。 |
| G7 | COMPLETED | H 估计包络与独立组件整机；D 仅交付指定高度下的保守最大连续板区及孔中心允许域。 |
| G8 | COMPLETED | 六工况 × 三网格，实际 SPOOLES；所有比值≥100%，超过3%的作者偏差有独立调查。 |
| G9 | COMPLETED | S1–S9 的 CAD 证据闭合；实际器件参数和实测性能按限定清单保留。 |
| G10 | COMPLETED | 逐件自适应 CAD 体积、密度假设，以及真正切片后的耗材、时间和单盘排布。 |
| G11 | COMPLETED | 实际铰轴下的压盘覆盖、±0.35 mm 贴膜调整链、外向止挡及不破外表面。 |

## 数值与来源

### G1

9 个打印件的实体、网格、自相交、尺寸和五脚共面；关键薄壁另列实测截面。

证据：[solids.json](../../reports/l2_r4/solids.json), [mesh_self_intersections.json](../../reports/l2_r4/mesh_self_intersections.json), [mesh_units_and_volume.json](../../reports/l2_r4/mesh_units_and_volume.json), [foot_planes.json](../../reports/l2_r4/foot_planes.json), [critical_wall_sections.json](../../reports/l2_r4/critical_wall_sections.json), [surface_normal_wall_samples.json](../../reports/l2_r4/surface_normal_wall_samples.json), [BODY_C19.json](../../reports/l2_r4/BODY_C19.json)。

详细数值见 [FINAL_ACCOUNTING.json](FINAL_ACCOUNTING.json) 的 `gates.G1.metrics`。

### G2

逐对原始结果保留；仅对明确的接触面、轴孔和自攻螺纹区作局部分解。

证据：[functional_static_contacts.json](../../reports/l2_r4/functional_static_contacts.json), [all_printed_hardware_intersections.json](../../reports/l2_r4/all_printed_hardware_intersections.json), [hardware_intersections.json](../../reports/l2_r4/hardware_intersections.json)。

详细数值见 [FINAL_ACCOUNTING.json](FINAL_ACCOUNTING.json) 的 `gates.G2.metrics`。

### G3

电池固定间隙、软线 0.2 mm 通道、光学/服务区和天线禁区。

证据：[component_pairs.json](../../reports/l2_r4/component_pairs.json), [wire_component_clearances.json](../../reports/l2_r4/wire_component_clearances.json), [reserved_space_checks.json](../../reports/l2_r4/reserved_space_checks.json)。

详细数值见 [FINAL_ACCOUNTING.json](FINAL_ACCOUNTING.json) 的 `gates.G3.metrics`。

### G4

每孔 200 个边界点及 1000 个棱柱点；另查 1000 个顶壳点。有意结构变更与原始占用结果单独列出。

证据：[six_window_samples.json](../../reports/l2_r4/six_window_samples.json)。

详细数值见 [FINAL_ACCOUNTING.json](FINAL_ACCOUNTING.json) 的 `gates.G4.metrics`。

### G5

主键、滚轮点击组和两侧键逐姿态精确 BRep 检查；滚动另以包住实际零件的旋转不变包络验证。

证据：[main_and_wheel_motion_raw.json](../../reports/l2_r4/main_and_wheel_motion_raw.json), [side_functional_motion.json](../../reports/l2_r4/side_functional_motion.json), [wheel_continuous_rotation.json](../../reports/l2_r4/wheel_continuous_rotation.json)。

详细数值见 [FINAL_ACCOUNTING.json](FINAL_ACCOUNTING.json) 的 `gates.G5.metrics`。

### G6

微动/挡板体素与精确转折点复核、两键帽每 0.25 mm 直推、顶压钢销及底部螺丝刀可达。

证据：[assembly_routes_final.json](../../reports/l2_r4/assembly_routes_final.json), [key_insertion_exact.json](../../reports/l2_r4/key_insertion_exact.json), [assembly_access.json](../../reports/l2_r4/assembly_access.json), [D7_exterior_containment.json](../../reports/l2_r4/D7_exterior_containment.json)。

详细数值见 [FINAL_ACCOUNTING.json](FINAL_ACCOUNTING.json) 的 `gates.G6.metrics`。

### G7

H 估计包络与独立组件整机；D 仅交付指定高度下的保守最大连续板区及孔中心允许域。

证据：[donor_envelope.json](../../reports/l2_r4/donor_envelope.json), [native_roundtrip.json](../../reports/l2_r4/native_roundtrip.json)。

详细数值见 [FINAL_ACCOUNTING.json](FINAL_ACCOUNTING.json) 的 `gates.G7.metrics`。

### G8

六工况 × 三网格，实际 SPOOLES；所有比值≥100%，超过3%的作者偏差有独立调查。

证据：[fem/G8.json](../../reports/l2_r4/fem/G8.json)。

详细数值见 [FINAL_ACCOUNTING.json](FINAL_ACCOUNTING.json) 的 `gates.G8.metrics`。

### G9

S1–S9 的 CAD 证据闭合；实际器件参数和实测性能按限定清单保留。

证据：[side_actuation_force_and_tuning.json](../../reports/l2_r4/side_actuation_force_and_tuning.json), [optical_stack_and_power.json](../../reports/l2_r4/optical_stack_and_power.json), [battery_service_path.json](../../reports/l2_r4/battery_service_path.json), [battery_plug_access.json](../../reports/l2_r4/battery_plug_access.json), [fem/S7.json](../../reports/l2_r4/fem/S7.json)。

详细数值见 [FINAL_ACCOUNTING.json](FINAL_ACCOUNTING.json) 的 `gates.G9.metrics`。

### G10

逐件自适应 CAD 体积、密度假设，以及真正切片后的耗材、时间和单盘排布。

证据：[CAD_mass.json](../../reports/l2_r4/CAD_mass.json), [slice_summary.json](../../reports/l2_r4/slice_summary.json), [F2_trial.json](../../reports/l2_r4/F2_trial.json)。

详细数值见 [FINAL_ACCOUNTING.json](FINAL_ACCOUNTING.json) 的 `gates.G10.metrics`。

### G11

实际铰轴下的压盘覆盖、±0.35 mm 贴膜调整链、外向止挡及不破外表面。

证据：[side_kinematics_independent.json](../../reports/l2_r4/side_kinematics_independent.json), [side_actuation_force_and_tuning.json](../../reports/l2_r4/side_actuation_force_and_tuning.json), [side_functional_motion.json](../../reports/l2_r4/side_functional_motion.json), [D7_exterior_containment.json](../../reports/l2_r4/D7_exterior_containment.json)。

详细数值见 [FINAL_ACCOUNTING.json](FINAL_ACCOUNTING.json) 的 `gates.G11.metrics`。

## 证据范围

精确值仅对应声明的模型与离散姿态；封闭网格、线弹性模拟和参考电子包络均不等于实物装配/打印强度/电子性能认证。

## 仅以下实物项目保留

1. 实物侧键：贴膜调整、通断测试、手感
2. 实测按压力
3. D2F-01F 实物的 FP / OP / TTP
4. PAW3950 实际镜头高度
5. D 方案供体型号确认和主板测绘（DONOR_PENDING）
6. 无线、续航、DPI、宏等功能验证
7. 打印实物的称重和试装
