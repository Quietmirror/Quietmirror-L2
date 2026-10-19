# L2-r4 参数化源与复现

单位mm，坐标沿用R3.2。最终打印件在 `models/L2_r4/parts`；原始参数在 `cad/rebuild_r2/parameters.json`，电子估计包络在 `cad/rebuild_r3_2/electronics.json`。本目录的 `side_module.py` 定义侧键、挡板和一体托架，`build_body.py` 从母面重建BODY，`main_key_relief.py` 只修正主键内部让位，`assemble.py` 构建独立H组件。

请在单独克隆中复现，避免覆盖手工编辑的产物：

```powershell
python -m venv _support/venv
_support/venv/Scripts/python.exe -m pip install -r cad/l2_r4/requirements.txt
_support/venv/Scripts/python.exe -u cad/l2_r4/rebuild_all.py
```

Linux对应解释器为 `_support/venv/bin/python`。CAD/VTK需要OpenGL运行库；有限元另需CalculiX 2.21。数值运行环境见各独立检查工作流、`l2-r4-final-fem.yml` 和Windows产物脚本。最终 `.github/workflows/l2-r4-build.yml` 只复核提交的报告、原生产者身份和所有门槛，不会自动重建或改写已核对的模型。每次有限元求解前必须有至少10GB可用RAM，SPOOLES直接法串行；三档网格均保留。

重建不会继承旧的验收状态。运行 `ci_run.py --config` 指定以下检查配置，报告会记录实际几何和验证源码的身份：

- `GEOMETRY_FINAL.json`：实体、闭合网格、自相交、厚度截面与尺寸；`STATIC_FINAL.json`：打印件完整实体逐对间隙；`ACCESS_FINAL.json`：完整BODY键帽直推、工具可达、压盘覆盖及隐藏特征。旧 `DIAGNOSTIC_RUN.json` 保留为历史诊断，不能代替这些最终入口。
- `MOTION_RUN.json`：主键和滚轮组；`side_functional_checks.py`：完整侧键运动。
- `SPACE_RUN.json`：四件装入、工具可达、六个窗口、D板域、电池服务。
- `ELECTRONICS_RUN.json`：H包络、预留区、硬件和线束；随后运行 `contact_audit_final.py` 对明确的局部功能配合作分类。
- `FINAL_FEM.json`：G8、作者差异控制、S7。只允许一个FEM工作进程依序求解。

`d7_fast_check.py`、`side_clearance_probe.py` 和 `battery_probe.py` 是开发诊断，不可替代G5/S6最终证据。`RUN.json` 只描述当前CI阶段，并不表示无需检查其他门槛。

最终采用 `battery_selection.json` 中的14×20×6mm估计电池，以及 `wheel_clearance_finish.py` 中的C17自制转接板轮廓和C18载架后底面让位。原18×22×6mm电池的有限路线搜索未得到通过路径；缩小电池体积不能证明容量或12小时续航。电池替换保持原插头、线束与服务预留区；C18仅在载架Y34.2..36.2处将底面抬高0.20mm，保留Z12.2座面、1.60mm名义剩余厚度及原BODY与五脚。电池最终验收入口为 `battery_service_final.py`，读取实际保存的电池STEP逐姿态重放；候选搜索报告不能替代该报告。

主键及滚轮分组报告由 `combine_motion.py` 汇总；侧键由 `combine_side_motion.py` 汇总。必须覆盖完整角度集合且无重复，不能只挑通过的组。功能接触区使用具名源特征分解，并通过重新合并后与原实体双向求差检查是否丢失或新增材料；原始全实体相交结果始终保留。

C19在 `wheel_mechanism.py` 生成中键座时削平横梁端帽，并将三处端子孔改为1.8×2.7mm。中键本体、螺栓轴线和压杆高度不移动；五个脚贴局部区域及Z≤5.1低位区域分别求差确认。`body_c19.py` 是与上一候选比较的开发入口，正常完整重建仍使用 `rebuild_all.py`。C19改变BODY，因此G8/S7、装配路径、各组运动、电子与静态检查、六窗及最终打印/渲染全部重验，不能沿用C18的通过状态。

当前距离检查必须导入 `exact_distance.pair`，场景最小值使用 `bounded_scene.scene_pairs`。它们直接测原始完整实体；不对BODY做布尔裁剪。`common.py`中的旧距离函数仅保留历史源码，已因局部裁剪丢失几何的回归实例撤回验收用途。`distance_regression.py`保存了五个已知姿态的完整实体对照，其中末姿态必须继续判为间隙失败。最终总表同时拒绝任何带旧裁剪方法标记的验收数据。

Windows执行 `windows_deliverables.ps1` 使用官方FreeCAD便携包及PrusaSlicer 2.9.6实际生成并重开FCStd/STEP/3MF。切片工程是255×155mm床面和PLA的估计配置，不含打印机认证G-code。`render.py` 仅从实际组件生成视图，`plot_checks.py` 仅绘制实际计算报告。最后依次运行 `gate_accounting.py` 和 `write_docs.py`；发布前运行 `gate_accounting.py --check-only`，任何CAD失败或证据版本不一致都会阻止发布。

署名、实际来源和许可证见 `ATTRIBUTION.md`、仓库 `NOTICE.md` 与 `LICENSE`。FreeCAD内各组件是独立BRep实体；可编辑参数/结构逻辑由Python源提供，不声称具有完整原生草图树或求解过的运动关节。
