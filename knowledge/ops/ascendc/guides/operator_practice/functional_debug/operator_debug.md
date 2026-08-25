---
type: Guide
title: 算子调试（功能调试）
description: 从异构计算章节可以了解到Ascend C算子主要包括Tiling和Kernel实现两部分组成。
tags: [task.lookup, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/functional_debug/operator_debug.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 算子调试

从异构计算章节可以了解到Ascend C算子主要包括Tiling和Kernel实现两部分组成。

Tiling实现运行在Host侧CPU上，一般使用传统的调测手段（比如gdb工具）即可完成调试。

Kernel实现运行在Device侧NPU上，Ascend C提供了多种调试方式，包括孪生调试、上板调试等，具体的调试方法请参考算子调试。

<!-- cannbot:related:start -->
## 相关

- [CPU域孪生调试（功能调试）](../../programming_guide/debug_and_tuning/functional_debug/cpu_twin_debug.md)（`related`）：算子调试总流程中的 Host/CPU 调试由该卡展开为 CPU 孪生编译、GDB 单步及 BuiltIn 置空导致的重定义边界。
- [运行正常（功能调试）](running_normally.md)（`related`）：operator_debug 将运行异常按 Host Tiling 与 Kernel 两部分拆解，是从“先能正常运行”进入具体定位流程的直接入口。
- [NPU域上板调试（功能调试）](../../programming_guide/debug_and_tuning/functional_debug/npu_board_debug.md)（`same_topic`）：《NPU域上板调试（功能调试）》处理“NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。”。《算子调试（功能调试）》提供“从异构计算章节可以了解到Ascend C算子主要包括Tiling和Kernel实现两部分组成。”，其具体合同或探针直接接入NPU 上板打印、异常定位、Tiling 调试、精度对比和离线解析流程。
- [精度正常（功能调试）](accuracy_normal.md)（`same_topic`）：《精度正常（功能调试）》处理“性能优化的基础是算子运行得到正确的计算结果。评判计算结果正确性需要有一定的评判标准，即使用已知的正确的输出和实际结果进行比较。优化过程中，每次迭代修改后，都需要验证性能优化的新结果是否满足精度评判标准。”。《算子调试（功能调试）》明确提供“从异构计算章节可以了解到Ascend C算子主要包括Tiling和Kernel实现两部分组成。”，其参数、调用或验证步骤直接接入精度正常时的基线固定、二分定位、误差对比和复现流程。
<!-- cannbot:related:end -->
