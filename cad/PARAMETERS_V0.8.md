# V0.8 参数与复现

单位 mm；坐标 X 向右、Y 向前、Z 向上，前端 Y=0，向后距离 D=-Y。保持 100% 导入切片器。可编辑源为 CadQuery Python + JSON，STEP 可在支持实体建模的 CAD 中继续修改。

## 参数入口

| 内容 | 参数 / 源码 |
|---|---|
| 外形名义长、最大宽、握宽、高 | `parameters_v08.json` 中 `length / max_width / grip_width / height` 和 `shell_stations`；沿用 V0.6 放样方法 |
| 主键触感面 | `left_key / right_key` 的 x、y（即 D）、width、length |
| 主键导向位置 | `modules.left/right.origin`，与触感面是两个独立控制位置；改键面位置时需同时核对柱塞连接 |
| 两侧键位置 | `modules.thumb_front/thumb_rear.origin`，分别为 [-21.5,-36.5,17.3]、[-21.5,-50.5,18.7]；侧键造型在 `mechanisms_v08.py:side_face` |
| 滚轮 | `wheel.y / axis_z / diameter / width`；中央装入口由 `carrier_install_opening_xy / carrier_install_opening_d` 控制 |
| 中键导向 | `modules.middle.origin`；支架连杆路径在 `wheel_parts` 中，调整轴位后必须重查这些路径 |
| 行程与滑动配合 | `mechanism.travel`、`radial_clearance`、`stem_xy`；侧键使用较窄柱塞，其横向止挡由前后肩承担 |
| 轴配合 | `printed_axle_diameter / wheel_bore_diameter / bearing_bore_diameter` |
| 开关托架 | `switch_seat_clearance_per_side`；默认轻触开关机械例子为 6×6×5 mm |
| 后孔 | `ventilation`，调用既有 `vent_layout_v06.py` 的镜像轮廓生成；前孔在 `build_v08.py:front_holes` 中由可用区域差集生成 |
| 电子尺寸与摆位 | `electronics_v08.json`；全部估计，未给真实 PCB 孔位 |

这些是可编辑设计变量，不是任意修改单个数字后仍自动满足全部装配关系的承诺。本版按用户要求局部修整底框：保留 V0.6 承力路径，使用平面轮廓内收 0.7 mm、前后边界各内退 0.8 mm 限定底框；只削超出该边界的局部材料。五脚、传感器和电源开关下部区域用布尔差检查保留，不对整个 STL 缩放。`side_buttons / side_interface` 等继承字段保留为历史参考，本版活动侧键实际位置以 `modules` 为准；`wheel.axis_z` 优先于历史 `height_offset`。

## 环境

本轮实际使用 Python 3.12.14、CadQuery 2.8.0 / OCP 7.9.3.1.1、trimesh、Shapely、NumPy、SciPy、pymeshlab、VTK、Pillow 和 PrusaSlicer 2.9.6。Python 依赖见仓库 `requirements.txt`。路径里的 `.tools` 是本地工具目录，不分发工具安装包。

从项目根目录运行，以下 `python` 应指向已安装依赖的环境：

```powershell
python cad/build_v08.py
python cad/calibration_v08.py
python cad/validate_v08.py
python cad/check_geometry_v08.py
python cad/electronics_v08.py
python cad/clearances_v08.py
python cad/render_v08.py
python cad/render_electronics_v08.py
python cad/slice_v08.py
python cad/check_package_v08.py
python cad/write_release_v08.py
python cad/check_history_v08.py
```

`slice_v08.py` 内的 PrusaSlicer 路径需指向本机安装位置。正式复现从 `build_v08.py` 的默认模式开始；`--reuse-core / --reuse-shell` 仅用于本地迭代缓存，修改壳体参数后不能使用旧缓存。

V0.8 依赖仓库内保存的 V0.6 SHELL STEP、V0.6 内侧补筋路径报告，以及共用的放样、导出和渲染工具。下载整个项目 ZIP 可以保留这些依赖；只下载一个新脚本不足以复现。

## 文件种类

- `exports/v08/print/`：20 个已摆正打印朝向的单实体 STL/STEP。
- `exports/v08/placed/`：装配坐标中的同名部件，另有五个非打印 `SWITCH_EXAMPLE`。
- `MECHANICAL_ASSEMBLY.step`：25 个命名实体的机械装配观察文件。
- `PRINT_PLATE.3mf`：20 件塑料件的打印托盘，包含通用切片估计配置。
- `VIEW_ONLY.3mf`：观察场景，包含非打印开关或电子件，不是打印托盘。
- `CLEARANCES.step`：六种估计净空，不是实体零件。
- `calibration/`：滑动、轴孔和螺钉导孔校准件；不计入 20 件整套估重。

## FreeCAD

在 FreeCAD GUI 中运行 `open_v08_in_FreeCAD.FCMacro`，选择整个仓库目录，可导入命名 STEP 零件并保存 `Quietmirror_V08_local.FCStd`。该宏未在本机 FreeCAD 实际执行；它导入实体，不会自动还原 CadQuery 的建模历史或完成装配求解。后续应建立滑动、转动和固定关节，并引入真实零件的 CAD/测量值。

## V0.8 新增控制

- `main_key_surface`：主键纵向高度控制点、1.8 mm 壁厚、0.7 mm 横向微拱、2.5 mm 平面转角、0.45 mm 触感边圆角，以及前沿框架切除高度 11.8 mm。两键以 X=0 镜像。独立键面从 D=0.4 延至 D=27.4 mm。
- `fenrir_side`：组合带中心 D43.5/Z18、长26.6/高4.8、斜率0.1、中央间隔1.4、外凸0.35、皮厚1.8、周边间隙0.3、圆角0.3，单位 mm。采用母壳平移差集构造曲面；外观带与柱塞原点分别控制，改参数后要检查其连通。
- `base_trim`：局部外缘内收和前后端退让。不缩小五脚直径，不移动传感器轴线。
- `main_install_reliefs`：按照柱塞肩部外廓加0.3 mm单边让位，形成贯通上方的装入槽；从导向止挡面上方0.05 mm开始，不切掉导向上沿。`preserve_lower_interfaces` 将原底部完整实体保留，仅减去明确定义的外缘框架修整体，避免后壳孔误切尾部脚贴台。
- `electronics_v08.json:schematic_omit_print_parts` 明确电子场景替换的 11 个机械试验夹具；这些从电子装配中省略，但保留在完整机械打印包中。
- `check_geometry_v08.py` 有限法向样本不能证明全局最薄壁；`validate_v08.py` 记录静态体积相交、45 个按键行程位置、155 个按顺序装入位置、连续滚轮旋转外包络及前端净空。阈值 0.01 mm³。
