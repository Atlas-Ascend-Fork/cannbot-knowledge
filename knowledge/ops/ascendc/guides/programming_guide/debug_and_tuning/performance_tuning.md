---
type: Guide
title: 性能调优（调试与调优）
description: 通过毕昇编译器编译生成可执行程序后，使用msOpProf工具采集Ascend C算子在AI处理器上执行的性能数据，进行性能精细调优。
tags: [task.lookup, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/debug_and_tuning/performance_tuning.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 性能调优

## 性能采集与分析工具
通过毕昇编译器编译生成可执行程序后，使用msOpProf工具采集Ascend C算子在AI处理器上执行的性能数据，进行性能精细调优。
msOpProf工具包含msopprof和msopprof simulator两种使用方式，协助用户定位算子内存、算子代码以及算子指令的异常，实现全方位的算子调优。两种使用方式的详细说明请参考表1。
表1 msopprof和msopprof simulator功能说明表
功能名称：适用场景：使用方式：展示的图形
--：--：--：--
msopprof：适用于上板性能分析（实际运行环境中的性能分析），可协助用户定位算子内存和性能瓶颈。：直接分析运行中的算子，无需额外配置，适合在板环境中快速定位算子性能问题。：计算内存热力图Roofline瓶颈分析图Cache热力图通算流水图算子代码热点图
msopprof simulator：适用于仿真性能分析，可协助用户分析算子指令和代码热点问题。：需要参考msopprof simulator配置，配置环境变量（如LD_LIBRARY_PATH）和编译选项（如添加-g生成调试信息），适合在仿真环境中详细分析算子行为。：指令流水图算子代码热点图内存通路吞吐率波形图
## NPU域上板性能分析
算子程序通过毕昇编译器编译生成可执行程序后，可以通过msopprof在NPU上完成性能采集。以SIMD编程场景为例，使用msOpProf工具采集上板性能数据大致步骤如下：
1.  参考AI Core SIMD编译，编译add算子样例，生成可执行文件。
dav-后为NPU架构版本号，请根据实际情况进行替换，各产品型号对应的架构版本号请通过对应关系表进行查询。
2.  使用msopprof调用算子可执行文件进行性能采集。
3.  查看性能数据，了解当前算子性能瓶颈。
表2 msopprof文件介绍
对于SIMT编程场景，只需遵循AI Core SIMT编译指导进行算子编译，生成可执行文件后，按照上述步骤2和步骤3使用msOpProf工具执行程序，以获取算子执行的性能数据。
## NPU域仿真性能分析
在非昇腾设备上，通过毕昇编译器仿真编译后生成可执行程序，可以通过msopprof simulator完成性能流水仿真。当前仅支持SIMD编程场景，SIMT编程场景不支持。
-   通过CMake方式仿真编译算子
-   灵活控制不同的target是否开启仿真编译。修改CMakeList，使用target_link_libraries与target_link_directories手动配置链接库与路径：
其中仿真库所在目录与NPU架构版本号之间的关系如下，目录名使用下划线连接“dav”和架构版本号。
其中仿真编译所依赖的库介绍如下，开启仿真编译时，需要优先链接，确保优先使用仿真库的符号，防止出现运行时coredump等异常情况。

<!-- cannbot:related:start -->
## 相关

- [MarkStamp](../../../apis/simd_api/basic_api/debug_interface/performance_stats/mark_stamp.md)（`explains`）：性能调优指南说明如何采集并读取流水图定位热点；MarkStamp 写入的 idx 标记正是在该分析流程中把图上位置映射回 Kernel 代码。
- [MetricsProfStart](../../../apis/simd_api/basic_api/debug_interface/performance_stats/metrics_prof_start.md)（`explains`）：性能调优指南给出 msOpProf 上板与 simulator 的采集分析流程，说明在什么调优任务中用 MetricsProfStart/Stop 限定 Kernel 代码段。
- [MetricsProfStop](../../../apis/simd_api/basic_api/debug_interface/performance_stats/metrics_prof_stop.md)（`explains`）：焦点处理MetricsProfStop 标定性能采集区间；性能调优（调试与调优）正文界定“通过毕昇编译器编译生成可执行程序后，使用msOpProf工具采集Ascend C算子在AI处理器上执行的性能数据，进行性能精细调优”。候选是采集区间的 Start/Stop 对或 msOpProf 调优流程，直接决定采集窗口。
- [性能统计](../../../apis/simd_api/basic_api/debug_interface/performance_stats/performance_stats.md)（`explains`）：性能调优指南说明如何把 kernel 侧采集标记接入上板测量和瓶颈分析。
- [分析性能数据（性能分析）](../../operator_practice/performance_analysis/analyze_performance_data.md)（`related`）：调优不是只跑 profiler；分析页把采集结果与理论带宽/算力、最长流水及利用率对照，形成选择优化方向的判据。
- [获取性能数据（性能分析）](../../operator_practice/performance_analysis/collect_performance_data.md)（`related`）：性能调优指南中的 msOpProf 上板和 simulator 流程需要先采集稳定数据；采集页给出命令入口和 trace 可视化方式。
- [调试与调优概述](overview.md)（`related`）：总览在功能正确后引导进入 msOpProf 性能调优，子指南给出上板与仿真路径差异。
<!-- cannbot:related:end -->
