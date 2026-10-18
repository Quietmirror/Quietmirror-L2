"""Publish human-readable results from the final R3 evidence, without overwriting R2."""
from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[2];RP=ROOT/'reports/rebuild_r3'
def read(n):return json.loads((RP/n).read_text(encoding='utf8'))
def write(p,s):p.write_text(s.strip()+'\n',encoding='utf8',newline='\n')
def main():
    static=read('static_checks.json');motion=read('motion_checks.json');ins=read('insertion_checks.json')
    wall=read('thickness_volume_audit.json');sl=read('slice_summary.json');invar=read('preserved_interfaces.json')
    assert static['pass_check'] and motion['pass_check'] and ins['pass_check'] and sl['pass'] and invar['pass_check']
    assert read('geometry_acceptance.json')['pass'] and read('native_freecad_checks.json')['pass'] and read('electronic_space_checks.json')['pass_check']
    vol=wall['total_adaptive_cad_volume_mm3']/1000
    write(RP/'README.md',f'''# R3：机械干涉修正与两种电子方案空间检查

**机械模型和声明的分体电子包络通过本轮几何检查；ATK 整板假设不通过。尚未确认任何实际 ATK A1 Plus 或半组装 PAW3950 主板能直接装入。** 用户本轮确认：板型尚未确定，先检查两种方案的空间和接口。

R2 和全部历史文件保留。主壳仍为 **88.236 × 66.096 × 30.564 mm**；左右主键触感面、宽度、铰链位置、五脚及 USB 接口位置保留。BODY 的 Z=0–5 mm 与 R2 精确布尔对比差异体积为 **{invar['exact_bottom_band_symmetric_difference_mm3']:.6f} mm³**。

![R3 四视图](../../views/rebuild_r3/R3_FOUR_VIEWS.png)

## 交付与下载

| 文件 | 用途 |
|---|---|
| [R3 打印 STL](../../releases/Fenrir-MiniSE-R3/R3_PRINT_STL.zip) | 9 个塑料分件，含本版装配和适配说明 |
| [R3 3MF](../../releases/Fenrir-MiniSE-R3/FENRIR_MINISE_R3_PLA_PRINT_PLATE.3mf) | 嵌入配置并实际切片，需按实际打印机重切 |
| [R3 STEP 与三种场景](../../releases/Fenrir-MiniSE-R3/R3_STEP.zip) | 纯机械完整模型、PAW3950 分体估计布局、ATK 不通过诊断；零件均以 mm 建模 |
| [原生 FreeCAD](../../releases/Fenrir-MiniSE-R3/FENRIR_MINISE_R3.FCStd) | 72 个有名称的机械／硬件参考 BRep，已保存并重开验证；不是有约束的动态装配 |
| [可复现源码与 R2 基准](../../releases/Fenrir-MiniSE-R3/R3_SOURCE_AND_BASE.zip) | R3 Python/JSON、依赖的 R2 源码及精确基准 STEP/STL，避免依赖原作者缓存目录 |
| [在线源文件](../../cad/rebuild_r3/) | [复现方法](../../cad/rebuild_r3/ENVIRONMENT.md)与参数 |

## 本次修正

1. **主键行程计算修正。** R2 把竖直位移当成沿倾斜微动柱的位移，原名义 0.542 mm 实际按轴线计算约 0.477 mm。保留主键本体，将固定限位从 2.3° 调到 2.8°，按本版假设自由高度得到 **0.586 mm**。中键限位从 3.8° 调到 4.1°，得到 **0.585 mm**；两个侧键为 **0.580 mm**。
2. **编码器固定补全。** 新增自定轮廓的 1.2 mm 小板、两个带导孔的载架支座、M2×3 螺钉与垫圈。板边避开中键托架及主键螺钉；新增支座后重新贯通端子孔，避免填回焊脚通道。检查包含螺钉和小板随载架下压的情况。
3. **USB 固定补全。** 接口本身不动，将假设适配板改为 20×10×1 mm，安装孔改至 X=±7.8、Y=13 mm。新增抬高支柱、桥接筋和实际螺钉头／垫圈包络，避开接口金属壳与编码器板。
4. **电子布局重排。** 保留原机构一起检查，未隐藏微动座来“制造空位”。分体板、电池、插头、开关、天线净空和五条线束通道有独立包络。旧 20×24×6 mm 电池假设未通过已检查位置；本图采用 **18×22×6 mm 候选尺寸**，含周围 0.5 mm 的预留。此改变不代表同样容量能塞进更小封装。

## 验证结果与边界

| 检查 | 实际结果 |
|---|---|
| 静态 | {static['parts']} 个实体／包络，{static['pairs']} 对，0 个超出允许局部接触区的干涉 |
| 五键按压 | 每个 41 个位置；主键 0–2.8°、侧键 0–0.60 mm、中键 0–4.1°，通过 |
| 滚轮组合 | 0%、50%、100% 中键按压，各 24 个转角，共 72 组，通过 |
| 机械装入 | {len(ins['stages'])} 个阶段、总计 {sum(x['poses'] for x in ins['stages'])} 个采样位置，通过；含编码器板与 USB 小板进入 |
| 打印网格 | 9 个均封闭、法线一致、各自单连通、无检出的自相交面 |
| 五脚与底部 | Ø8 mm 五脚底面共面，Z=0–5 mm 与 R2 保持一致 |
| 电子包络 | 21 个假设元件位于母壳外形以内；电池预留、天线净空、向下光路检查通过 |
| 原生 CAD | FreeCAD 保存并重开 72 个有效单实体；STEP 三场景也重新导入检查 |
| 切片 | PLA {sl['estimated_total_filament_g']} g，{sl['estimated_time']}，包含支撑与裙边 |

检查使用 0.025 mm 弦差目标的导出网格，异常相交报告阈值 0.01 mm³，候选干涉用 CAD BRep 复核。仅四组明确的螺钉／导孔啮合区和线束端点的局部接触区被作为预期接触处理；按键运动只去除微动的活动柱区域，未跳过整个微动外壳。**有限采样不是连续扫掠证明、制造公差分析或实物装配测试。** 电子安装架、全部导线和电子元件整体装入路径尚未定型。

9 个塑料件 CAD 体积约 **{vol:.3f} cm³**，按 PLA 1.24 g/cm³ 折算 **{vol*1.24:.2f} g** 实体材料；不含电子与金属件。壁厚抽样仍存在轮廓边缘短弦和约 1.26 mm 的载架局部弦，不能写成“所有位置都 ≥1.6 mm”。详见 [壁厚与体积](thickness_volume_audit.json)。R2 有限元结果只作为历史，本轮没有对修正后的 BODY 重新进行强度认证。

## 两种主板的结论

**ATK A1 Plus：当前不能放行。** 36×50×1.2 mm 只是旧假设，现位置与 BODY 约 225.71 mm³、中键微动约 1.215 mm³ 相交。R2 的有限平移／90° 转向网格共检查 780 个位置，也没有找到该矩形板的无干涉位置；这不证明真实 ATK 板所有形状和姿态都不可能。实际板形、元件高度、开关／编码器／传感器／USB／天线位置必须量到后再决定换布局或改壳。不能假设供体使用 PAW3950，也不能指导裁掉已有元件的 PCB。

**PAW3950 分体方案：声明的估计尺寸可以获得无干涉布局。** 它要求独立传感器板、控制／无线板、侧键板、编码器板和 USB 适配板，不能视为某款现成半组装板的已验证适配。安装架孔位、铜箔布线、实际插头、全部焊线、镜头工作高度与无线功能仍未验收。详见 [兼容性报告](COMPATIBILITY.md)。

![分体方案](../../views/rebuild_r3/05_custom_estimates.png)

[按键与装配](INSTALLATION.md) · [检查数据](validation_inputs.json) · [R2 审计原始发现](R2_missing_interface_audit.json) · [ATK 失败诊断](blocked_donor_check.json) · [来源与许可](NOTICE_R3.md)
''')
    write(RP/'COMPATIBILITY.md','''# R3 主板、配件与按键兼容性

## 判定范围

本轮没有实际主板，用户确认按估计包络继续。以下“通过”只针对所列坐标、尺寸和有限运动采样；不是供体替换件认证。ATK 方案是明确不通过的诊断模型，PAW3950 方案是尚未释放制造的分体布局。机械样机是第三种独立交付。

## 按键对应关系

| 操作 | 模型零件 → 对应参考件 | 几何结果 | 尚需实测 |
|---|---|---|---|
| 左键 | LEFT_KEY → SWITCH_LEFT / D2F | 2.8°，沿柱轴约 0.586 mm；全范围采样无刚性外壳穿透 | 自由／动作／总行程、回位、预压、摩擦 |
| 右键 | RIGHT_KEY → SWITCH_RIGHT / D2F | 与左键镜像，约 0.586 mm | 同上 |
| 侧前／侧后 | 两个 SIDE_*_KEY → 两枚 D2F | 滑移 0.60 mm，扣除假设 0.02 mm 间隙后约 0.580 mm | 捕获销防脱、导轨摩擦、真实开关柱高度 |
| 中键 | WHEEL_CARRIER → SWITCH_MIDDLE / D2F | 4.1°，沿柱轴约 0.585 mm；滚轮、小板、编码器与螺钉共同运动 | 编码器电缆柔性余量、微动回位力矩 |
| 滚动 | WHEEL → EC10E1220505 轮廓参考 | 同轴；六角对边 1.67 mm，参考孔下限 1.73 mm；圆轴 Ø2 对 Ø2.35 支撑孔 | 打印六角实际尺寸、配合扭矩、轴向保持与耐磨 |
| 充电口 | USB_C_REFERENCE → 新 USB 适配板 | 接口位置不变，板孔 X±7.8/Y13，螺钉头与垫圈纳入检查 | 具体连接器焊盘、外壳落位、线缆护套尺寸 |

主键与中键钢轴 Ø2 / 孔 Ø2.35，名义径向间隙 0.175 mm；侧捕获销 Ø1.5 / 孔 Ø1.72，名义径向间隙 0.11 mm。这些数字是设计值。0.4 mm 喷嘴不保证能稳定实现 0.06 mm 的六角对边差或 0.02–0.03 mm 的初始触点间隙，应先试印并修孔、校准作动面和止挡。

Omron D2F 公开图给出针柱型 PT 最大 0.5 mm、OT 最小 0.25 mm，OP 从安装孔基准计算。R3 采用移动作动平面与固定柱轴线的交点计算行程；没有把 Z 位移直接当作行程，也没有把 PT 最大值加 OT 最小值当成每个开关都安全的总行程。真实自由高度和实际 PT/OT 未测，约 0.58 mm 的模型压入量仍须按实购开关校准。[Omron 原图](https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2f.pdf)

编码器图检查了 7 mm 安装高度、9.8 mm 本体宽、4.4 mm 厚、2.5 mm 信号脚间距及 1.73 mm 六角孔下限。本版打印载架的顶面为支承基准；小板在载架下方，Z=9.2–10.4，端子末端 Z=8.5，留约 0.7 mm 板下端子。两螺钉中心为 (8.5,26.1) 与 (1.3,32.5)。这是新设计的机械适配板轮廓，未交付电路或 Gerber。[Alps Alpine 原图](https://tech.alpsalpine.com/cms.media/product_catalog_ec_03_ec10e_en_a9ede251c7.pdf)

ATK 原板若固定了另一种微动、光学开关或不同轴高编码器，不能从以上表格推导它能匹配。是否允许外接独立五键、编码器与传感器，取决于真实接口和固件，当前未确认。

## 分体电子空间

| 元件／净空 | 本次假设尺寸（mm） | 状态 |
|---|---|---|
| 传感器板 | 18×18×1.2 | 估计，偏置布板以避开右侧电池；不是 PAW3950 标准板型 |
| 控制／无线板 | 18×18×1.2 | 从先验布局重新分区的目标面积，尚无原理图／布线 |
| PAW3950 封装 | 8×8×2.4 | 仅占位，实际封装与引脚须由供货资料确认 |
| 匹配镜头 | 12×14×4 | 仅占位，光学高度没有验收 |
| 电池 | 18×22×6 | 比旧 20×24×6 假设更小；实际容量未知 |
| 电池周围预留 | 19×23×7 | 每侧增加 0.5 mm，检查中未占用；不等于电芯膨胀安全认证 |
| 电池插头 | 5×6×3 | 仅包络，针数、极性、插拔方向未定 |
| 侧键板 | 1×30×4 | 估计竖板，六处端子槽按当前 D2F 模型避让；真实焊盘未设计 |
| 编码器板 | 最大 12.2×15.1×1.2，有边缘退让 | 按现有编码器／螺钉位置创建的自定义机械外形 |
| USB 板 | 20×10×1 | 自定义孔位，不能直接套用任意成品充电板 |
| 电源开关 | 本体 8×4×3、拨片 3×2×1.8 | 假设，底部开敞区触达需实物确认 |
| 远置天线 | 板 8×4×0.8，净空 12×8×5 | 假设分体天线，需要匹配网络和整机射频测试 |
| 走线 | USB、电池、侧键板、传感器板、天线五条通道 | 部分线束占位；不是全部端子、线径、弯曲半径及焊接工艺验证 |

以上实体和五条通道与完整机械机构共同检查了静态和按压运动。预留孔位只是项目自定接口，实际板未测前不制作供应商适配孔板。电池托架、主板支架和天线支架还需要按实购件设计；最终位置通过不等于已找到所有电子元件的安装路径。

## 光学高度与功能

传感器轴线沿 Z 垂直于鼠标垫。当前镜头占位最低点 Z=7.8 mm，并非 PAW3950 的正确工作距离。脚贴装在 Z=0 平台下面，故“镜头底面到鼠标垫 = 镜头底面 Z + 实际脚贴厚度”。应根据真实传感器板、封装、镜头卡扣与推荐工作高度重算板高／镜头高度，让光路穿过开放底部；不能用调 LOD 掩盖错误的光学距离。

400–6400 DPI、2.4 GHz 1 kHz、宏、LOD、左右／中键／双侧键、低延迟无线、电源开关和充电都是功能目标。未设计或烧录固件，也未验证接收器、RF、延迟、充电或续航。PAW3950 是传感器型号；无线 1 kHz 要由主板、固件和匹配接收器共同实现。没有引入用户不需要的可选 Sync 技术。

12 小时的电流预算应由实购电芯决定。按可用容量系数 0.75：300 mAh 对应平均电流 ≤18.75 mA；400 mAh ≤25 mA；500 mAh ≤31.25 mA。这是计算例，不说明 18×22×6 mm 一定能容纳任何一个容量。持续满性能耗电、电池实际容量、转换损耗和充电能力必须实测。

## 真实主板到手后必须量的尺寸

测量 PCB 完整外轮廓、厚度、双面最高元件及焊点；固定孔直径／坐标；传感器中心和 PCB 基准、镜头型号／安装堆叠／工作距离；五个开关的型号、位置、自由／动作／总行程；编码器轴高／孔形／脚距；USB 相对 PCB 的位置和插头护套；电池长宽厚、线头保护、插头与拔出方向；电源开关位置；天线区域、金属／电池距离；以及接收器型号、接口针序、电压与固件能力。

ATK 若保持原板原元件，须用实测 STEP 重新检查，不能偷偷删掉当前机构或裁板来宣称通过。半组装 PAW3950 板也须重新检查；本图只是一个分体架构的空间建议。
''')
    write(RP/'INSTALLATION.md',f'''# R3 打印、装配与校准

只打印 PRINT STL 或 3MF 内的 9 个塑料件。硬件、PCB、镜头、电池和线束包络不打印；ATK 红色板是失败诊断。

## 打印

0.4 mm 喷嘴、0.20 mm 层高、4 壁、20% 填充，普通 PLA，支撑允许覆盖所有区域。实际切片 {sl['estimated_total_filament_g']} g / {sl['estimated_time']}，包括支撑与裙边；按自己的打印机重新切片。BODY 五脚朝下，主键触感面朝上，侧键／压条按 PRINT 包朝向，滚轮圆轴端朝下、轴竖直；载架平置。清理悬空安装座、轴孔和小板支柱下方的支撑。

9 件塑料总体积 {vol:.3f} cm³，实体 PLA 约 {vol*1.24:.2f} g。壳体与键边的短弦不是普通壁厚承诺，新增支柱孔与端子孔之间最紧的设计平面筋约 1.69 mm；载架旧过渡区域仍有约 1.26 mm 的抽样弦。不要未经试印就整体减薄。

## 机械辅料与适配板

- D2F 针柱式参考微动 5 枚；用实购子型号核对自由高度、动作点和超行程。
- EC10E1220505 轮廓参考编码器 1 枚；核对 7 mm 支承高度和六角孔。
- 原 R2 微动固定：M2×12 10 枚、AF4×1.6 螺母 10 枚、OD5/ID2.2/厚0.3 垫圈 20 枚。
- R3 增加 M2×3 4 枚；USB 用 OD5/ID2.2/厚0.3 垫圈 2 枚，编码器板用 OD4.2/ID2.2/厚0.3 垫圈 2 枚。参考圆头包络 Ø3.8×1.6。导孔 Ø1.7 是试制方案，需校准螺纹和夹紧力，不是反复拆装寿命保证。
- 主键钢轴 Ø2×21.8 两根、载架钢轴 Ø2×13.8 一根、侧键捕获销 Ø1.5×5.6 两根；轴端采取可拆的防脱措施，不让胶进入活动孔。
- USB 自定义适配板 20×10×1 mm；编码器自定义适配板厚 1.2 mm、最大边界 12.2×15.1 mm，按 STEP 的缺口和孔位制作。它们不是随便购买同尺寸矩形板即可替换的成品，也没有电路／Gerber 生产文件。
- 约 Ø7–7.5 mm 圆点脚贴 5 枚，实际厚度记入光学尺寸链。

## 已检查的机械安装顺序

1. 清理主壳，检查五脚、导向、轴孔、端子孔和两处新支柱。
2. 先后侧、再前侧微动；从前端抬高、偏置进入，落到下座，再滑入可拆压条。路径坐标见 `insertion_checks.json`，不是把微动直接从上方硬压。
3. 装中键微动，再沿 18° 座面法线放入两个主键微动；使用原 M2 紧固组件。完整螺钉／工具插入路径未逐一证明，先留足工具空间。
4. 在壳外配合滚轮、编码器、载架与编码器小板，焊脚穿过通道；本次无电路板制造和焊接实测。**编码器小板与轮组一同从前端进入，M2×3 固定螺钉在轮组就位后由下方安装**，不要带着突出螺钉头一起穿过前方 USB 支柱。金属固定脚和端子与板的机械保持依赖实际 PCB／焊接，不可把空孔占位当成已固定。
5. USB 板和连接器从前端水平进入，落在两个支柱上，再装垫圈／M2×3。端口本身的位置沿用 R2。
6. 主键从上方稍向前放入，再后下落到铰链；外侧穿主键钢轴。侧键从左侧插入，再装上方捕获销。载架钢轴从右侧穿入。
7. 冷态检查五键、轮转、中键回位和轴向松动。按实购微动校准触点间隙和止挡，不能因模型可到 2.8°／4.1° 就强压实际开关到底。
8. 先完成机械试装再装电池和电子件；电子全安装顺序与支架尚未定型。贴五脚，实测共面与镜头到垫高度。

本轮机械装入为 18 阶段、930 个有限网格采样。它不包含手指、工具柄、全部紧固件插入、焊接与摩擦。对当前未选定主板，不宣称整体电子样机已经可以按图装成。

试握记录：夹持宽度、顶掌、无名指／小指拖地、指肚碰孔边、滚轮与侧键触达、抬鼠稳定。试按记录：卡滞、回弹、空行程、误触、侧键过早触底、六角松紧和滚轮轴向晃动。尺寸来源仍是近似手部测量，190 mm 张开跨度不是掌宽。
''')
    notice=(ROOT/'reports/rebuild_r2/NOTICE_R2.md').read_text()
    write(RP/'NOTICE_R3.md','''# R3 attribution and license

2026 Quietmirror contributors. R3 makes local corrections to the R2 mechanical reconstruction and adds explicitly estimated electronic layouts. All older source attribution and CERN-OHL-P-2.0 terms are retained. R3 did not import manufacturer CAD, third-party scan geometry, or new external GPL source. Datasheets are linked, not relicensed or republished. R3 preview images are renders of this project's actual generated CAD.

The exact R2 base and source dependencies are included in R3_SOURCE_AND_BASE.zip. Native FCStd consists of named imported BRep features; edit the delivered Python/JSON to regenerate parameters. Estimated PCB outlines are original proposed interfaces, not measured supplier boards.

## Retained R2 attribution

'''+notice)
    write(ROOT/'cad/rebuild_r3/ENVIRONMENT.md','''# Reproduce R3

All modelling uses millimetres. The validated working directory is `D:\\Projects\\Quietmirror\\github`; runtimes, caches and logs stay in its sibling `_support`. Source `enter-project.ps1` before Python. R3 uses the same portable Python/CadQuery/OpenCascade/FreeCAD/PrusaSlicer versions documented in `cad/rebuild_r2/ENVIRONMENT.md`.

Extract `R3_SOURCE_AND_BASE.zip` into a dedicated project directory. It contains `exports/rebuild_r2/assembly`, `print`, `gauges` and the R2 Python dependencies used by `mechanical.py`; it does not require an unpublished mother-surface cache. Alternatively regenerate R2 using its published source before R3. Do not run R2 build over an edited historical checkout.

Run `REPRODUCE.ps1` after setting up the documented sibling runtimes. It builds R3, checks static/motion/mesh/insertion/bottom invariants, slices, renders, saves and reopens native FreeCAD, then generates reports and packages. `audit_r2.py` separately reproduces the historical missing-interface audit; `probe.py` is a development diagnostic, not an acceptance result. No GUI focus or system settings are required.

`parameters.json` controls the revised mechanical stops. `electronics.json` controls the separate estimated layouts. `mechanical.py` gives the additional adapter outlines, hole positions and raised mounting supports; it preserves R2 source and base files. The top-level R3 generated STEP scenes retain part names. CAD scene validity and clearance do not solve manufacturing tolerances, circuit design, PCB routing or physical assembly.

The R3 FEM is deliberately not rerun by this script: R2 FEM remains historical evidence, not certification of the revised BODY. Rendering uses bundled Mesa software OpenGL; Python and slicing run at reduced priority with two-thread environment limits where supported.
''')
    if not (ROOT/'README_R2.md').exists():shutil.copyfile(ROOT/'README.md',ROOT/'README_R2.md')
    write(ROOT/'HISTORY_R3.md','''# R3 version preservation

R3 continues published R2 commit `c07ce1799f32c020c791f2cc08b835941a0c471f`. R2 source, generated releases, reports and views remain at their original paths. The exact R2 homepage is retained as `README_R2.md`. V0.1–V0.9 files, `README_V0.9.md`, the original history and the R1 unaccepted archive remain unchanged.

New work is isolated under `cad/rebuild_r3`, `reports/rebuild_r3`, `views/rebuild_r3`, `exports/rebuild_r3` and `releases/Fenrir-MiniSE-R3`. This is a mechanical/interference and estimated electronic-fit revision, not a new verified donor PCB or wireless product.
''')
    write(ROOT/'README.md',f'''# Quietmirror · Fenrir / MiniSE R3

**R3 已修正主键限位、编码器小板与 USB 固定，并完成机械模型及两种电子方案的空间检查。** 机械模型与声明的分体包络通过有限几何检查；ATK 整板假设不通过，实际主板适配尚未确认。

![R3 实际 CAD](views/rebuild_r3/R3_FOUR_VIEWS.png)

[完整检查报告](reports/rebuild_r3/README.md) · [主板与按键兼容性](reports/rebuild_r3/COMPATIBILITY.md) · [打印和安装](reports/rebuild_r3/INSTALLATION.md) · [可编辑源文件](cad/rebuild_r3/)

| 下载 | 内容 |
|---|---|
| [R3 STL](releases/Fenrir-MiniSE-R3/R3_PRINT_STL.zip) | 9 个可打印塑料件 |
| [R3 3MF](releases/Fenrir-MiniSE-R3/FENRIR_MINISE_R3_PLA_PRINT_PLATE.3mf) | 已实际切片，PLA {sl['estimated_total_filament_g']} g，{sl['estimated_time']}，含支撑与裙边 |
| [R3 STEP](releases/Fenrir-MiniSE-R3/R3_STEP.zip) | 纯机械、PAW3950 分体估计、ATK 不通过诊断三种场景，含分件与接口 |
| [R3 FreeCAD](releases/Fenrir-MiniSE-R3/FENRIR_MINISE_R3.FCStd) | 72 个命名机械／硬件参考实体，已保存重开 |
| [源码与精确 R2 基准](releases/Fenrir-MiniSE-R3/R3_SOURCE_AND_BASE.zip) | Python/JSON 与依赖基准几何，可复现 R3 |

主壳 **88.236×66.096×30.564 mm**。主键触感面／宽度、五脚和既有功能参考位置保留；底部 Z=0–5 mm 与 R2 精确对比一致。主键按微动轴线计算的名义压入量由约 0.477 修正为 0.586 mm。

**检查：98 个实体／包络、4753 对静态组合；五键各 41 个位置；72 个滚轮按压／旋转组合；18 个机械装入阶段。** 9 个打印 STL 封闭、各自连通，无检出的自相交。有限采样不能代替实物试印、公差、回弹或强度测试。

![内部估计空间](views/rebuild_r3/05_custom_estimates.png)

两种电子路线的边界：ATK 真实板未测，历史 36×50×1.2 mm 假设与现机构相交；PAW3950 分体架构的所列包络可放入，但不是某款半组装板的已验证替换。候选电池空间为18×22×6 mm，容量未知；光学工作距离、所有电子支架／线束、固件、无线1 kHz、宏、LOD、充电和12小时续航均未实测。[详细兼容性与待测数据](reports/rebuild_r3/COMPATIBILITY.md)

**历史全部保留：** [R2 原首页](README_R2.md) · [R2 报告](reports/rebuild_r2/README.md) · [V0.9 原首页](README_V0.9.md) · [原历史](HISTORY.md) · [R3 保存说明](HISTORY_R3.md)。R2 有限元结论不自动覆盖 R3 修改后的结构。

许可 [CERN-OHL-P-2.0](LICENSE)，保留[原署名](NOTICE.md)、[R2 署名](reports/rebuild_r2/NOTICE_R2.md)和[R3 署名](reports/rebuild_r3/NOTICE_R3.md)。本项目为独立参数化重建，未复制原厂 CAD 或受限商业扫描。
''')
    print('R3 reports and homepage generated; R2 preserved',flush=True)
if __name__=='__main__':main()
