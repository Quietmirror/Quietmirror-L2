# L2-r4 Dremel 3D45 / PLA 打印包

这是 L2-r4 的增量打印交付，直接使用已验收的九个 STL；不重建或修改 BODY、六个顶部窗口、五个脚贴平台或按键机构。原 `L2-r4` 标签和文件保留。用户所说的 “stf” 按 **STL** 交付，不创建仅改扩展名的伪 STF 文件。

## 文件用途

| 文件 | 用途 |
| --- | --- |
| `L2_r4_ALL_PARTS_PRINT_PLATE.stl` | 九件按打印方向排在同一床面。毫米、1:1；STL 不包含支撑或材料参数。 |
| `L2_r4_WHOLE_ASSEMBLED_PRINTABLES.stl` | 九个塑料件在装配姿态的完整外形；保留零件分离关系，用于查看，不能直接当作可活动的一体打印文件。 |
| `L2_r4_3D45_PLA_PLATE.3mf` | Dremel 3D Slicer 2.3.2 工程，九个独立对象、机器/工艺/PLA 配置和已切片路径。 |
| `L2_r4_3D45_PLA_PLATE.gcode` | 由上述工程导出的 3D45 打印路径，包含支撑、首层和结束指令。 |
| `PRINT_PATH_VERIFIED.png` | 从实际 G-code 绘制的整盘、首层、支撑和中间层路径。 |
| `PRINT_VALIDATION.json` | 实际切片质量、时间、路径边界及软件检查结果。 |

电子参考包络不计入可打印 STL，原 [完整 H 装配 STEP](../../models/L2_r4/FULL_ASSEMBLY_H.step)、[FreeCAD 工程](../../models/L2_r4/FULL_ASSEMBLY_H.FCStd) 和 [九件单独 STL/STEP](../../models/L2_r4/parts) 继续提供。

## 本次实际结果

整盘 **35.05 g、7 小时 1 分 55 秒、128 层**；按实际 XY 挤出统计，支撑约 12.299 g、接触面约 0.972 g、brim 约 0.265 g。时间为切片器估计，未计实机校准、人工预热/准备和支撑清理时间。切片器的“首层 3 秒”统计字段与首层完整路径明显不符，保留原始值供追溯，不用作首层工时结论。

整盘 STL 包围尺寸 **210.880 × 88.236 × 25.564 mm**；整体塑料装配尺寸按长×宽×高为 **88.236 × 66.096 × 25.564 mm**，不含参考脚贴与电子元件。模型 1:1，3MF 回读最大边界差 0.00000623 mm。包含支撑的实际挤出范围为 X −121.874～98.158、Y −68.278～25.514、Z 0.2～25.6 mm，均在 3D45 的床面/行程内。

引擎返回 `Success / 0`，九件均有实际模型挤出，原生结果未列出零件警告。日志保留树支撑的非终止性缓存诊断及无 Wayland 显示导致的缩略图提示；3MF 的几何、参数与嵌入 G-code 导出和回读通过，但没有原生渲染缩略图。本包另附由完整 G-code 绘制并人工核看的路径图。未将这些软件结果表述为实物支撑可拆性或打印成功证明。

构建与校验记录：[通过的 GitHub Actions 运行](https://github.com/Quietmirror/Quietmirror-L2/actions/runs/39410542279)；源提交 `4a656c57931e83f6620147ff8c5f55085e68ec1b`，产物提交 `3db274719e5872d17041ebfdfc142957f7d4908a`。

## 机器与材料

使用 Dremel 3D Slicer **v2.3.2** 发布包的 3D45 0.4 mm、PLA 和 0.20 mm 标准配置，解析完整继承链后保存，并记录项目覆盖项。Dremel 1.2.3 随包机器定义另用于核对床面中心原点、255 × 155 × 170 mm 行程及启停指令。

该新旧版本的材料默认值不同：1.2.3 的 Dremel PLA 为 230/60°C，2.3.2 的 Dremel PLA 为 220/45°C。本包采用 **2.3.2 的 220/45°C**，没有把两套默认温度混合使用。普通第三方 PLA 品牌未知，220°C 是明确的起始预设，不是对所有 PLA 的材料认证。

采用 1.75 mm PLA，密度 1.24 g/cm³；0.2 mm 层高与首层、4 道墙、5 层顶底、20% gyroid。外壁 25 mm/s、内壁 35 mm/s、填充 45 mm/s、首层 20 mm/s、加速度 500 mm/s²，限制体积流量 8 mm³/s。启用 Arachne 细壁路径、3 mm 外沿 brim、仅从床面生长的 organic 支撑；顶部间隙 0.2 mm、XY 间隙 0.35 mm、3 层接触面。

启停沿用 3D45 的 M132、M907、G162 序列类型；显式加入温度等待、毫米和相对挤出初始化以及逐层 G92 E0。结束回抽限制为 1 mm。关闭未确认的压力提前、辅助/排风控制和圆弧输出；不写入永久机器设置。机器配置完整差异在 `reports/l2_r4_3d45/profile_changes.json`。

## 朝向、支撑与装配

- BODY 底朝下。最低边缘 Z=5.0 mm，脚贴粘贴面 Z=5.2 mm，排盘后粘贴面距床 0.2 mm；保持既有底部几何，不把这两者误写成同一平面。
- 左右主键、前后侧键和滚轮托架保持原装配方向后落床。两件挡板绕 X 轴 90°，滚轮绕 Y 轴 90°，使滚轮轴线竖直。
- 支撑从底部开口进入壳体内部，也承托主键内侧结构；先清理大窗口及底部入口，再逐步清理微动支座、托架、销孔周边。不可把支撑当永久承力结构。
- 分别打印的侧键、挡板和滚轮按原 [装配顺序](../../handoff/l2_r4/ASSEMBLY_SEQUENCE.md) 装配，配用钢销、螺钉、微动开关等实际零件后检查活动间隙。
- 普通 PLA 较硬且细结构易脆，清理支撑和插销时不要硬撬。完成首件后检查销孔、薄筋及侧键回位，现有计算不能替代 PLA 实物装配与疲劳测试。
- 在 3D45 上选对应 PLA，避免设备的材料识别设置覆盖文件中的 220/45°C；按该机使用说明处理玻璃床面、调平和首层。以工具路径文件打印，不对整盘 STL 再做不等比缩放。

## 验证范围

检查两个 STL 各含九个闭合、法向一致的连通组件；零件原始网格身份、摆放尺寸、3MF 九对象回读；核对每个零件都有实际模型挤出、全部挤出及普通移动不超出床面、加热等待和结束指令、回抽、材料与层高参数。预览图直接取实际 G-code。

软件切片完成不代表实体已经打印。原 L2-r4 的真实供体板测绘、镜头高度、开关手感、PLA 实物强度/公差、无线功能、12 小时续航和实物称重仍待硬件试验。此包不将未知电子尺寸改成已验证装配尺寸。

## 复现

在安装 numpy、trimesh、scipy、matplotlib、lxml、networkx 的 Python 环境运行：

```powershell
python cad/l2_r4_3d45/build_print_package.py --app <Dremel3DSlicer程序目录>
python cad/l2_r4_3d45/validate_print.py
```

Linux 构建使用发布固定的 AppImage 与软件 OpenGL，见 `ci_run.py` 和工作流 `l2-r4-3d45.yml`。原始网格、配置、脚本、日志和结果一起保存；不把显卡缩略图崩溃算作成功切片工程导出。

## 实际来源与许可

- [Dremel Slicer v2.3.2 发布](https://github.com/dremel-digilab/Dremel-Slicer/releases/tag/v2.3.2)：实际使用其中的引擎及 `resources/profiles/Dremel/machine/Dremel 3D45 0.4 nozzle.json`、`filament/Dremel PLA @3D45.json`、`process/0.20mm Standard @Dremel 3D45 0.4.json` 与各自继承文件。
- [Dremel 官方旧版软件下载入口](https://www.dremel.com/au/en/digilab/software)：读取其 1.2.3 安装包内 `resources/definitions/Dremel3D45.def.json` 与 `resources/materials/PLA.xml.fdm_material`，用于交叉核对。
- [Dremel 官方 DigiLab FAQ](https://www.dremel.com/gn/en/service--support/faq/digilab-faq)：3D45 接受 `.gcode`，无需把纯文本伪装成 `.g3drem`。
- Dremel Slicer 派生自 OrcaSlicer / Bambu Studio / PrusaSlicer / Slic3r，按其 AGPL-3.0 许可保留配置来源与 `profiles/UPSTREAM_LICENSE.txt`。本目录切片构建与验证脚本也按 AGPL-3.0 提供；原 CAD 继续沿用仓库 CERN-OHL-P-2.0 和原作者署名。
