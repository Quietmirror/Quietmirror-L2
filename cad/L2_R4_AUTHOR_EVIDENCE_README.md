# L2-r4 作者证据包

本分支 `l2-r4` 只包含作者的设计文件、检查脚本和结果数据，供执行智能体按 [`specs/Quietmirror_L2_r4_CAD_Complete_2026-10-19.md`](../specs/Quietmirror_L2_r4_CAD_Complete_2026-10-19.md) 执行。**不是发布版本**，没有新的模型文件，没有 PR，也没有 tag。

| 目录 | 内容 |
|---|---|
| `cad/l2_r4_author/` | r4 检查脚本和结果：V2 新增结构与全部组件的干涉（`v2_interference.*`）、侧键对并入托架的止挡检查（`side_key_stop_check.*`）、r3 发布版间隙不足项的定位（`gap_locate.*`）、小零件装入路径搜索脚本（`path_check.py` + `loose_parts.json`，作者这次没有跑完）、r4 质量估算（`mass_v2.py`） |
| `cad/l2_fem_author/` | 作者的整壳有限元流程：`fem_variants.py`（选面、约束、网格设置，附录 B 的参考实现）、`fem_l2.py`（L2 用的包装：跳过 R3.2 侧键挡墙工况）、r4 试验件构建脚本（`l2_frame_variant.py` + `r4_frame.json`、`l2_reinforce_variants.py`、`l2_v_variants.py`、`l2_diag_variant.py`）、结果汇总 `fem_r4_results.json`（全部试验件 × 工况，带 R3.2 比值）、R3.2 / P0 / P1 / P7 结果 `fem_summary.json`、并入托架的几何 `variants/R4_SIDE_FRAME_ONLY.step` |
| `cad/l2_r3_check/` | r3 侧键模块数据和 BRep 检查（`r3_parameters.json` 等）、旧侧键座重建（`R32_OLD_SIDE_SEAT_RECONSTRUCTED.step`）、模块视图 |

**依赖与路径：**
- 脚本里的绝对路径（`D:\Quietmirror_L2\...`）是作者本机的工作目录，复用时要改成仓库内的相对路径。
- `fem_variants.py` 需要 R3.2 的 `rebuild_r2/fem_check.py`、`rebuild_r2/parameters.json` 和 `reports/rebuild_r3_2/design_metadata.json`，这三个文件仓库里都有。
- 工具链：Python 3.12、CadQuery 2.8、gmsh 4.15.2、CalculiX 2.22。

**输入几何：**
- r4 试验件建在 `models/L2_r3/parts/BODY.step`（main `1ac9de77`）上，做的是加法布尔，只用于快速验证。
- 正式 r4 BODY 必须在源码层重建（见 spec §8）。
