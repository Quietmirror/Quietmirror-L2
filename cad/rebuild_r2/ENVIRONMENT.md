# R2 复现环境

本机实际续接目录为 `D:\Projects\Quietmirror\github`，工具及缓存为相邻 `_support`。原来的 C 盘工程未覆盖。工具不打包进模型下载包。

已使用：Python 3.12.14、CadQuery 2.8.0 / OpenCascade、trimesh 5.1.1、Manifold3D 3.5.4、VTK 9.6.2、FreeCAD 1.1.4、Gmsh 4.15.2、CalculiX 2.22、PrusaSlicer 2.9.6。具体 Python 依赖见 `requirements.txt`。本项目是 Windows 上的可复现工作流，尚未在其他平台执行完整流水线。

目录约定：

```text
D:\Projects\Quietmirror\
  github\                    # 源码与交付产物
  _support\
    python\                  # 独立 Python 运行时
    venv\Scripts\python.exe
    tools\FreeCAD\FreeCAD_1.1.4-Windows-x86_64-py311\FreeCADCmd.exe
    tools\FreeCAD\FreeCAD_1.1.4-Windows-x86_64-py311\bin\ccx.exe
    tools\Gmsh\gmsh-4.15.2-Windows64\gmsh.exe
    tools\PrusaSlicer\PrusaSlicer-2.9.6\prusa-slicer-console.exe
    config\
    cache\
    temp\
    logs\
    work\fenrir_rebuild_r2\  # 大型求解输入、DAT/FRD、G-code 等本地证据
    enter-project.ps1
```

`enter-project.ps1` 将 TEMP、TMP、PIP_CACHE_DIR、XDG_CACHE_HOME、MPLCONFIGDIR、PYTHONPYCACHEPREFIX 指到 `_support`，设置 `PYTHONUTF8=1` 与最多两个通用计算线程，并设置 `QUIETMIRROR_ROOT` 和虚拟环境 PATH。FEM 求解子进程另设单线程。仓库中的同名模板按项目位置计算路径；本机实际入口仍在 `_support`。复现者先按目录表准备对应便携工具和虚拟环境；不要修改历史版本的源码来适配路径。

```powershell
. D:\Projects\Quietmirror\_support\enter-project.ps1
python -m pip install -r cad\rebuild_r2\requirements.txt
.\cad\rebuild_r2\REPRODUCE.ps1
```

完整顺序：生成 CAD → 静态和运动检查 → 分步装入检查 → 几何/网格检查 → 接口量规 → 壁厚与自适应体积 → 有限元 → FreeCAD 保存/重开 → 3MF 切片 → 实际 CAD 渲染。

`REPRODUCE.ps1` 每步检查退出码。有限元的计算成功与网格收敛/强度判定不同，必须继续读 `fem_results.json`，不能只看进程退出为 0。输出日志和摘要绑定实际输入文件；任何几何或装配参数改动后都应重新验证。对活动件单独的小改动不自动废弃未变主壳的有限元，但对应碰撞、装入、网格、原生文件和切片必须重做。

绝对弦差导出、网格轻量清理只焊接数值重复顶点、去零面积/重复面；没有补洞或丢弃小实体。厚度脚本使用自适应 CAD 体积积分：默认 OpenCascade 体积积分在裁剪 BSpline 上可出现较大差异，报告以自适应积分与实际 STL 的交叉核对为准。

源代码中的 `hardware_check.py`、`probe.py` 等保留用于进一步诊断。最终交付结果以 README 列出的当前报告为准，旧迭代失败报告不混作验收。

计算过程中的一次 1.6 mm 网格、E=1500 MPa 掌压工况在双线程 CalculiX 下以 `0xC0000005` 退出，没有有效结果。同一个输入改为单线程后完成；这只是观察到的可用执行方式，未证明崩溃根因。后续求解子进程固定单线程，已完成且输入相同的旧作业通过输入/DAT 绑定结果缓存复用。没有修改系统线程设置或重启程序。

原始网格、输入、DAT/FRD 和日志保存在 `_support/work/fenrir_rebuild_r2/fem`，不随 GitHub 模型包上传。公开摘要保留输入、网格和结果的关联信息，复现脚本可重新生成原始作业。大型细网格求解会占用数 GB 内存，任务串行运行；本机使用后台低优先级进程。

1.2 mm 细化作业随后在单线程下同样以 `0xC0000005` 退出，没有可接受的位移/应力结果。1.4 mm 的后续求解也没有生成有效结果。最终采用 2.4、2.0、1.6 mm 三档直接求解，并按实际最后两档判断位移、P95 与峰值各自的收敛情况；未把失败作业算作通过。没有证明崩溃由线程或内存中的哪一项导致。失败日志保留在本地支持目录。

另做了 ITERATIVE CHOLESKY 的独立解析梁对照。位移接近直接求解，但默认迭代精度未通过本项目严格的合力/力矩平衡门槛，因此没有将其用于主壳验收。`solver_crosscheck.py` 和 `solver_crosscheck.json` 保留为诊断证据，不属于默认复现流水线。官方算法说明见 [CalculiX 2.22 手册](https://www.dhondt.de/ccx_2.22.pdf)。主壳继续使用已通过梁基准的默认直接求解器；没有调低验收门槛。
