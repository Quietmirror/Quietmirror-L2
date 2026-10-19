# L2-r4 参数化源与复现

单位mm，坐标沿用R3.2。最终打印件在 `models/L2_r4/parts`；原始参数在 `cad/rebuild_r2/parameters.json`，电子估计包络在 `cad/rebuild_r3_2/electronics.json`。本目录的 `side_module.py` 定义侧键、挡板和一体托架，`build_body.py` 从母面重建BODY，`main_key_relief.py` 只修正主键内部让位，`assemble.py` 构建独立H组件。

请在单独克隆中复现，避免覆盖手工编辑的产物：

```powershell
python -m venv _support/venv
_support/venv/Scripts/python.exe -m pip install -r cad/l2_r4/requirements.txt
_support/venv/Scripts/python.exe -u cad/l2_r4/rebuild_all.py
```

Linux对应解释器为 `_support/venv/bin/python`。CAD/VTK需要OpenGL运行库；有限元另需CalculiX 2.21。完整受控执行环境见 `.github/workflows/l2-r4-build.yml`、`l2-r4-final-fem.yml` 和Windows产物脚本。每次有限元求解前必须有至少10GB可用RAM，SPOOLES直接法串行；三档网格均保留。

重建不会继承旧的验收状态。运行 `ci_run.py --config` 指定以下检查配置，报告会记录实际几何和验证源码的身份：

- `DIAGNOSTIC_RUN.json`：实体、闭合网格、自相交、厚度截面与尺寸。
- `MOTION_RUN.json`：主键和滚轮组；`side_functional_checks.py`：完整侧键运动。
- `SPACE_RUN.json`：四件装入、工具可达、六个窗口、D板域、电池服务。
- `ELECTRONICS_RUN.json`：H包络、预留区、硬件和线束；随后运行 `contact_audit.py` 对明确的局部功能配合作分类。
- `FINAL_FEM.json`：G8、作者差异控制、S7。只允许一个FEM工作进程依序求解。

`d7_fast_check.py`、`side_clearance_probe.py` 和 `battery_probe.py` 是开发诊断，不可替代G5/S6最终证据。`RUN.json` 只描述当前CI阶段，并不表示无需检查其他门槛。

Windows执行 `windows_deliverables.ps1` 使用官方FreeCAD便携包及PrusaSlicer 2.9.6实际生成并重开FCStd/STEP/3MF。切片工程是255×155mm床面和PLA的估计配置，不含打印机认证G-code。`render.py` 仅从实际组件生成视图，`plot_checks.py` 仅绘制实际计算报告。最后依次运行 `gate_accounting.py` 和 `write_docs.py`；发布前运行 `gate_accounting.py --check-only`，任何CAD失败或证据版本不一致都会阻止发布。

署名、实际来源和许可证见 `ATTRIBUTION.md`、仓库 `NOTICE.md` 与 `LICENSE`。FreeCAD内各组件是独立BRep实体；可编辑参数/结构逻辑由Python源提供，不声称具有完整原生草图树或求解过的运动关节。
