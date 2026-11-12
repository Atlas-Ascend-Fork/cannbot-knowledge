---
type: API
title: DeepEP Normal dispatch/combine：配套句柄、量化选择与策略差异
description: 定义 Normal token 分发与聚合的数据/scale 契约，记录公开 dispatch 没有 quant_mode 形参、量化标志互斥及
  alltoall 与 default 的差异。
tags:
- task.implementation
- topic.mixture_of_experts
- topic.data_movement.communication.collective_communication
- topic.compute.quantization
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/doc/NORMAL_API.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/buffer.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/device_info.py
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/strategies/normal_strategy.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/README.md
  role: supporting
created_at: '2026-11-08T11:02:02Z'
updated_at: '2026-11-08T11:02:02Z'
platforms:
- a2
- a3
- '950'
aliases:
- DeepEP normal dispatch
- DeepEP combine
---

# DeepEP Normal dispatch/combine：配套句柄、量化选择与策略差异

## 调用顺序与主输入

Normal 模式用于 Prefill/训练的 token 分发与结果聚合。先在同一 Buffer 调用 [get_dispatch_layout](deepep_get_dispatch_layout.md)，再将路由统计、`topk_idx [T,K]`、`topk_weights [T,K]` 与 `x [T,H]` 传入 `dispatch`。典型 `x` 为 BF16，索引为 int64，权重为 float32。

公开入口为 `Buffer.dispatch(x, handle=None, ..., use_fp8=False, use_mxfp4=False, use_mxfp8=False)`。文档虽然给出了 `quant_mode=...` 示例，固定版本的这个公开函数没有该形参；模式字符串是它内部传给策略的参数。调用方应使用实际布尔形参，不直接照抄字符串示例。

返回六项为 `recv_x, recv_topk_idx, recv_topk_weights, num_recv_tokens_per_expert_list, handle, event`。后续专家 FFN 完成后，将计算结果与原始 `handle` 配套交给 `combine`。default 分发目前拒绝非 `None` 的输入 handle；返回 handle 必须原样保留，不能把它当成支持跨批次复用的公开缓存格式。default 的句柄是 tuple，alltoall 的句柄是 dict，不能混传。

## 实际量化选择与布局

`utils._resolve_quant_mode` 首先检查三个量化布尔值：同时为真的数量超过 1 会抛 `ValueError`。文档的“优先级”不能解释为可同时启用多个模式。设备表将 `use_fp8=True` 在 A2/A3 映射为 INT8，在 950 映射为 per-token E4M3；`use_mxfp8`、`use_mxfp4` 仅在表内 950 架构项支持，A2/A3 会拒绝。

全部布尔为假时，Normal Buffer 再读取已弃用的 `DEEP_NORMAL_MODE_USE_INT8_QUANT=1`，否则选择 BF16。传入 `x` 的 dtype 不参与量化模式选择。实际设备探测失败时，当前表允许 `use_fp8` 回退 INT8；这不是新硬件支持的证明。

| 有效模式 | recv_x 的主契约 |
| --- | --- |
| BF16 | BF16 `[T_recv,H]` 单 Tensor |
| INT8 | `(int8 [T_recv,H], float32 [T_recv])` |
| 950 per-token FP8 | `(float8_e4m3fn [T_recv,H], float32 [T_recv])` |
| 950 MXFP8 | FP8 数据与 E8M0 scale，每 32 个 hidden 元素一个 scale |
| 950 MXFP4 | packed FP4 数据，逻辑 hidden 对应半宽物理数据，以及每 32 元素一个 E8M0 scale |

文档与封装对 scale 有展平和二维描述差异；消费方应核对所选后端返回的实际 shape/stride，不能仅由 scale 元素数相等直接传给任意 GMM。

## default 与 alltoall 不共享全部语义

default 根据 `runtime.get_num_rdma_ranks()>1` 选择跨节点路径。该路径的模式守卫只接受 BF16/INT8；具体 A2 跨节点部署文档进一步要求禁用 Normal 量化。源码存在一个模式分支不代表此平台场景已支持。

文档中“alltoall 不支持 MXFP”的概括与同页枚举及固定源码冲突：`AlltoAllNormalCommStrategy._SUPPORTED_QUANT_MODES` 明确接受 `bf16/int8/mx_fp8_e4m3/mx_fp4_e2m1`，但不接受 per-token FP8/E5M2。该事实仅是 Python 路径准入，不是所有平台/软件组合的运行保证。

alltoall 先做路由重排，分别交换量化 scale 与 token，再按本地专家重排；combine 逆重排、反向 alltoall 后按句柄保存的 routing weights 聚合。它在函数内等待 collective work，返回空 `EventOverlap()`。default combine 也主要复用句柄中的原始索引与权重，不能以重新传入 `topk_weights` 保证覆盖句柄权重。

## 范围与验证

Normal API 文档给出的 A2 hidden 为 7168，A3 hidden 范围 1024–7168；专家数不超过 512、top-k 不超过 16，A2 跨节点 top-k 起点为 2。token/长序列和 HCCL 缓冲约束应与[A2 指南](../../guides/integration/sgl_kernel_npu/deepep_a2_communication.md)及实际平台说明一并验收，不能从 Buffer 的默认 Config 表外推出更大规模可用性。

验证要覆盖分发/聚合配对、不同专家负载、量化 data 与 scale 的对应、零 token 的真实后端行为及模式切换。异步参数不构成已建立跨流依赖，见[事件边界](../../guides/integration/sgl_kernel_npu/deepep_buffer_strategies.md)。本次未执行编译、通信、数值或性能测试。

## Evidence

- [python/deep_ep/doc/NORMAL_API.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/doc/NORMAL_API.md)（primary）
- [python/deep_ep/deep_ep/buffer.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/buffer.py)（implementation）
- [python/deep_ep/deep_ep/utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/utils.py)（implementation）
- [python/deep_ep/deep_ep/device_info.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/device_info.py)（constraint）
- [python/deep_ep/deep_ep/strategies/normal_strategy.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/strategies/normal_strategy.py)（implementation）
- [python/deep_ep/README.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/README.md)（supporting）
