---
type: Guide
title: 运行正常（功能调试）
description: 运行正常是算子开发后进行调测的前提，是后续进行性能优化的基础。Ascend C提供了多种调测方法和调测工具，供开发者使用，具体内容请参考功能调试。
tags: [task.lookup, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/functional_debug/running_normally.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 运行正常

运行正常是算子开发后进行调测的前提，也是后续进行性能优化的基础。算子开发完成后，需要先确保其在目标硬件上能够正确执行（不崩溃、不越界、不超时），再进入功能调试（验证计算结果精度是否符合预期）和性能优化（提升执行效率和资源利用率）阶段。Ascend C提供了多种调测方法和调测工具供开发者使用，包括CPU模拟调试、NPU上板执行调试、精度比对工具、Dump数据落盘分析等。具体调测方法和工具使用请参考功能调试章节。

<!-- cannbot:related:start -->
## 相关

- [CPU域孪生调试（功能调试）](../../programming_guide/debug_and_tuning/functional_debug/cpu_twin_debug.md)（`related`）：CPU 孪生可在上板前验证控制流、用 gdb/printf 定位基础逻辑，但不支持 SIMT 且 BuiltIn 限定符被置空，适合作为前置而非设备等价验证。
- [NPU域上板调试（功能调试）](../../programming_guide/debug_and_tuning/functional_debug/npu_board_debug.md)（`related`）：NPU 上板调试提供 printf/DumpTensor、msSanitizer 与单步工具，可直接定位 focal 所说的目标硬件崩溃、越界和运行异常。
- [算子调试（功能调试）](operator_debug.md)（`related`）：operator_debug 将运行异常按 Host Tiling 与 Kernel 两部分拆解，是从“先能正常运行”进入具体定位流程的直接入口。
- [精度正常（功能调试）](accuracy_normal.md)（`related`）：算子能运行后下一道门禁是与已知正确输出比较，并在每次性能修改后复验精度；它把“运行正常”推进到可优化状态。
<!-- cannbot:related:end -->
