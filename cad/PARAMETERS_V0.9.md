# V0.9 参数与复现

单位 mm；坐标 X 向右、Y 向前、Z 向上，前端 Y=0，向后距离 D=-Y。保持 100% 导入切片器。可编辑源为 CadQuery Python + JSON，STEP 可在支持实体建模的 CAD 中继续修改。

## 参数入口

| 内容 | 参数 / 源码 |
|---|---|
| 外形名义长、最大宽、握宽、高 | `parameters_v09.json` 中 `length / max_width / grip_width / height` 和 `shell_stations`；沿用 V0.6 放样方法 |
| 主键触感面 | `left_key / right_key` 的 x、y（即 D）、width、length |
| 主键导向位置 | `modules.left/right.origin`，与触感面是两个独立控制位置；改键面位置时需同时核对柱塞连接 |
| 两侧键位置 | `modules.thumb_front/thumb_rear.origin`，分别为 [-21.5,-36.5,17.3]、[-21.5,-50.5,18.7]；侧键造型在 `mechanisms_v09.py:side_face` |
| 滚轮 | `wheel.y / axis_z / diameter / width`；中央装入口由 `carrier_install_opening_xy / carrier_install_opening_d` 控制 |
| 中键导向 | `modules.middle.origin`；支架连杆路径在 `wheel_parts` 中，调整轴位后必须重查这些路径 |
| 行程与滑动配合 | `mechanism.travel`、`radial_clearance`、`stem_xy`；侧键使用较窄柱塞，其横向止挡由前后肩承担 |
| 轴配合 | `printed_axle_diameter / wheel_bore_diameter / bearing_bore_diameter` |
| 开关托架 | `switch_seat_clearance_per_side`；默认轻触开关机械例子为 6×6×5 mm |
| 侧键托架固定 | `side_mount_centres_xy` 为局部坐标 (-6,-3.4)、(-6,3.4)，两耳都位于按键下方；外侧键面位置不变 |
| 主键支撑与侧键让位 | `main_support_drop_mm=4` 将主键根部横筋置于Z12；`side_aperture_inner_extension_mm=1.2` 给侧键内行程让位 |
| 三角孔 | `vent_layout_v09.py` 的半侧边界、内部控制点、Delaunay三角化；`ventilation.minimum_planar_web` 控制内缩，孔全数镜像 |
| 电子尺寸与摆位 | `electronics_v09.json`；全部估计，未给真实 PCB 孔位 |

这些是设计变量，不保证任意改动后仍自动满足装配。V0.9的壳高26、壁1.6、平面筋1.8 mm。`frozen_bottom`指向V0.8底框来源；从其低区扣除旧壳面得到承力核心，保留该核心并重建低处侧壁，本轮不再次裁短底框。主键大小23×27 mm，母曲面由shell_stations和height共同生成，按键没有独立的抬高高度曲线。R6平面转角让前端边界顺着母壳收拢。侧键以modules和fenrir_side为准。

## 环境

本轮实际使用 Python 3.12.14、CadQuery 2.8.0 / OCP 7.9.3.1.1、trimesh、Shapely、NumPy、SciPy、pymeshlab、VTK、Pillow 和 PrusaSlicer 2.9.6。Python 依赖见仓库 `requirements.txt`。路径里的 `.tools` 是本地工具目录，不分发工具安装包。

从项目根目录运行，以下 `python` 应指向已安装依赖的环境：

```powershell
python cad/build_v09.py
python cad/calibration_v09.py
python cad/validate_v09.py
python cad/check_geometry_v09.py
python cad/electronics_v09.py
python cad/clearances_v09.py
python cad/render_v09.py
python cad/render_electronics_v09.py
python cad/slice_v09.py
python cad/package_steps_v09.py
python cad/check_package_v09.py
python cad/write_release_v09.py
python cad/check_history_v09.py
```

`slice_v09.py` 内的 PrusaSlicer 路径需指向本机安装位置。正式复现从 `build_v09.py` 的默认模式开始；`--reuse-core / --reuse-shell` 仅用于本地迭代缓存，修改壳体参数后不能使用旧缓存。

V0.9依赖V0.8的BODY.step以保留底部，并复用历史版本的放样、导出、渲染工具。完整下载仓库才能复现。

## 文件种类

- `exports/v09/print/`：20 个已摆正打印朝向的单实体 STL/STEP。
- `exports/v09/placed/`：装配坐标中的同名部件，另有五个非打印 `SWITCH_EXAMPLE`。
- `MECHANICAL_ASSEMBLY.step`：25 个命名实体的机械装配观察文件。
- `PRINT_PLATE.3mf`：20 件塑料件的打印托盘，包含通用切片估计配置。
- `VIEW_ONLY.3mf`：观察场景，包含非打印开关或电子件，不是打印托盘。
- `CLEARANCES.step`：六种估计净空，不是实体零件。
- `calibration/`：滑动、轴孔和螺钉导孔校准件；不计入 20 件整套估重。

## FreeCAD

在 FreeCAD GUI 中运行 `open_v09_in_FreeCAD.FCMacro`，选择整个仓库目录，可导入命名 STEP 零件并保存 `Quietmirror_V09_local.FCStd`。该宏未在本机 FreeCAD 实际执行；它导入实体，不会自动还原 CadQuery 的建模历史或完成装配求解。后续应建立滑动、转动和固定关节，并引入真实零件的 CAD/测量值。

## 本轮关键几何

- `main_face`：母壳与23×27 mm遮罩求交，再减去下移1.8 mm的母壳，获得与外壳同源的键面；边缘R0.25。没有额外抬高面。
- 上壳三角形逐边内缩0.9 mm，邻边的间距为1.8 mm；三角尖角小圆角R0.65或按面积减小。外缘分段近似曲线，不能宣称周边每处严格等宽。
- 普通壁1.6 mm；主键触感层1.8 mm竖向厚度，与曲面法向厚度不是同一个量。承力筋2.4–2.8 mm，导向机构保留原尺寸。
- 主键导向Z16、中键导向Z17.5 mm；滚轮轴降至Z13.0，支架后连杆随中键导向降低。
- 侧键托架内腔按13.8×12 mm、局部X中心-1.7 mm开让位；仅保护真实R2.3安装柱，避免把托架R2.65避让区误留成悬空碎片。
- `main_key_surface.motion_relief_depth=0.6`：用同源键面向下移动0.6 mm切出局部运动让位，对0.4 mm空行程另留0.2 mm名义余量；该刀具不含柱塞，不改变导向限位。
- USB前上方原孤立横条去除，形成与滚轮安装槽连通的开放式前喉口；接口本体包络不变。
- 电子场景省略的11个试验夹具、真实安装/编码器接口未完成的限制仍适用。
- 检查包括20件拓扑、静态体积相交、45个按压位置、155个顺序装入位置、连续轮体旋转外包络、同源键面、壁厚采样、五脚和底部布尔差。

三个完整装配STEP分别在 `MECHANICAL_ASSEMBLY.zip`、`ATK_A1_PLUS_ESTIMATED.zip`、`PAW3950_CUSTOM_ESTIMATED.zip`（文件均带quietmirror_V0.9_前缀）。校验脚本缺少原STEP时会从对应包解出固定文件名；FreeCAD导入宏直接使用仓库内的分件STEP。

BODY.step因上传接口单次体积限制，单独放在 `exports/v09/quietmirror_V0.9_BODY_STEP.zip`。这是原始STEP的无损压缩；`package_steps_v09.ensure_body_step()`及验证脚本、电子脚本、FreeCAD宏会按需解出同一文件到placed/print。STL仍可直接下载。

最终下横梁由 `wheel.carrier_lower_crossbar_length=4.2` 和 `carrier_lower_crossbar_d=26.9` 控制，宽11、高2 mm。完整五个平台由 `preserve_lower_interfaces` 重新并入，避免从旧壳提取承力核心时丢掉平台与旧侧壁重合的少量材料。完整构建后运行validate即可复现；finalize_v09_carrier.py与restore_v09_platforms.py记录本轮增量修正过程，不需要在全新构建后另跑。
