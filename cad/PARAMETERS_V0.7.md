# V0.7 参数与复现

单位 mm；坐标 X 向右、Y 向前、Z 向上，前端 Y=0，向后距离 D=-Y。保持 100% 导入切片器。可编辑源为 CadQuery Python + JSON，STEP 可在支持实体建模的 CAD 中继续修改。

## 参数入口

| 内容 | 参数 / 源码 |
|---|---|
| 外形名义长、最大宽、握宽、高 | `parameters_v07.json` 中 `length / max_width / grip_width / height` 和 `shell_stations`；沿用 V0.6 放样方法 |
| 主键触感面 | `left_key / right_key` 的 x、y（即 D）、width、length |
| 主键导向位置 | `modules.left/right.origin`，与触感面是两个独立控制位置；改键面位置时需同时核对柱塞连接 |
| 两侧键位置 | `modules.thumb_front/thumb_rear.origin`，分别为 [-22,-39.5,15.5]、[-22,-53.5,16.0]；侧键造型在 `mechanisms_v07.py:side_face` |
| 滚轮 | `wheel.y / axis_z / diameter / width`；中央装入口由 `carrier_install_opening_xy / carrier_install_opening_d` 控制 |
| 中键导向 | `modules.middle.origin`；支架连杆路径在 `wheel_parts` 中，调整轴位后必须重查这些路径 |
| 行程与滑动配合 | `mechanism.travel`、`radial_clearance`、`stem_xy`；侧键使用较窄柱塞，其横向止挡由前后肩承担 |
| 轴配合 | `printed_axle_diameter / wheel_bore_diameter / bearing_bore_diameter` |
| 开关托架 | `switch_seat_clearance_per_side`；默认轻触开关机械例子为 6×6×5 mm |
| 后孔 | `ventilation`，调用既有 `vent_layout_v06.py` 的镜像轮廓生成；前孔在 `build_v07.py:front_holes` 中由可用区域差集生成 |
| 电子尺寸与摆位 | `electronics_v07.json`；全部估计，未给真实 PCB 孔位 |

这些是可编辑设计变量，不是任意修改单个数字后仍自动满足全部装配关系的承诺。本版冻结 V0.6 的 Z≤5.4 mm 底部；若改变整体长宽并需要改变底部，应另建底部版本，不应对整个 STL 等比缩放。`side_buttons / side_interface` 等继承字段保留为历史参考，本版活动侧键实际位置以 `modules` 为准；`wheel.axis_z` 优先于历史 `height_offset`。

## 环境

本轮实际使用 Python 3.12.14、CadQuery 2.8.0 / OCP 7.9.3.1.1、trimesh、Shapely、NumPy、SciPy、pymeshlab、VTK、Pillow 和 PrusaSlicer 2.9.6。Python 依赖见仓库 `requirements.txt`。路径里的 `.tools` 是本地工具目录，不分发工具安装包。

从项目根目录运行，以下 `python` 应指向已安装依赖的环境：

```powershell
python cad/build_v07.py
python cad/calibration_v07.py
python cad/validate_v07.py
python cad/check_geometry_v07.py
python cad/electronics_v07.py
python cad/clearances_v07.py
python cad/render_v07.py
python cad/render_electronics_v07.py
python cad/slice_v07.py
python cad/check_package_v07.py
python cad/write_release_v07.py
python cad/check_history_v07.py
```

`slice_v07.py` 内的 PrusaSlicer 路径需指向本机安装位置。正式复现从 `build_v07.py` 的默认模式开始；`--reuse-core / --reuse-shell` 仅用于本地迭代缓存，修改壳体参数后不能使用旧缓存。

V0.7 依赖仓库内保存的 V0.6 SHELL STEP、V0.6 内侧补筋路径报告，以及共用的放样、导出和渲染工具。下载整个项目 ZIP 可以保留这些依赖；只下载一个新脚本不足以复现。

## 文件种类

- `exports/v07/print/`：20 个已摆正打印朝向的单实体 STL/STEP。
- `exports/v07/placed/`：装配坐标中的同名部件，另有五个非打印 `SWITCH_EXAMPLE`。
- `MECHANICAL_ASSEMBLY.step`：25 个命名实体的机械装配观察文件。
- `PRINT_PLATE.3mf`：20 件塑料件的打印托盘，包含通用切片估计配置。
- `VIEW_ONLY.3mf`：观察场景，包含非打印开关或电子件，不是打印托盘。
- `CLEARANCES.step`：六种估计净空，不是实体零件。
- `calibration/`：滑动、轴孔和螺钉导孔校准件；不计入 20 件整套估重。

## FreeCAD

在 FreeCAD GUI 中运行 `open_v07_in_FreeCAD.FCMacro`，选择整个仓库目录，可导入命名 STEP 零件并保存 `Quietmirror_V07_local.FCStd`。该宏未在本机 FreeCAD 实际执行；它导入实体，不会自动还原 CadQuery 的建模历史或完成装配求解。后续应建立滑动、转动和固定关节，并引入真实零件的 CAD/测量值。
