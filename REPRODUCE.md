# L2 r2 独立复核重放

查看报告和 STEP 不需要执行代码。本轮验收状态为“复核完成，有必须修正项”；诊断件不能用作最终打印或装配认证。

## 输入与版本

- 基准：Quietmirror/github 固定提交 `f1b1090931d717117287ea2b79c2e14ddc234937` 的 R3.2。
- [r2复核包](handoff/Quietmirror_L2_R2_Independent_Review_2026-10-18.zip)保存本轮使用的 `exports/rebuild_r3_2/assembly/BODY.step`、母面参考、元数据、参数、报告和源文件。解压到工程根目录即可恢复这些输入；不要用它覆盖其他来源的同名工作文件。
- 新克隆也可以使用归档的 R3.1/R3.2 FCStd，经 `cad/l2_r1/independent_check.py restore` 恢复命名 STEP。恢复函数不覆盖已存在 STEP，复现时应确认已有输入来源。
- `exports/l2_r2_diagnostic/support_reference` 是上轮独立恢复的母面输入。本轮几何程序优先使用这些公开参考，不依赖本机私有缓存。
- 原始 FEM `.geo/.inp/.dat/.sta` 和完整求解日志保存在本机 `_support/work/fem_r2`，未重复上传大型中间作业。公开脚本可重新生成；不同版本/网格参数可能改变离散化结果。

## 环境

本轮实际环境：Windows、Python 3.12、CadQuery 2.8/OCP、NumPy、SciPy、Matplotlib、VTK、Gmsh 4.15.2、CalculiX 2.22。工具与虚拟环境二进制未上传。

`_support/enter-env.ps1` 保存了实际工程路径 `D:\Quietmirror_L2`；换机器须修改 `$ProjectRoot` 并准备 `_support/venv/Scripts/python.exe`，再设置 `cad/l2_r1/independent_fem.py` 的 GMSH、CCX 路径。创建 `_support/logs`、`temp`、`cache`、`config/matplotlib` 后运行。换 CAD 或求解器版本必须重做解析梁基准。没有声称已在另一台机器完成安装测试。

全部重型进程用 `run_guarded.ps1`：4 GiB Windows Job 内存上限、单线程、低优先级、串行。系统可用内存不足时仅终止本作业树。没有更改系统性能设置。

## 顺序

1. 准备基准 BODY、r1证据 JSON、参数与元数据；本轮包已包含这些复核依赖。
2. 运行 `geometry_recheck.py`、`contact_recheck.py`，得到明确假设下的托架及完整支承面检查。
3. 使用上轮相同解析梁工具校验求解链；本轮引用已通过的梁结果。随后将 `fem_recheck.py --size 2.4`、`--size 2.0`、`--size 1.6` **依次**运行。
4. 运行 `summarize_fem.py` 和 `render_review.py`。
5. 阅读新 JSON/图和日志，人工复核后才运行 `write_review.py`。它含本次评审文字，会重写当前 README、handoff 和参数记录，不能把旧文字无审查地套到新几何上。

例如：

```powershell
. .\_support\enter-env.ps1
& .\_support\run_guarded.ps1 -Executable $CadPython -Arguments @('cad/l2_r2/geometry_recheck.py') -Log '_support/logs/l2_r2_geometry.log' -MemoryGiB 4
& .\_support\run_guarded.ps1 -Executable $CadPython -Arguments @('cad/l2_r2/contact_recheck.py') -Log '_support/logs/l2_r2_contact.log' -MemoryGiB 4
# 待前一任务结束并核对退出码后，再运行下一项。
& .\_support\run_guarded.ps1 -Executable $CadPython -Arguments @('cad/l2_r2/fem_recheck.py','--size','2.4') -Log '_support/logs/l2_r2_fem_2.4.log' -MemoryGiB 4
```

详细证据边界见 [SECOND_CHECK](handoff/SECOND_CHECK.md)。三档基线完成不等于已收敛，也不等于最终 L2 的 S8 通过；实际微动、PCB、镜头和叠装尺寸仍未认证。
