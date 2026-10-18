# V0.5 参数、孔形算法与复现

单位 **mm**。X向右，Y向前，Z向上；前端Y≈0，尾端Y=-90，脚贴粘贴面Z=0。孔阵使用`D=-Y`表示距前端的正距离。

[参数 JSON](parameters_v05.json) · [主生成器](build_v05.py) · [孔形生成器](vent_layout_v05.py)。V0.5与V0.4相比，只有`ventilation`改变几何；`version`、`notes`更新版本记录。其他外形、底部、侧键、滚轮和电子包络参数沿用。

## 新增孔阵参数

| 字段 | 默认 | 含义 |
|---|---|---|
| `ventilation.minimum_planar_web` | 2.2 | 共享分区各向内退让该值的一半，得到孔间直边的平面筋距；不是法向壳厚 |
| `ventilation.corner_radius` | 1.0 | 对二维孔轮廓生成真实CAD圆角，不是贴图 |
| `ventilation.seed_rows[0]` | D53，X=-13.3/0/13.3 | 前排三个孔的分区种子 |
| `ventilation.seed_rows[1]` | D64，X=-19.2/-6.4/6.4/19.2 | 中排四个交错孔 |
| `ventilation.seed_rows[2]` | D75.2，X=-12.5/0/12.5 | 后排三个孔 |
| `ventilation.domain_right_xd_mm` | 6个右边界站位 | X,D分别为[21,48]、[21,54.5]、[23.5,58]、[23,66]、[21.3,72]、[17.6,79.5]，再镜像得到左边界 |

种子点是分区控制参数，不一定是最终不规则孔的面积质心。相邻种子点的垂直平分线形成共享边界；内缩、R1圆角后再挤出切刀。边缘分区与外壳设计边界相交，孔形因此各自不同。右侧孔只生成一次，直接镜像到左侧；中线孔由镜像种子约束成对称形。

保持种子左右成对、右边界X为正、D有序。改变筋宽、边界或种子后必须重跑验证；参数化不保证任意值均能生成有效圆角、保持单实体或满足打印厚度。别把筋宽继续减小当作已经验证的减重方案。

原始圆角孔轮廓、面积、外接宽长、邻接关系存入[vent_layout.json](../reports/v05/vent_layout.json)。毫米向量图为[14_vent_layout.svg](../views/v05/14_vent_layout.svg)，仅用于解释孔形，不能替代三维STEP或打印STL。

## 继承参数与冻结约束

主壳约90×62×28；名义夹持宽54，最终中段截面约53.06。壳壁目标1.8；五脚Ø8.8，底筋2.6。主键中心X±14.2、D24，接触区23×41；固定滚轮中心X0、D17、Z17.5，Ø15×5.2；左右键和滚轮均保持固定试握结构。

两拇指键中心D33/47、Z16.5/18.8。窗口12×6.6，键面10.8×5.4，限位边13.2×6.2×1.6。FIT版用原有1.2×1.6×4的小桥固定键帽，因此全模型不能宣称最薄处都≥1.6。

冻结底部仍直接读取[已交付V0.3 SHELL STEP](../exports/v03/quietmirror_fingertip_V0.3_SHELL.step)，保留Z≤6 mm完整区域。长度、最大宽、夹持宽、脚贴、底筋与传感器基准参数改变时会触发冻结约束。Z6上方的0.6 mm过渡边和上壳0.6 mm宽度收量沿用V0.4。

“对称”覆盖主壳、主键和孔阵；左侧键及冻结的右托边保留原先右手功能，完整FIT不是全特征镜像。解除这一限制会涉及右侧功能件或底部的新版本。

## 生成与验证

Python 3.12，依赖见[requirements.txt](../requirements.txt)。在项目根目录运行，生成器会创建临时`.tools`目录。需要同时保留仓库内`build_v03.py`、`build_mouse.py`等帮助文件和V0.3底部STEP。

```powershell
python cad/build_v05.py
python cad/validate_v05.py
python cad/check_bottom_v05.py
python cad/check_vents_v05.py
python cad/check_side_button_path_v05.py
python cad/render_v05.py
python cad/render_vents_v05.py
python cad/make_diagrams.py --version 0.5
python cad/write_electronics_v05.py
```

`check_vents_v05.py`在`validate_v05.py`之后运行：它用保存的上壳和原始外曲面网格检查孔口贯通、镜像和细筋法向弦厚。底部检查比较最终保存的STEP，不仅比较生成时的脚坐标。侧键装入检查为≤1.5 mm步长的离散检查，不是连续扫掠或实物配合测试。

STEP提供有效B-rep，完整参数和构造逻辑在Python/JSON，未提供Fusion或SolidWorks原生历史树。

## 切片与图像

使用PrusaSlicer 2.9.6，导入[V0.5估算INI](../slicing/V0.5_PLA_0.4_0.20_ESTIMATE.ini)，FIT五脚朝下、按毫米/100%比例。导出3MF应保留配置；本仓库用`embed_3mf_profile.py --version 0.5`将完整INI放入3MF，再用`check_3mf_roundtrip.py --version 0.5`核对不外载INI的重切片结果。CLI导出时使用`--center 110,110`，确保在220 mm参考热床中间。

切片日志与机用G-code属于本地临时文件，不作为未知打印机的可执行文件发布。数据记录和配置见[打印说明](../slicing/V0.5_PRINTING.md)。所有外形图由实际STL渲染；孔形图从CAD圆弧轮廓生成，未使用AI概念图冒充模型。
