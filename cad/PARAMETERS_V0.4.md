# V0.4 参数、坐标和底部冻结

源文件：[build_v04.py](build_v04.py)；参数：[parameters_v04.json](parameters_v04.json)。单位mm，X向右，Y向前，Z向上；前端约Y=0，末端Y=-90，脚贴粘贴面Z=0。JSON中的纵向位置通常写作距前端的正距离，建模时转成负Y。

## 本轮可以调整的上部参数

| 字段 | 默认 | 作用与限制 |
|---|---:|---|
| `height` | 28 | 新上部的名义高度基准；真实极值见CAD报告 |
| `shell_stations` | 10组站位 | 每组为距前端距离、半宽参考、壳顶高度；PCHIP插值后放样，不从照片反推精确曲率 |
| `upper_width_reduction` | 0.6 | 上部最大参考宽度比62 mm底部小0.6 mm；形成明确过渡，避免近重合薄面 |
| `transition_collar_height` | 0.6 | 在Z=6上方沿旧截面挤出过渡边；不改冻结平面以下 |
| `side_profile_power` | 4 | 横截面超椭圆指数；越大侧面和顶面越平，肩部过渡越集中 |
| `wall` | 1.8 | 新上壳近似法向壁厚目标；既有底部不会随它改变；最终需采样检查 |
| `rear_cavity_end` | 81 | 内腔终点；保留低尾根，避免薄片与斜底筋擦边相交 |
| `left_key / right_key` | X±14.2、距前24，23×41 | 固定主键接触区轮廓。槽宽0.65，保留三处桥；不是弹簧或可动键 |
| `wheel` | X0、距前17、Ø15×5.2 | 顶高=`height+height_offset`=25；中心Z17.5。窗口8.4×18.2，轮架根部仍为旧底部 |
| `wheel_roof_tie_z` | 17.7 | 上部支撑与新键面壳的连接高度，改变轮位后须检查相交与强度 |
| `side_buttons` | 距前33/47，Z16.5/18.8 | 保留纵向位置与键帽尺寸，前/后键分别下调2.7/0.4 mm避让低上壳；改动后重新验证窗口、键帽和装入路径 |
| `ventilation` | 6个12×11外接框六边孔，R1.1 | 两排中心距前56/70，X分别[-16,0,16]/[-15,0,15]；相邻名义平面筋距至少3 |

上壳法向厚度由内外两套曲线近似实现，不是解析恒定偏置。内轮廓增加0.08 mm补偿并考虑纵向坡度。修改参数后必须重新生成、验证和切片；参数化不表示任意参数组合均通过验证。

## 冻结的底部

`frozen_bottom.source_step` 指向已交付 [V0.3 SHELL STEP](../exports/v03/quietmirror_fingertip_V0.3_SHELL.step)，`through_z_mm=6.0`。生成器直接取该STEP的整个Z≤6 mm区域，不重新用近似尺寸画底部。五脚、底筋、传感器框、右托边、轮架根部和完整下壳带均包含其中。

`length=90`、`max_width=62`、`grip_width=54`、脚贴尺寸、底筋参数和传感器参考框在此版被冻结。改这些值会触发明确错误，避免误以为改变参数还能“底部不变”。原V0.1–V0.3源文件仍保留长度/握宽等参数；下一轮若要改变底部，应另开版本并解除冻结约束。

保存后的FIT和SHELL均与V0.3对应STEP做完整冻结区域的双向布尔差检查，结果见 [bottom_preservation.json](../reports/v04/bottom_preservation.json)。顶视或底视图能透过开孔看到上壳，因此整体底视图不要求逐像素相同；检查依据是冻结区域的实际几何。

## 侧键与打印细节

接口沿用V0.3：窗口12×6.6、键面10.8×5.4、内侧限位边13.2×6.2×1.6；名义单边开口余量0.6 mm。两个独立键帽按内侧限位边贴床导出。FIT版通过1.2×1.6×4的临时连接固定侧键，**1.2 mm是刻意保留的局部薄特征**，不应写成全模型最薄处≥1.6 mm。

默认生成两种模型：`FIT`为一个固定试握实体；`SHELL`保留侧键窗口，配两个独立键帽。装配STEP中的三个实体不能直接叠印，电子参考STEP中的彩色框也不参与打印。

## 复现

安装 [requirements.txt](../requirements.txt) 中依赖后，在项目根目录执行：

```powershell
python cad/build_v04.py
python cad/validate_v04.py
python cad/check_bottom_v04.py
python cad/check_side_button_path_v04.py
python cad/render_v04.py
python cad/make_diagrams.py --version 0.4
python cad/write_electronics_v04.py
```

生成器复用本仓库的 `build_v03.py` 几何工具和 `build_mouse.py` 基础构造；全部依赖源文件已放入仓库。第一次运行会自动创建临时工作目录。STEP提供有效B-rep；完整参数和构建逻辑在Python/JSON，不包含Fusion或SolidWorks原生历史树。
