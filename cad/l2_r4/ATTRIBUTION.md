# L2-r4 源文件、作者证据与许可

本版以本仓库 L2-r3 源码及 Quietmirror/github 的 R3.2 原始几何为基础，沿用根目录 LICENSE 的 CERN-OHL-P-2.0 和 NOTICE。没有引入商业鼠标厂家的 CAD、标志或未公开主板尺寸。

实际读取并保留的源文件包括 cad/rebuild_r2/build.py、mechanics.py、interfaces.py、surfaces.py、fem_check.py，cad/l2_r3/，原 R3.2 FCStd 的命名 BRep，以及电子包络和机构元数据。

本轮已取得作者分支 l2-r4 的证据包，固定来源提交为 f637118455159515a200e6e0f35c0eea1c7d1633，其历史包含文档引用的 54dac615。cad/l2_r4_author/、cad/l2_fem_author/、cad/l2_r3_check/ 保留在原路径。作者结果用于比对，最终模型是否通过，以本轮独立执行记录为准。

装配路线实际参考 guided_paths.py、path_check.py、guided_routes.json 和 loose_parts.json。新脚本增加实际定位销、精确转折点和最后落座检查，并处理射线奇偶数异常，不把作者简化包络的成功直接归为最终模型成功。

fem_loads.py 的载荷和约束函数改编自作者的 fem_variants.py；积分及结果解析复用本项目 fem_check.py。实际模型、载荷、求解器和网格参数记录在输出报告中。

olliebella、Kotinos、paw3395-pcb 等早期参考的作者与许可继续保存在根目录 NOTICE 和 references。本轮没有重新测量真实 ATK 供体或 PAW3950 自制板，相关尺寸仍为明确标注的参考包络。