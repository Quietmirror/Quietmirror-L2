# V0.6 参数与复现

本轮是原创 CadQuery 源码，在 V0.3/V0.5 的曲面与工具函数上继续构建；不需要冻结的底部 STEP。保留旧脚本作为依赖及历史文件。毫米；X向右、Y向前，前端Y=0，JSON的y/d通常是距前端正距离D，CAD中Y=-D，Z向上。

## 可编辑数据

- [parameters_v06.json](parameters_v06.json)：长、宽、高、握宽、壳面站位、壁厚、主键区域、轮径/轮宽/轮高、侧键高度/窗口/导向、USB口、底部开关口、孔列/筋宽。
- [electronics_v06.json](electronics_v06.json)：两方案各部件尺寸、中心、估计依据、条件性主板滚轮避让、净空、电池容量和电流预算。
- [build_v06.py](build_v06.py)：对称底部、五脚、传感器参考框、主键和侧键接口。五脚目前在代码明确排列：X±21/D8、X±21.5/D61.5、X0/D81.5，Z0；不是实板安装孔。
- [vent_layout_v06.py](vent_layout_v06.py)：从实际壳体低位截面取轮廓，生成12个裁形分区。R1为圆角构造的折线近似，圆周48段、简化0.005 mm；不是无限精度解析圆弧。左右孔通过复制镜像，中心孔先裁半再镜像。
- [electronics_v06.py](electronics_v06.py)：根据JSON构建有名称/颜色的分件示意，STEP、观察3MF和部件STL；不创建真实PCB安装孔。

外形长度变化不会自动缩放未知电子件，也不会自动重做全部接口。更改后必须重新运行检查，特别是尾腔、侧键导向、轮轴和孔筋。几何可编辑不等于任意参数值都能生成有效模型。名义尺寸与最终放样包围盒的小偏差同时记录，不伪装成精确人体适配尺寸。

## 环境

Python 3.12；固定依赖见 [requirements.txt](../requirements.txt)。本次使用 CadQuery 2.8.0 /OCP 7.9.3.1.1、PrusaSlicer 2.9.6。VTK图像从实际导出STL渲染；Windows字体默认 `C:/Windows/Fonts/msyh.ttc`。其他系统可在渲染脚本中换成可用中文字体。

Windows PowerShell 示例，项目根目录执行：

```powershell
py -3.12 -m venv .tools/cad-env
.tools/cad-env/Scripts/python.exe -m pip install -r requirements.txt
.tools/cad-env/Scripts/python.exe cad/build_v06.py
.tools/cad-env/Scripts/python.exe cad/validate_v06.py
.tools/cad-env/Scripts/python.exe cad/check_geometry_v06.py
.tools/cad-env/Scripts/python.exe cad/check_side_button_path_v06.py
.tools/cad-env/Scripts/python.exe cad/electronics_v06.py
.tools/cad-env/Scripts/python.exe cad/validate_electronics_v06.py
.tools/cad-env/Scripts/python.exe cad/slice_v06.py
.tools/cad-env/Scripts/python.exe cad/render_v06.py
.tools/cad-env/Scripts/python.exe cad/write_release_v06.py
```

首次运行需要创建 `.tools`，build脚本会创建它和输出目录。`slice_v06.py` 默认查找 `.tools/PrusaSlicer-2.9.6/PrusaSlicer-2.9.6/prusa-slicer-console.exe`；若使用其他安装路径，编辑其中`slicer`变量。工具程序本身不打包进GitHub。不要直接将估算G-code送到未知打印机。

切片器导出的3MF由 `embed_3mf_profile.py --version 0.6` 写入完整配置，再通过 `check_3mf_roundtrip.py --version 0.6` 对无外部INI的重切片核对。共享脚本追加0.6选项，旧版命令仍可使用。所有网格验证针对实际保存的STL，而不是只检查CAD创建调用是否返回成功。

`reports/v06/`保存体积、壁厚、筋、对称、脚底平面、电子干涉和切片数据；`.tools`里的中间STEP/STL与G-code不发布。电子版几何由参数源重建；`CLEARANCES`不是打印零件。

## 后续外部软件接续

导入三版中的对应STEP到FreeCAD或熟悉的CAD，毫米比例；先保留每个子零件，不布尔合并整个电子装配。原参数在本目录Python/JSON中，普通STEP导入不能自动恢复完整参数历史。真实板件确定后，先锁传感器/镜头高度和滚轮轴线，再建安装、按键行程和上下盖闭合。
