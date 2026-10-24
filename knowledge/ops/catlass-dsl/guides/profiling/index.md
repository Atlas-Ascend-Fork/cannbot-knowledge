# profiling

- [msOpProf 上板采集与 CATLASS 调用流程](collection_workflows.md)：使用 msOpProf 对 CATLASS、Python 和单算子程序进行可复现的上板性能采集。
- [msOpProf CSV 指标解读与瓶颈归因](metrics_and_bottlenecks.md)：解读基础耗时、计算、搬运、Cache、局部存储和资源冲突指标，并映射到 CATLASS 优化候选。
- [msOpProf Simulator 仿真采集与指令级分析](simulator_analysis.md)：编译 CATLASS 仿真目标，采集逐行和逐指令性能数据，并用流水与热点图验证优化假设。
- [MindStudio Insight 可视化瓶颈分析](visualization_analysis.md)：使用热力图、Roofline、Cache、流水图和源码热点将 msOpProf 结果定位到 CATLASS 代码。
