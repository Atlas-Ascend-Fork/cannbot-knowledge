---
type: API
title: AscDuplicate
description: 将src的最低位元素广播到dst中被mask筛选的位置，未被mask筛选的位置置为0。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_fill/asc_duplicate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscDuplicate

将src的最低位元素广播到dst中被mask筛选的位置，dst中未被mask筛选的位置被置为0。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、fp8_e4m3fn_t、fp8_e5m2_t、fp8_e8m0_t、half、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Duplicate 广播枚举与模板顺序不兼容](../../../../../runbooks/compilation/reg_duplicate_highlow_precedes_merge_mode.md)（`exemplifies`）：该卡给出 high/low 与 MergeMode 模板参数次序的编译诊断。
- [InitOutput GM 专用，UB 清零用 Duplicate](../../../../../runbooks/compilation/initoutput_gm_ub_duplicate.md)（`exemplifies`）：InitOutput GM 专用，UB 清零用 Duplicate 与《AscDuplicate》的实质衔接是：InitOutput 只接受 GM GlobalTensor，而 UB LocalTensor 要用 Duplicate；相关 API、类型错误、TBuf 取 LocalTensor 和清零覆盖故障直接验证该边界。
- [UB 预填充 Duplicate 引入 Vector 开销拖慢纯写带宽](../../../../../runbooks/performance/duplicate_ub_prefill_hurts_pure_write_bandwidth.md)（`exemplifies`）：《UB 预填充 Duplicate 引入 Vector 开销拖慢纯写带宽》的任务是“在纯写 HBM 带宽探针的 DataCopy(UB→GM) 前加 Duplicate<half> 预填充 UB，相对原版纯写带宽反而下降约 5%，因 Duplicate 占用 Vector 流水线与 MTE3 串行，不应作为写带宽优化手段。”。《AscDuplicate》具体提供“将src的最低位元素广播到dst中被mask筛选的位置，未被mask筛选的位置置为0。”，它直接用于纯写带宽中 Duplicate 占用 Vector 流水并与 MTE3 串行的验证。
- [AscDuplicate](../../vector_compute/asc_duplicate.md)（`same_topic`）：Vector C API 与 Reg C API 都做标量广播，但输出载体不同。
- [AscDuplicateHighest](asc_duplicate_highest.md)（`same_topic`）：AscDuplicateHighest 与《AscDuplicate》的实质衔接是：AscDuplicateHighest 从 src 最高 lane 广播到 mask 选中位置；Merge/Scalar/普通 Duplicate 的来源与未选中位置处理不同，相关错例直接约束枚举、范围和归约结果广播。
- [AscDuplicateMerge](asc_duplicate_merge.md)（`same_topic`）：Merge 版本保留未命中 mask 的目的值，而普通版本执行 zeroing。
- [AscDuplicateScalar](asc_duplicate_scalar.md)（`same_topic`）：AscDuplicateScalar 与《AscDuplicate》的实质衔接是：AscDuplicateScalar 把一个 scalar 广播到 RegTensor；Merge/Highest/普通 Duplicate 改变未选中 lane 或来源，标量运算和错例直接约束广播范围与消费方式。
- [Duplicate](../../../basic_api/reg_vector_compute/data_padding/duplicate.md)（`same_topic`）：C Reg API AscDuplicate 是 C++ Reg Duplicate 的直接对应入口。
- [数据填充](data_fill.md)（`same_topic`）：DataFill 总页中的基础广播入口。
<!-- cannbot:related:end -->
