# L2-r4 · Dremel 3D45 / PLA 打印交付

在原 L2-r4 CAD 上补齐整盘 STL、整体装配 STL 和 Dremel 3D45 专用切片。模型保持 1:1，不改变原底部、五脚贴平台或按键机构，旧版 L2-r4 Release 保留。

**软件检查通过；尚未实机试印，因此本打印包标为预发布。**

下载完整 ZIP 即可获得九件原始 STL/STEP、两种组合 STL、Dremel 3MF、G-code、参数、构建脚本、路径图及检查报告。

| 项目 | 结果 |
| --- | --- |
| 切片软件 | Dremel 3D Slicer 2.3.2 |
| 目标机器 | Dremel 3D45，255 × 155 × 170 mm，床面中心原点 |
| 材料 / 喷嘴 / 层高 | 1.75 mm PLA / 0.4 mm / 0.2 mm |
| 温度 | 喷嘴 220°C、热床 45°C |
| 结构参数 | 4 道墙、5 层顶底、20% gyroid |
| 支撑与附着 | organic 仅从床面起，0.2 mm 接触间隙，3 mm 外沿 brim |
| 切片估计 | 35.05 g、7 小时 1 分 55 秒、128 层，含支撑 |
| 整盘 STL 尺寸 | 210.880 × 88.236 × 25.564 mm |
| 整体塑料装配尺寸（长×宽×高） | 88.236 × 66.096 × 25.564 mm |
| 软件核对 | 两种 STL 各九个闭合组件；3MF 九对象回读；每件有模型挤出；含支撑路径不越界；加热等待、相对挤出和结束回抽检查通过 |

`L2_r4_ALL_PARTS_PRINT_PLATE.stl` 是实际排盘。`L2_r4_WHOLE_ASSEMBLED_PRINTABLES.stl` 是装配外形预览，不是可直接原位打印的活动机构。电子参考件不作为打印塑料件加入这两份 STL。

3MF 没有原生渲染缩略图；附带的 PNG 来自交付 G-code。PLA 品牌、公差和支撑清理需要首件确认；主板、镜头、开关、电池、无线与续航等原有硬件待验证项目继续保留。

[详细说明](https://github.com/Quietmirror/Quietmirror-L2/blob/main/cad/l2_r4_3d45/README.md) · [通过的构建和校验](https://github.com/Quietmirror/Quietmirror-L2/actions/runs/39410542279) · [原 L2-r4 CAD 发布](https://github.com/Quietmirror/Quietmirror-L2/releases/tag/L2-r4)
