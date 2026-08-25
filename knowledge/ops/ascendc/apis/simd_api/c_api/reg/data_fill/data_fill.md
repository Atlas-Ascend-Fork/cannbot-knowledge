---
type: API
title: 数据填充
description: 寄存器侧数据填充类接口汇总，提供duplicate及其标量、合并、高位合并等多种数据广播填充能力。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_fill/data_fill.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 数据填充

寄存器侧数据填充接口提供数据广播与填充能力。asc_duplicate将数据复制填充到目标寄存器，asc_duplicate_scalar以标量值填充。
_merge变体（asc_duplicate_merge/asc_duplicate_scalar_merge/asc_duplicate_highest_merge）支持与已有数据合并填充；_highest变体（asc_duplicate_highest）填充高位数据。

<!-- cannbot:related:start -->
## 相关

- [InitOutput GM 专用，UB 清零用 Duplicate](../../../../../runbooks/compilation/initoutput_gm_ub_duplicate.md)（`exemplifies`）：InitOutput GM 专用，UB 清零用 Duplicate 与《数据填充》的实质衔接是：InitOutput 只接受 GM GlobalTensor，而 UB LocalTensor 要用 Duplicate；相关 API、类型错误、TBuf 取 LocalTensor 和清零覆盖故障直接验证该边界。
- [Softmax 手工尾填充会触发 Vector 异常](../../../../../runbooks/compilation/softmax_manual_tail_fill_route_vector_exception.md)（`exemplifies`）：该卡展示 tail fill 路线参数/地址错误导致向量异常。
- [UB 预填充 Duplicate 引入 Vector 开销拖慢纯写带宽](../../../../../runbooks/performance/duplicate_ub_prefill_hurts_pure_write_bandwidth.md)（`exemplifies`）：该卡量化无必要预填充对纯写带宽的损失。
- [AscDuplicate](asc_duplicate.md)（`same_topic`）：DataFill 总页中的基础广播入口。
- [AscDuplicateMerge](asc_duplicate_merge.md)（`same_topic`）：Merge 版本保留未命中 mask 的旧值。
<!-- cannbot:related:end -->
