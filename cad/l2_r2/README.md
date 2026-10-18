# r2独立复核重放

工程根目录D:\Quietmirror_L2。每次先进行PowerShell点加载：`. D:\Quietmirror_L2\_support\enter-env.ps1`。重型进程统一通过`_support/run_guarded.ps1`，MemoryGiB=4，串行，不同时开多个求解/建模任务。

顺序：

1. `geometry_recheck.py`：按r2建立诊断托架、间隙表、12组处置及算术。依赖原始R3.2文件及r1独立复原母面。
2. `contact_recheck.py`：独立复原PCB耳、与实际BODY核对完整底面接触。
3. `fem_recheck.py --size 2.4`、`--size 2.0`、`--size 1.6`分别串行运行。它只复用cad/l2_r1/independent_fem.py的独立网格/求解工具；不导入原作者的FEM函数。
4. `summarize_fem.py`：网格体积、刚度趋势、平衡摘要。
5. `render_review.py`：从诊断STEP和实测JSON绘图。
6. `write_review.py`：生成现行和版本化报告。

示例：
```powershell
. D:\Quietmirror_L2\_support\enter-env.ps1
& D:\Quietmirror_L2\_support\run_guarded.ps1 -Executable $CadPython -Arguments @('D:\Quietmirror_L2\cad\l2_r2\geometry_recheck.py') -Log 'D:\Quietmirror_L2\_support\logs\l2_r2_geometry.log' -MemoryGiB 4 -TimeoutSeconds 1800
```

`adopt_plan.py`是本次方案接入记录，通常不需要再次执行。原始附件r1保留于specs/archive，新附件原文在specs；parameters_reviewed.json和handoff/PARAMETERS_CORRECTED.md记录已核实的修正/约束。没有最终生产尺寸或已验证的实物配合。

若换机器，先配置CadQuery/OCP、NumPy、SciPy、VTK、Matplotlib、Gmsh和CalculiX。r1的独立_check.py生成母面参考（也在r2交付support_reference中提供），完整生产基准和依赖由同仓库保留。不要修改源码路径以指向旧工作树的未提交模型。
