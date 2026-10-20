# L2-r4 内部结构与运动模拟

状态：**CAD_COMPLETE / HARDWARE_PENDING**。

## G8 整壳刚度

C3D10二阶四面体；E=1500MPa，ν=0.35；五脚Uz固定，两个局部点约束面内刚体自由度。CalculiX默认SPOOLES直接法，三个网格档串行运行。每次求解记录可用内存、峰值RSS、真实日志以及力/力矩平衡。

| 工况 | 网格mm | 刚度N/mm | R3.2基准 | 比值 | 作者偏差 | 平衡 |
| --- | --- | --- | --- | --- | --- | --- |
| palm_down_20N | 2.4 | 144.818 | 105.640 | 137.09% | +1.02% | True |
| left_main_root_down_5N | 2.4 | 35.746 | 25.893 | 138.05% | +12.76% | True |
| right_main_root_down_5N | 2.4 | 28.226 | 25.074 | 112.57% | +0.88% | True |
| LC3_squeeze_2x2N | 2.4 | 835.690 | 496.430 | 168.34% | -9.36% | True |
| press_A_d16_x14_y60 | 2.4 | 74.530 | 62.210 | 119.80% | +0.39% | True |
| press_B_d16_x-14_y72 | 2.4 | 58.687 | 56.210 | 104.41% | -3.04% | True |
| palm_down_20N | 2.0 | 146.174 | 105.970 | 137.94% | +1.19% | True |
| left_main_root_down_5N | 2.0 | 35.803 | 25.591 | 139.91% | +14.46% | True |
| right_main_root_down_5N | 2.0 | 28.356 | 24.718 | 114.71% | +2.78% | True |
| LC3_squeeze_2x2N | 2.0 | 846.222 | 502.000 | 168.57% | -8.35% | True |
| press_A_d16_x14_y60 | 2.0 | 74.122 | 62.150 | 119.26% | -0.77% | True |
| press_B_d16_x-14_y72 | 2.0 | 59.011 | 53.900 | 109.48% | +2.24% | True |
| palm_down_20N | 1.6 | 144.170 | 105.040 | 137.25% | +1.24% | True |
| left_main_root_down_5N | 1.6 | 35.145 | 25.091 | 140.07% | +11.43% | True |
| right_main_root_down_5N | 1.6 | 28.115 | 24.472 | 114.89% | +2.13% | True |
| LC3_squeeze_2x2N | 1.6 | 847.155 | 497.990 | 170.11% | -9.01% | True |
| press_A_d16_x14_y60 | 1.6 | 72.733 | 61.770 | 117.75% | -1.53% | True |
| press_B_d16_x-14_y72 | 1.6 | 59.286 | 55.310 | 107.19% | +0.31% | True |

作者根部加载脚本使用Y35..42，正文指定35.5..42.5；本轮采用正文，独立重算R3.2同定义基准，并取其与原表的较大值。相同最终网格只改变加载区的控制求解用于解释根部差异。夹持和粗网格指压B差异另用作者V2几何控制件重算；对照包含几何导致的网格变化，不推断单项特征贡献。几何控制件不属于打印版本。差异调查原始证据见 fem/REFERENCE_R32_ROOT_PROTOCOL.json 与 fem/AUTHOR_GEOMETRY_DIFFERENCE.json。

## 作者几何的独立对照

| 工况 | 网格mm | 作者N/mm | 对照N/mm | 对照与作者偏差 | 最终件与对照偏差 | 查明 |
| --- | --- | --- | --- | --- | --- | --- |
| LC3_squeeze_2x2N | 2.4 | 922.030 | 920.898 | -0.123% | -9.253% | True |
| press_B_d16_x-14_y72 | 2.4 | 60.530 | 60.651 | +0.199% | -3.238% | True |
| LC3_squeeze_2x2N | 2.0 | 923.320 | 923.890 | +0.062% | -8.407% | True |
| LC3_squeeze_2x2N | 1.6 | 931.070 | 930.497 | -0.062% | -8.957% | True |

上述对照不替换最终BODY的18项主结果；最终件仍须独立超过R3.2基准。三档网格的实际数值均保留，不以粗网格单值代表收敛极限。

## S7 侧键5N与螺钉预紧

挡柱施加5N，每颗螺钉采用20N参考预紧。20N是明确的工程假设，不是已知拧紧扭矩换算；模型为线弹性等效面力，没有声称完成摩擦接触、螺纹滑牙或层间破坏预测。整壳和侧框区域P95均需≤10MPa，挡板另查预紧与微动反力。

| 零件 | 工况 | 网格mm | 整体P95 MPa | 侧框P95 MPa | 通过 |
| --- | --- | --- | --- | --- | --- |
| BODY | SF_stop | 2.4 | 0.685 | 0.933 | True |
| BODY | SR_stop | 2.4 | 0.698 | 1.012 | True |
| SF_RETAINER | SF_RETAINER_preload_and_switch | 2.4 | 1.993 | 未取得 | True |
| SR_RETAINER | SR_RETAINER_preload_and_switch | 2.4 | 1.637 | 未取得 | True |
| BODY | SF_stop | 2.0 | 0.690 | 0.933 | True |
| BODY | SR_stop | 2.0 | 0.701 | 1.014 | True |
| SF_RETAINER | SF_RETAINER_preload_and_switch | 2.0 | 1.957 | 未取得 | True |
| SR_RETAINER | SR_RETAINER_preload_and_switch | 2.0 | 1.664 | 未取得 | True |
| BODY | SF_stop | 1.6 | 0.693 | 0.951 | True |
| BODY | SR_stop | 1.6 | 0.704 | 1.024 | True |
| SF_RETAINER | SF_RETAINER_preload_and_switch | 1.6 | 1.934 | 未取得 | True |
| SR_RETAINER | SR_RETAINER_preload_and_switch | 1.6 | 1.604 | 未取得 | True |

## S3/S4 侧键行程与理想杠杆力

根据D2F-01F官方OF最大值0.74N、PT最大值0.5mm计算，实际FP/OP/TTP仍待测。各接触点力臂用实际几何坐标定义，未机械套用作者示例中含糊的“中点”数值。

| 键 | 触点 | Y坐标mm | 理想力N | 按压行程mm |
| --- | --- | --- | --- | --- |
| SIDE_FRONT_KEY | cap_midpoint | 50.175 | 0.782 | 0.578 |
| SIDE_FRONT_KEY | quarter_hinge_to_far | 47.987 | 1.419 | 0.319 |
| SIDE_FRONT_KEY | far_edge | 56.050 | 0.355 | 1.275 |
| SIDE_REAR_KEY | cap_midpoint | 64.525 | 0.774 | 0.580 |
| SIDE_REAR_KEY | quarter_hinge_to_far | 66.862 | 1.411 | 0.318 |
| SIDE_REAR_KEY | far_edge | 58.350 | 0.353 | 1.272 |


[Omron D2F官方数据表](https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2f.pdf)。该力值不含摩擦、打印弹性、实际预压和装配偏差。其余S1–S9状态逐项见GATES和FINAL_ACCOUNTING。
