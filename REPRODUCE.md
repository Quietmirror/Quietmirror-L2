# L2 独立复核的复现范围

本仓库提供复核输入、源码、参数和已有结果，不把尚未完成的正式 L2 模型或硬件装配声明为通过。查看结果不需要运行 CAD 或 FEM。

## 基准输入

已包含 R3.1、R3.2 的 FCStd、R3.2 的 `reports/rebuild_r3_2/design_metadata.json` 和基准 CAD 源码。它们来自 Quietmirror/github 固定提交 `f1b1090931d717117287ea2b79c2e14ddc234937`，不会随原仓库 main 更新。

`independent_check.py restore` 从两份 FCStd 的 Document.xml/BRep 数据恢复命名 STEP 组件。它不会覆盖同名已存在的 STEP；要独立复现，应使用一个新克隆，或先确认已有 exports 的来源。

本仓库包含的是本轮所需输入。历史版本的完整打印包、STEP 总包及历史报告仍在原仓库；历史建模脚本可能依赖这些未重复分发的旧文件。此说明只覆盖本轮 `cad/l2_r1` 复核。

## 已使用的环境

- Windows，Python 3.12，CadQuery 2.8 / OCP，NumPy、SciPy、Matplotlib、VTK。
- Gmsh 4.15.2，CalculiX 2.22。
- 本次 FEM 使用单线程、串行求解。保护脚本默认设置 4 GiB Windows Job 内存上限，系统空闲内存过低时只终止本次作业树。

工具、Python 虚拟环境及求解器二进制未上传。仓库内的 `_support/enter-env.ps1` 保存了实际运行时的 `D:\Quietmirror_L2` 路径；其他电脑须将其 `$ProjectRoot` 改为克隆目录，并准备 `_support/venv/Scripts/python.exe`。FEM 源码顶部 `GMSH` 和 `CCX` 常量须指向本机对应版本程序。

这份环境说明是复现前提，不表示本仓库已经在另一台电脑上完成安装或验证。CAD 库与求解器版本改变后须重做梁校验。

## 运行顺序

在项目根目录准备 Python 依赖、求解器路径及 `_support/logs`、`_support/temp`、`_support/cache`、`_support/config/matplotlib` 后：

```powershell
. .\_support\enter-env.ps1

# 以下任务按顺序运行；connectivity 依赖 openings 生成的母皮数据。
# restore、surface、openings、connectivity、layout 等 CAD 作业也建议使用保护脚本。
$tasks = @('restore', 'baseline', 'arithmetic', 'surface', 'openings', 'connectivity', 'layout')
foreach ($task in $tasks) {
  & .\_support\run_guarded.ps1 -Executable $CadPython -Arguments @('cad/l2_r1/independent_check.py', $task) -Log "_support/logs/$task.log"
  if ($LASTEXITCODE -ne 0) { throw "Failed: $task" }
}

& .\_support\run_guarded.ps1 -Executable $CadPython -Arguments @('cad/l2_r1/independent_fem.py', 'beam_pair') -Log '_support/logs/beam_pair.log'
# 只有梁校验通过后，再运行整壳：
& .\_support\run_guarded.ps1 -Executable $CadPython -Arguments @('cad/l2_r1/independent_fem.py', 'body', '--size', '2.4') -Log '_support/logs/body_2.4.log'

& $CadPython cad/l2_r1/render_checks.py
```

先核对生成的 JSON 和求解日志，再考虑执行 `write_review.py`。该脚本会重写 README、报告、参数和复核 ZIP，且报告文字含本次评审结论；它不是适用于任意新结果的自动验收程序。新一轮数值变化时须同步审阅报告文字，不能直接套用旧结论。根目录发布导航位于 Git 历史，可据此恢复。

## 证据边界

- `exact_author_reproduction_certified=false`：独立载荷、约束与位移度量在输入 JSON/源码中明确，但原作者同工况严格复现仍缺信息。
- 整壳当前发布 2.4 mm 网格结果；2.0 / 1.6 mm 整壳收敛未完成。
- 诊断 STEP 故意保留所发现的断开与间隙问题；不能据此直接加工装配。
- 无实际 PCB、微动和镜头尺寸前，装配匹配与真实点击/回弹不认证。
