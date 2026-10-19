# 最终模型干涉报告

静态打印件检查 28/28 对。穿模 0 对，未达到通用间隙阈值 1 对。

| A | B | 间隙/下界 mm | 相交 mm³ | 说明 |
|---|---|---|---|---|
| BODY | LEFT_KEY | 0.3000 | 0.000000 | exact_if_below_padding_else_lower_bound |
| BODY | RIGHT_KEY | 0.3000 | 0.000000 | exact_if_below_padding_else_lower_bound |
| BODY | SIDE_FRONT_KEY | 0.0000 | 0.000000 | exact_if_below_padding_else_lower_bound |
| BODY | SIDE_REAR_KEY | 0.0000 | 0.000000 | exact_if_below_padding_else_lower_bound |
| BODY | SIDE_SWITCH_CARRIER | 0.0000 | 0.000000 | exact_if_below_padding_else_lower_bound |
| BODY | WHEEL | 0.6500 | 0.000000 | lower_bound_by_AABB_exclusion |
| BODY | WHEEL_CARRIER | 0.2500 | 0.000000 | exact_if_below_padding_else_lower_bound |
| LEFT_KEY | RIGHT_KEY | 10.6000 | 0.000000 | AABB_distance_lower_bound |
| LEFT_KEY | SIDE_FRONT_KEY | 2.5250 | 0.000000 | AABB_distance_lower_bound |
| LEFT_KEY | SIDE_REAR_KEY | 16.2000 | 0.000000 | AABB_distance_lower_bound |
| LEFT_KEY | SIDE_SWITCH_CARRIER | 0.6500 | 0.000000 | AABB_distance_lower_bound |
| LEFT_KEY | WHEEL | 1.1590 | 0.000000 | exact |
| LEFT_KEY | WHEEL_CARRIER | 3.0005 | 0.000000 | exact |
| RIGHT_KEY | SIDE_FRONT_KEY | 31.3718 | 0.000000 | AABB_distance_lower_bound |
| RIGHT_KEY | SIDE_REAR_KEY | 35.6619 | 0.000000 | AABB_distance_lower_bound |
| RIGHT_KEY | SIDE_SWITCH_CARRIER | 21.5098 | 0.000000 | AABB_distance_lower_bound |
| RIGHT_KEY | WHEEL | 2.6883 | 0.000000 | exact |
| RIGHT_KEY | WHEEL_CARRIER | 3.2000 | 0.000000 | exact |
| SIDE_FRONT_KEY | SIDE_REAR_KEY | 0.4717 | 0.000000 | exact |
| SIDE_FRONT_KEY | SIDE_SWITCH_CARRIER | 1.1217 | 0.000000 | exact |
| SIDE_FRONT_KEY | WHEEL | 19.5429 | 0.000000 | AABB_distance_lower_bound |
| SIDE_FRONT_KEY | WHEEL_CARRIER | 14.8700 | 0.000000 | AABB_distance_lower_bound |
| SIDE_REAR_KEY | SIDE_SWITCH_CARRIER | 0.7000 | 0.000000 | exact |
| SIDE_REAR_KEY | WHEEL | 29.0530 | 0.000000 | AABB_distance_lower_bound |
| SIDE_REAR_KEY | WHEEL_CARRIER | 16.0872 | 0.000000 | AABB_distance_lower_bound |
| SIDE_SWITCH_CARRIER | WHEEL | 10.5368 | 0.000000 | AABB_distance_lower_bound |
| SIDE_SWITCH_CARRIER | WHEEL_CARRIER | 5.1000 | 0.000000 | AABB_distance_lower_bound |
| WHEEL | WHEEL_CARRIER | 0.1750 | 0.000000 | exact |


有意接触：载架与安装耳、微动与载架承压面、侧板与安装座、卡舌静止时与端圈、硬止挡、钢销及螺钉功能配合。即使是有意接触，非螺纹实体相交体积仍应≤0.001 mm³。不能用“有意接触”解释明显穿模。

电子检查未满足阈值的项目、运动逐姿态数据见 [component_pairs.json](../../reports/l2_r3/component_pairs.json)、[motion_samples.json](../../reports/l2_r3/motion_samples.json)。电子件均是估计包络；触点、焊脚、插头和线束需实测。零间隙垫片另查 [side_actuation_housing_check.json](../../reports/l2_r3/side_actuation_housing_check.json)。

主键/中键硬壳及滚轮、编码器、固定螺钉、转接板随动的附加检查见 [functional_motion.json](../../reports/l2_r3/functional_motion.json)，最终大于0.001mm³记录 0 条。托架直线上装路径最大相交 212.250 mm³，不能按此路径组装。D供体假设板碰撞 1 对，详见donor_placeholder_check.json；这只否定当前假设布局，不是对未知真实ATK板的测量。

最终全局最薄壁尚未认证；已提供关键位置的直线截面采样和名义截面。刀口、小孔和配合不适合直接凭渲染判断。
