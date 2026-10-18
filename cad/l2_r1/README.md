# L2 独立复核脚本

入口报告：../../handoff/SECOND_CHECK.md。所有脚本仅导入标准库及CAD/数值库，不导入旧建模或FEM检查函数。R3.2源文件仅用作数据与结构来源核对。

1. 从指定Git提交导出`cad`、相关reports、R3.1/R3.2 FCStd与STEP归档，按handoff/PROVENANCE.md设置工作区。
2. 执行 `_support/enter-env.ps1`，重型作业经 `_support/run_guarded.ps1`。
3. `independent_check.py restore`恢复72个独立组件；依次执行`baseline`、`arithmetic`、`surface`、`openings`、`connectivity`、`layout`。
4. `independent_fem.py beam_pair`校验工具链；`independent_fem.py body --size 2.4`生成并求解八工况，记录精确载荷选择与约束。2.0/1.6整壳收敛不是本次已完成项目。
5. `render_checks.py`生成实际CAD检查图；`write_review.py`整理报告和复核包。

窗口、载荷和基准几何数据保留R3.2出处。诊断STEP不是可打印成品；`parameters_reviewed.json`包含待落实的修正值，`geometry_release=false`。

依赖：Python 3.12、CadQuery 2.8、OCP、NumPy、SciPy、Matplotlib、VTK、Gmsh 4.15.2、CalculiX 2.22；使用项目已有D盘工具。本次不安装系统组件。
