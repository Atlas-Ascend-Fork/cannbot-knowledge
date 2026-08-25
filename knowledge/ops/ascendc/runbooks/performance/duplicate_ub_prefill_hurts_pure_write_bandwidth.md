---
type: "Runbook"
title: "UB 预填充 Duplicate 引入 Vector 开销拖慢纯写带宽"
description: "在纯写 HBM 带宽探针的 DataCopy(UB→GM) 前加 Duplicate<half> 预填充 UB，相对原版纯写带宽反而下降约 5%，因 Duplicate 占用 Vector 流水线与 MTE3 串行，不应作为写带宽优化手段。"
tags: ["task.optimization", "topic.data_movement.data_copy", "topic.implementation.pipeline", "topic.performance.analysis"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# UB 预填充 Duplicate 引入 Vector 开销拖慢纯写带宽

## 现象

在 Ascend950PR 上跑 `test/write_only/probe_write.asc` 纯写 HBM 带宽（UB→GM MTE3，`useL2=0`）。kernel 把 `LocalTensor local = buf.Get<half>()` 取出后直接构 `DataCopyParams` 发 `DataCopy(cGm[offset], local, writeParams)`。当时怀疑 UB 未初始化（随机值）让 HBM 控制器对写有不同处理，于是加 `Duplicate<half>(local, (half)1, ...)` 预填充 UB。跑出后纯写带宽反而相对原版下降约 5%（绝对值仅作 provenance，不进正文），随即回退改动。A/B 计时用 msprof MTE3 + NPU event。

## 适用场景

- 工程形态：Kernel 直调（ops-direct-invoke）纯写 HBM 带宽探针，`DataCopy` UB→GM。
- API 路径：`Duplicate<half>`（Vector 流水线）；`DataCopy`（MTE3 写）；`TBuf`/`LocalTensor` UB。
- 验证过的平台与 CANN 版本：Ascend950PR；CANN 9.1.0。
- 适用粒度：operator_family（所有把 UB 数据搬出到 GM 的写带宽/搬运 kernel）。
- 路线优先级：banned（不要在纯写 GM 的 DataCopy 前用 `Duplicate` 预填充 UB 试图提写带宽——会引入 Vector 流水线开销）。
- 不适用或未验证场景：UB 数据本身就是计算结果（已被 Vector 生产）的场景，`Duplicate` 不额外开销；本卡只覆盖"为搬出而预填充"的纯写探针。

## 根因

`Duplicate<half>` 是 Vector 流水线指令，执行时占用 Vector 管线把 UB 填成指定值。在纯写探针里，UB 内容对 HBM 写带宽无影响（HBM 控制器按总线事务写，不关心 payload 初值），但 `Duplicate` 与 `DataCopy`（MTE3）在 kernel 里串行执行，`Duplicate` 的 Vector 执行时间被加进 kernel 总时间，拉低写带宽。即"预填充 UB"没有 HBM 侧收益，只有 Vector 侧开销。

## 失败路线

**banned**：在纯写 GM 的 `DataCopy` 前用 `Duplicate<half>` 预填充 UB 试图提写带宽。

改动（verbatim，edit seq797 NEW）：

```
    LocalTensor<half> local = buf.Get<half>();
    Duplicate<half>(local, (half)1, tileBytes / sizeof(half));

    DataCopyParams writeParams;
```

回退（verbatim，edit seq800 NEW，恢复为不加 Duplicate）：

```
    LocalTensor<half> local = buf.Get<half>();

    DataCopyParams writeParams;
```

## 验证信号

- 加 `Duplicate` 预填充后纯写 HBM 带宽相对原版下降约 5%（参照路线：原版纯写无预填充）（来源平台：Ascend950；证据等级: tool_observed）

## 坏实践

- 为"让 HBM 写有已初始化数据"在纯写探针里加 `Duplicate` 预填充 UB——无 HBM 收益、纯增 Vector 开销。

<!-- cannbot:related:start -->
## 相关

- [AscDuplicate](../../apis/simd_api/c_api/reg/data_fill/asc_duplicate.md)（`exemplifies`）：《UB 预填充 Duplicate 引入 Vector 开销拖慢纯写带宽》的任务是“在纯写 HBM 带宽探针的 DataCopy(UB→GM) 前加 Duplicate<half> 预填充 UB，相对原版纯写带宽反而下降约 5%，因 Duplicate 占用 Vector 流水线与 MTE3 串行，不应作为写带宽优化手段。”。《AscDuplicate》具体提供“将src的最低位元素广播到dst中被mask筛选的位置，未被mask筛选的位置置为0。”，它直接用于纯写带宽中 Duplicate 占用 Vector 流水并与 MTE3 串行的验证。
- [AscDuplicate](../../apis/simd_api/c_api/vector_compute/asc_duplicate.md)（`exemplifies`）：《UB 预填充 Duplicate 引入 Vector 开销拖慢纯写带宽》的任务是“在纯写 HBM 带宽探针的 DataCopy(UB→GM) 前加 Duplicate<half> 预填充 UB，相对原版纯写带宽反而下降约 5%，因 Duplicate 占用 Vector 流水线与 MTE3 串行，不应作为写带宽优化手段。”。《AscDuplicate》具体提供“执行矢量复制（Duplicate）操作，将标量值复制填充到矢量中。”，它直接用于纯写带宽中 Duplicate 占用 Vector 流水并与 MTE3 串行的验证。
- [Duplicate](../../apis/simd_api/basic_api/memory_vector_compute/data_padding/duplicate.md)（`exemplifies`）：《UB 预填充 Duplicate 引入 Vector 开销拖慢纯写带宽》的任务是“在纯写 HBM 带宽探针的 DataCopy(UB→GM) 前加 Duplicate<half> 预填充 UB，相对原版纯写带宽反而下降约 5%，因 Duplicate 占用 Vector 流水线与 MTE3 串行，不应作为写带宽优化手段。”。《Duplicate》具体提供“将变量或立即数复制多次并填充到向量中，支持前n个数据计算和高维切分计算两种方式。”，它直接用于纯写带宽中 Duplicate 占用 Vector 流水并与 MTE3 串行的验证。
- [Duplicate](../../apis/simd_api/basic_api/reg_vector_compute/data_padding/duplicate.md)（`exemplifies`）：《UB 预填充 Duplicate 引入 Vector 开销拖慢纯写带宽》的任务是“在纯写 HBM 带宽探针的 DataCopy(UB→GM) 前加 Duplicate<half> 预填充 UB，相对原版纯写带宽反而下降约 5%，因 Duplicate 占用 Vector 流水线与 MTE3 串行，不应作为写带宽优化手段。”。《Duplicate》具体提供“将标量或源寄存器最低位元素广播到目的寄存器，支持Scalar和Tensor两种模式，可配合mask使用。”，它直接用于纯写带宽中 Duplicate 占用 Vector 流水并与 MTE3 串行的验证。
- [数据填充](../../apis/simd_api/c_api/reg/data_fill/data_fill.md)（`exemplifies`）：该卡量化无必要预填充对纯写带宽的损失。
- [InitOutput GM 专用，UB 清零用 Duplicate](../compilation/initoutput_gm_ub_duplicate.md)（`related`）：《UB 预填充 Duplicate 引入 Vector 开销拖慢纯写带宽》的任务是“在纯写 HBM 带宽探针的 DataCopy(UB→GM) 前加 Duplicate<half> 预填充 UB，相对原版纯写带宽反而下降约 5%，因 Duplicate 占用 Vector 流水线与 MTE3 串行，不应作为写带宽优化手段。”。《InitOutput GM 专用，UB 清零用 Duplicate》具体提供“AscendC InitOutput(GlobalTensor<T>, uint32_t, T) 是 GM 专用清零 API，把 LocalTensor 作为第一参数传入会触发 'no known conversion from LocalTensor to GlobalTensor'；UB LocalTensor 清零应改用 Duplicate(local, value, mask)。判别依据为编译器候选函数 note 显示 InitOutput 唯一签名第一参数为 GlobalTensor<T>。”，它直接用于纯写带宽中 Duplicate 占用 Vector 流水并与 MTE3 串行的验证。
- [L2 读写端口独立并行 HBM 总线串行共享](l2_hbm.md)（`related`）：《UB 预填充 Duplicate 引入 Vector 开销拖慢纯写带宽》的任务是“在纯写 HBM 带宽探针的 DataCopy(UB→GM) 前加 Duplicate<half> 预填充 UB，相对原版纯写带宽反而下降约 5%，因 Duplicate 占用 Vector 流水线与 MTE3 串行，不应作为写带宽优化手段。”。《L2 读写端口独立并行 HBM 总线串行共享》具体提供“Ascend950 L2 的 MTE2 读端口与 MTE3 写端口独立并行（吞吐可相加），HBM 总线被读写共享串行仲裁；并发读写带宽应按总数据量与实际并发时间算，不能把单路带宽相加当并发带宽。”，它直接用于纯写带宽中 Duplicate 占用 Vector 流水并与 MTE3 串行的验证。
<!-- cannbot:related:end -->
