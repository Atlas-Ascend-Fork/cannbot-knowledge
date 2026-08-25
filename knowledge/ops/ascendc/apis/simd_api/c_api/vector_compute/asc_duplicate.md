---
type: API
title: AscDuplicate
description: 执行矢量复制（Duplicate）操作，将标量值复制填充到矢量中。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_duplicate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscDuplicate

执行矢量复制（Duplicate）操作，将标量值复制填充到矢量中。
函数原型：void asc_duplicate(__ubuf__ half* dst, half src, uint32_t count)
约束：dst的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [InitOutput GM 专用，UB 清零用 Duplicate](../../../../runbooks/compilation/initoutput_gm_ub_duplicate.md)（`exemplifies`）：InitOutput GM 专用，UB 清零用 Duplicate 与《AscDuplicate》的实质衔接是：InitOutput 只接受 GM GlobalTensor，而 UB LocalTensor 要用 Duplicate；相关 API、类型错误、TBuf 取 LocalTensor 和清零覆盖故障直接验证该边界。
- [UB 预填充 Duplicate 引入 Vector 开销拖慢纯写带宽](../../../../runbooks/performance/duplicate_ub_prefill_hurts_pure_write_bandwidth.md)（`exemplifies`）：《UB 预填充 Duplicate 引入 Vector 开销拖慢纯写带宽》的任务是“在纯写 HBM 带宽探针的 DataCopy(UB→GM) 前加 Duplicate<half> 预填充 UB，相对原版纯写带宽反而下降约 5%，因 Duplicate 占用 Vector 流水线与 MTE3 串行，不应作为写带宽优化手段。”。《AscDuplicate》具体提供“执行矢量复制（Duplicate）操作，将标量值复制填充到矢量中。”，它直接用于纯写带宽中 Duplicate 占用 Vector 流水并与 MTE3 串行的验证。
- [Duplicate](../../basic_api/memory_vector_compute/data_padding/duplicate.md)（`related`）：“Duplicate”定义：将变量或立即数复制多次并填充到向量中，支持前n个数据计算和高维切分计算两种方式。；“AscDuplicate”定义：执行矢量复制（Duplicate）操作，将标量值复制填充到矢量中。。实质衔接：这些卡分别限定 Duplicate 的等价 Reg/C API、UB 清零和标量广播正用法，以及全量 padding 覆盖、归约标量来源和纯写预填充的失败/性能边界。
- [AscDuplicate](../reg/data_fill/asc_duplicate.md)（`same_topic`）：Vector C API 与 Reg C API 都做标量广播，但输出载体不同。
- [AscDuplicateHighest](../reg/data_fill/asc_duplicate_highest.md)（`same_topic`）：AscDuplicateHighest 与《AscDuplicate》的实质衔接是：AscDuplicateHighest 从 src 最高 lane 广播到 mask 选中位置；Merge/Scalar/普通 Duplicate 的来源与未选中位置处理不同，相关错例直接约束枚举、范围和归约结果广播。
- [AscDuplicateScalar](../reg/data_fill/asc_duplicate_scalar.md)（`same_topic`）：AscDuplicateScalar 与《AscDuplicate》的实质衔接是：AscDuplicateScalar 把一个 scalar 广播到 RegTensor；Merge/Highest/普通 Duplicate 改变未选中 lane 或来源，标量运算和错例直接约束广播范围与消费方式。
<!-- cannbot:related:end -->
