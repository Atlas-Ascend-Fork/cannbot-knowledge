---
type: API
title: DeepEP get_dispatch_layout：Normal 路由统计与返回值边界
description: 整理 Normal dispatch 前的专家与 rank 计数、输入连续性和分整除要求，区分文档预留的 RDMA/事件字段与不同 Python
  策略的实际行为。
tags:
- task.implementation
- topic.mixture_of_experts
- topic.compute.indexing
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/doc/GET_DISPATCH_LAYOUT_API.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/buffer.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/strategies/normal_strategy.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/deepep/deep_ep.cpp
  role: implementation
created_at: '2026-11-08T11:02:02Z'
updated_at: '2026-11-09T04:30:33Z'
platforms:
- a2
- a3
- '950'
aliases:
- get_dispatch_layout
---

# DeepEP get_dispatch_layout：Normal 路由统计与返回值边界

## 接口与用途

`Buffer.get_dispatch_layout(topk_idx, num_experts, previous_event=None, async_finish=False, allocate_on_comm_stream=False)` 为随后同一 Buffer 的 Normal dispatch 计算路由统计。文档声明支持 A2/A3/A5；其 A2/A3 数值边界不能自动扩展为 950 的精确上限。

`topk_idx` 为 NPU 上连续的 `int64 [T,K]`，文档要求 `K∈[1,16]`、全局专家数 `E∈[1,512]`，且 `E` 能被 rank 数整除。接口说明给出的 token 范围为 A2 跨节点至 4096、单节点至 8192；A3 非长序列至 8192、长序列至 32k。A2 配置指南另给 Normal 单机 8000 的场景上限，见[A2 指南](../../guides/integration/sgl_kernel_npu/deepep_a2_communication.md)，不能用 layout 容量单独证明整个算子链可用。

## 五个返回值及配套关系

| 返回值 | 文档形状或含义 |
| --- | --- |
| `num_tokens_per_rank` | `int32 [R]`，本 rank 的 token 对各目标 rank 的分配量 |
| `num_tokens_per_rdma_rank` | RDMA rank 计数预留字段，来源 API 文档称当前为 `None` |
| `num_tokens_per_expert` | 文档为 `int32 [E]`；default 实际为展平的 `int32 [round*E]`，保留逐轮全局专家计数；alltoall 为汇总所有来源 rank 的本地专家计数 `[E/R]` |
| `is_token_in_rank` | 文档声明 `bool [T,R]`；default 实际返回 `int32 [T,R]` 通知矩阵；alltoall 返回同形状 bool 零占位 |
| `event` | 事件封装；来源 API 文档称底层事件当前未使用 |

这些张量应作为一组传给后续 [dispatch](deepep_normal_dispatch_combine.md)，不要把专家计数和 rank 计数互换。

## 策略差异与证据边界

API 说明将 `previous_event`、异步和通信流分配参数描述为预留；当前 Python `DefaultNormalCommStrategy.get_dispatch_layout` 仍把它们透传给 runtime，并返回 `EventOverlap(event)`。这只证明参数传递，未证明底层实现了异步或 RDMA 计数，不能把封装对象存在解释成有效事件。

`alltoall` 策略使用专家直方图、all-gather、split 列表与局部专家索引计算，并把后续 dispatch 所需信息写进 `self._alltoall_layout`。它返回 `num_tokens_per_rdma_rank=None` 与空的 `EventOverlap()`；返回的 `num_tokens_per_expert` 是对全部来源 rank 求和后的本地专家计数 `[E/R]`，并非本 rank 对全局 E 个专家的发送计数；返回的 `is_token_in_rank` 是 bool 零初始化占位。因此该策略的统计不能脱离内部缓存，当作 default runtime 的通知矩阵直接使用。再次调用 layout 会更新缓存，应使 layout 与随后 dispatch 属于同一批输入。

## 验证信号

对小规模已知专家路由先人工计算每专家和每 rank 计数，再对照返回值；覆盖同 token 多专家落在同 rank、`-1` 路由与本地专家数为 1 的场景，具体特殊值支持还须核对目标策略。事件接口限制见[Buffer 指南](../../guides/integration/sgl_kernel_npu/deepep_buffer_strategies.md)。本次未执行上述测试，也未验证设备实现中的多核算法。

## Evidence

- [python/deep_ep/doc/GET_DISPATCH_LAYOUT_API.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/doc/GET_DISPATCH_LAYOUT_API.md)（primary）
- [python/deep_ep/deep_ep/buffer.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/buffer.py)（implementation）
- [python/deep_ep/deep_ep/strategies/normal_strategy.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/strategies/normal_strategy.py)（implementation）
