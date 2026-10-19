# L2-r3 复现

Python3.12、CadQuery2.8/OCP、NumPy、SciPy、Trimesh、VTK、Pillow、Gmsh4.15.2、FreeCAD1.1.4、PrusaSlicer2.9.6。Windows下设置PYTHONUTF8=1或使用python -X utf8执行脚本。工具链保存在本机_support，不上传二进制或缓存。更换路径时修改_support/enter-env.ps1与各工具路径。

依次运行：prepare_sources.py → side_module.py → build_body.py → remaining_parts.py → surface_mesh.py → electronics_assembly.py → additional_checks.py → validate.py → functional_checks.py → slice_plate.py → native.py（FreeCADCmd）→ render.py → trial_and_plate_views.py → mesh_metrics.py → run_staged_fem.py → write_report.py。每步检查退出码和报告。全部位于cad/l2_r3，重型任务使用4GiB Job限制、单线程及低优先级串行运行。Windows进程保护器随源码提供于cad/l2_r3/guard.py，只管理自己启动的子进程；系统可用内存低于512MiB时中止任务并记录原因。

bootstrap.py用于首次接入本机Downloads附件，不是新机器重放的必要步骤。源方案已保存specs。缺失作者r3参考文件已声明，不通过伪造目录绕过。

CAD构造在源码层取消旧座，原R3.2不变。原始CadQuery STL在少数BSpline接缝不封闭，surface_mesh.py从相同STEP曲面生成共边三角网格，并要求单连通/封闭/方向一致，未补洞。后续几何修改必须重新运行网格和检查。

native.py输出命名B-rep组件的可编辑FreeCAD文件，参数由Python/JSON控制；不是有完整草图历史和已解算装配约束的工程树。打印3MF不缩放，嵌入通用PLA配置，实际打印机需重新确认。

原R3.2输入来自固定基准提交和仓库保留文件。models/L2_r3/inputs/R32_BASELINE.FCStd保存原版命名B-rep；首次重放先用FreeCADCmd执行cad/l2_r3/restore_inputs.py，恢复缺失的exports/rebuild_r3_2/assembly/*.step，已存在文件不覆盖。FEM中间网格、求解日志及临时G-code留在_support/work，不进入发布仓库。

Python实际依赖版本见cad/l2_r3/requirements.txt。在项目根目录建立_support/venv并安装这些依赖，将Gmsh、FreeCAD、PrusaSlicer放到各脚本声明的_support/tools版本目录。先创建_support/work/l2_r3、reports/l2_r3、models/L2_r3/parts和reference目录；使用QUIETMIRROR_ROOT指向项目根目录。原母面参考已在exports/l2_r2_diagnostic/support_reference，旧参数和metadata保留于cad/rebuild_r2及reports/rebuild_r3_2。不要将bootstrap.py对本机Downloads的接入步骤当作必要依赖。

发布流程：prepare_model_bundle.py冻结模型和视图；write_report.py完成报告后，prepare_publication.py生成文本提交清单和全体文件校验表。GitHub工作流仅逐字校验并展开已测产物，不在CI里声称重新建模。l2-r3分支展开后经PR合并，main上的工作流创建INCOMPLETE预发布和附件。版本状态由本地实测报告确定，CI成功不等于机械验收通过。
