---
type: API
title: DeepEP Low-Latency：容量、有效 token 与量化兼容边界
description: 整理 Decode 分发/聚合的固定容量、专家有效计数和 handle 配对，区分 default、ops、alltoall 的 padding、量化与事件行为。
tags:
- task.implementation
- topic.mixture_of_experts
- topic.compute.quantization
- topic.implementation.synchronization
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/doc/LOW_LATENCY_API.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/buffer.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/device_info.py
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/strategies/low_latency_strategy.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/deepep/deep_ep.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/deepep/ops/op_kernel/moe_distribute_dispatch_v2.h
  role: implementation
created_at: '2026-11-08T11:02:02Z'
updated_at: '2026-11-09T04:31:21Z'
platforms:
- a2
- a3
- '950'
aliases:
- low_latency_dispatch
- low_latency_combine
---

# DeepEP Low-Latency：容量、有效 token 与量化兼容边界

## 分发与聚合接口

`low_latency_dispatch(x, topk_idx, num_max_dispatch_tokens_per_rank, num_experts, ..., use_fp8=True, use_mxfp4=False, use_mxfp8=False)` 面向 Decode。`x` 典型为 BF16 `[T,H]`，专家索引为 int64 `[T,K]`；`capacity=num_max_dispatch_tokens_per_rank` 在 EP group 各 rank 必须一致。

返回 `recv_x, recv_count, handle, event, hook`。default 路径的 `recv_count [E_local]` 在 `MOE_EXPERT_TOKEN_NUMS_TYPE=1`（未设置时默认值）下表示每专家实际 token 数；设为 `0` 时返回专家计数前缀和，须以前缀差分（首项直接取值）得到每专家有效长度，容量区并非所有行都有效，专家计算必须只消费有效范围。`low_latency_combine(x, topk_idx, topk_weights, handle, ...)` 使用同一次 dispatch 的索引、路由权重与原样 handle，输出原始本地 token 数的 BF16 结果。Normal handle 与 Low-Latency handle 不能互换。

API 文档给出 `T<=512` 且 `T<capacity`；A2 hidden 为正且不超过 7168，并需 32 元素对齐。A2 跨节点 top-k 为 2–16，单节点和 A3 为 1–16，专家数不超过 512。其他具体平台容量值仍以选中 backend 的约束为准，不能借模型 batch 小就忽略全 rank 统一容量。

## 量化以固定源码为准

Buffer 共用 `_resolve_quant_mode`，三个量化布尔互斥。950 的 `use_fp8=True` 选择 per-token FP8，A2/A3 为 INT8；950 MXFP8/MXFP4 要显式启用对应标志并关闭默认的 `use_fp8`，否则会因多个标志为真而失败。BF16 调用同样需要显式 `use_fp8=False`。

来源文档称 LL 支持已弃用环境变量回退，并将 `use_fp8=True,use_ue8m0=True` 解释为 MXFP8 别名；当前 Buffer 先用三个布尔解析模式，未把 `use_ue8m0` 传入解析器，也未在 LL Buffer/default Python 策略读取该环境变量。底层仍会接收到 legacy 标志，但仅凭此无法保证文档中的别名和回退解析成立。集成应使用显式 `use_mxfp8`，并检查目标 C++ 返回格式；本卡不把冲突行为作为稳定兼容承诺。

default 的量化返回为 `(data, scales)`：INT8/per-token FP8 为每 token 的 float32 scale，MXFP 为每 32 个 hidden 元素的 E8M0 scale；非量化为单 Tensor。数据类型、shape、scale 与 GMM 消费方式需要成组核对。

## 三种策略的关键差异

| 路径 | Python 可见行为 |
| --- | --- |
| `default` | 把解析后的模式、异步标志和 hook 标志交给 C++ runtime；返回其 packed 计数与事件/hook |
| `ops` | 将输入补齐到 capacity，创建 active mask 和配套 padding 索引/权重，调用 torch_npu dispatch/combine v2；聚合后裁回原长度 |
| `alltoall` | 先按固定 expert capacity 路由，交换整块数据，再重排；`recv_count` 被填成 `capacity×R`，不能视作 default 的真实有效计数 |

ops 的 `comm_alg="hierarchy"` 需要 `topk_weights`；当前实现随后无条件构造其 padding，因此不要假定省略该参数总可用。ops 仍按 `use_fp8/use_ue8m0` 构造自己的量化枚举，不能把 default 的模式字符串直接当作其结果格式。

alltoall 的模式白名单为 BF16/INT8/MXFP8 E4M3/MXFP4，量化发生在交换后，因此启用量化不意味着该路径的通信数据已量化。其 `low_latency_combine(use_mxfp8=True)` 会明确拒绝；ops 与 default 对这个参数的转发另行处理。

## 事件、窗口与验收

ops 返回的 hook 是空函数，alltoall 也返回空 hook/事件；default 是否有实际异步接收要继续核对 C++ backend。`EventOverlap.current_stream_wait()` 当前为空实现，不能据返回对象建立跨流顺序。同一 EP group 混用 Normal/LL 的窗口配置见[Buffer 指南](../../guides/integration/sgl_kernel_npu/deepep_buffer_strategies.md)。

验收应比较不同本地 T、相同 capacity、专家负载为零和 capacity 尾部，分别检查每个策略的数据有效范围与输出裁切。这里的容量约束和源码观察不代表实测，本次未执行编译、通信、数值或性能测试。

## Evidence

- [python/deep_ep/doc/LOW_LATENCY_API.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/doc/LOW_LATENCY_API.md)（primary）
- [python/deep_ep/deep_ep/buffer.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/buffer.py)（implementation）
- [python/deep_ep/deep_ep/utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/utils.py)（implementation）
- [python/deep_ep/deep_ep/device_info.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/device_info.py)（constraint）
- [python/deep_ep/deep_ep/strategies/low_latency_strategy.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/strategies/low_latency_strategy.py)（implementation）
