# L2 r2 来源与修改范围

- 用户2026-10-18确认“替代现有方案，继续独立复核修正项”。新附件已设为specs中的现行方案；r1方案在specs/archive，r1复核原文在handoff/archive/l2_r1。
- 唯一生产几何基准仍为Quietmirror/github提交f1b1090931d717117287ea2b79c2e14ddc234937的R3.2。原D盘工程及R3.3保留。
- r2新文件位于cad/l2_r2、reports/l2_r2、views/l2_r2、exports/l2_r2_diagnostic及handoff/l2_r2。根README和handoff现行入口已切换到r2。
- 新几何为独立复核诊断。没有更改原BODY、接口、脚贴或历史装配模型；没有生成最终L2 STL/3MF。
- 本轮仅读源文件/STEP，独立建立BRep与FEM输入；复用上轮本项目独立程序，不导入方案作者脚本函数。保留LICENSE、NOTICE。
- FEM：Gmsh4.15.2，CalculiX2.22，C3D10直中边，E1500MPa/nu0.35；自适应BRep体积。所有新重型进程4GiB Job上限、单线程、串行，原始计算及日志在_support。
- 方案中引用的作者fem3d/fem_variants.py、扫描复核目录和扫描报告未提供；附件的P0/P1/P7结论没有被本轮重新验证。
- 供体按用户原始名称ATK A1 Plus标待确认；没有替换型号，也没有使用未经实测的主板孔位。
