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

- [获取性能数据（性能分析）](../../operator_practice/performance_analysis/collect_performance_data.md)（`related`）：通过毕昇编译器编译生成可执行程序后，使用msOpProf工具采集Ascend C算子在AI处理器上执行的性能数据，进行性能精细调优。；在进行性能优化之前，需要拿到准确的性能数据，了解性能现状，并根据性能现状分析下一步的优化方向。Ascend C提供了多种性能测试方法，包括上板Profiling、单算子性能仿真流水图等手段。；性能调优入口要求用 msOpProf 采集，数据采集指南给出优化前建立性能现状及 Profiling/仿真方法的前置步骤。
<!-- cannbot:related:end -->
