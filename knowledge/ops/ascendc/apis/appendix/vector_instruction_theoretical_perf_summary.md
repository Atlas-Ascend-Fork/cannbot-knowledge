---
type: API
title: Vector指令理论性能汇总
description: 本节汇总介绍了一些主要的Vector指令的理论性能，以下内容针对如下型号生效：
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/vector_instruction_theoretical_perf_summary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: [agnostic]
---


# Vector指令理论性能汇总

本节汇总介绍了一些主要的Vector指令的理论性能，以下内容针对如下型号生效： - Ascend 950PR/Ascend 950DT - Atlas A3 训练系列产品/Atlas A3 推理系列产品 - Atlas A2 训练系列产品/Atlas A2 推理系列产品 注： - 缓存控制、同步控制和原子操作类指令，不涉及理论性能。 - 对于矢量计算API，若接口调用的传入参数`count`或`repeatTime`取值为0，不会执行计算操作，不会对目的操作数进行写入，该接口将被视为NOP（空操作），但相较于不调用会有额外性能耗时。 针对Ascend 950PR/Ascend 950DT：Memory矢量计算API主要由Reg矢量计算API实现，这类Memory矢量计算API不涉及理论性能。

适用：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。

<!-- cannbot:related:start -->
## 相关

- [Reg矢量计算接口理论性能汇总](reg_vector_compute_interface_theoretical_perf_summary.md)（`same_topic`）：Vector 总表明确指出 950 上大量 Memory 矢量 API 由 Reg API 实现而不单列理论性能；Reg 总表给出这些底层单指令性能及单双发说明，是性能估算的直接下钻。
<!-- cannbot:related:end -->
