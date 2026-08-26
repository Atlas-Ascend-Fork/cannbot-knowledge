---
type: Concept
title: TorchAir
description: '**Torch Ascend Intermediate Representation**，是 Ascend Extension for PyTorch（torch_npu）的图模式能力扩展库，提供昇腾设备亲和的 `torch.compile` 后端，实现 PyTorch 网络在 NPU 上的图模式推理加速与性能优化。 DeepSeek-R1 Decode 阶段走 TorchAir 图模式以规避 eager 下的 host 下发 bound，是 W8A8C8 + MTP1 benchmark 达到 TPOT 44.9 ms 的基础条件之一。'
tags:
- task.implementation
- topic.architecture
- topic.graph_execution
- topic.speculative_decoding
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-r1/deepseek_r1_decode_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-06-27T00:00:00Z'
platforms:
- a3
---

# TorchAir

## Summary

**Torch Ascend Intermediate Representation**，是 Ascend Extension for PyTorch（torch_npu）的图模式能力扩展库，提供昇腾设备亲和的 `torch.compile` 后端，实现 PyTorch 网络在 NPU 上的图模式推理加速与性能优化。

DeepSeek-R1 Decode 阶段走 TorchAir 图模式以规避 eager 下的 host 下发 bound，是 W8A8C8 + MTP1 benchmark 达到 TPOT 44.9 ms 的基础条件之一。

## Architecture

TorchAir 提供两种实现模式，由 YAML `exe_mode` 配置：

| `exe_mode` | TorchAir 模式 | 别名 | 性质 | | ---- | ---- | ---- | ---- | | `ge_graph` | **max-autotune** | GE 图模式 | 最激进优化，支持 SuperKernel、整图融合，编译耗时更长 | | `npugraph_ex` | **reduce-overhead** | ACL Graph | 以极低开销重放预录图，更接近 CUDA Graph 语义，迭代快 | | `eager` | — | eager | 不走图模式，调试用 |

DeepSeek-R1 `decode_r1_rank_128_128ep_a8w8c8_mtp_benchmark.yaml` 默认 `ge_graph` + `enable_superkernel: True`；`decode_r1_rank_16_16ep_a8w8.yaml` 默认 `npugraph_ex` + `enable_static_kernel: False`。

> 命名差异：decode 优化文档散文把 reduce-overhead 模式称作 `acl_graph`（`其中ge_graph对应max-autotune模式，acl_graph对应reduce-overhead模式`），但实际可配置的 `exe_mode` 枚举字段为 `npugraph_ex`（R1 各 YAML 注释一律为 `["eager", "npugraph_ex", "ge_graph"]`，无 `acl_graph`）。以 YAML 字段为准 —— 按文档散文去 YAML 填 `acl_graph` 会失败。

## Key Features

- `torch.compile` 后端：保持 PyTorch 标准编程模型，无需手改为静态 graph。
- **max-autotune**：类似 CUDA max-autotune，做整图 tiling、常量折叠、op-fusion；配合 [superkernel](../techniques/superkernel.md) 进一步把多算子融合为单 kernel。
- **reduce-overhead**：类似 CUDA Graph，图一次构建多次重放，降低 launch 开销；需要静态 shape + 稳定 control flow。
- `enable_cache_compile`：编译缓存，缩短重复拉起时的预热时间。
- **集合通信 AIV 展开**（同列于 decode 图模式优化清单的配套通信优化，非 TorchAir 本体）：`export HCCL_OP_EXPANSION_MODE=AIV`，利用 Device 的 Vector Core 计算单元加速通信操作执行，与 `ge_graph` 整图调度配合。详见 [multi-stream](../techniques/multi_stream.md)。

## Usage Scenarios

- Decode 阶段 host 下发紧张 → `ge_graph` 或 `npugraph_ex`。
- 大 EP + MoE + 多流场景下 task 数爆炸 → `ge_graph` + SuperKernel。
- 迭代调试 / eager 功能验证 → `exe_mode: "eager"`。

## Constraints

- **SuperKernel 仅在 `ge_graph` 下生效**，`npugraph_ex` 不支持。
- `npugraph_ex` 要求图结构稳定，动态 shape / control flow 会频繁重建图。
- Prefill 阶段的 micro-batch 双流与图模式的互动 source 未详细说明；实测 R1 prefill YAML 仅 `exe_mode: "ge_graph"`（`prefill_r1_rank_32_32dp_32ep_a8w8.yaml`）已经配合 micro_batch_mode=1 使用。
- 与 [mtp-speculative-decoding](../techniques/mtp_speculative_decoding.md) 的互动：Qwen3-Next 的 MTP 与图模式互斥（`--cuda-graph-bs` 不可同开），但 DeepSeek-R1 `decode_r1_rank_128_128ep_a8w8c8_mtp.yaml` 同时启用 MTP1 + `ge_graph`，**说明 R1 路径下 TorchAir + MTP 可以共存**，与 Qwen3-Next 场景不同。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-r1/deepseek_r1_decode_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-r1/deepseek_r1_decode_optimization.md) "torchair 图模式"章节；[TorchAir 官方文档](https://www.hiascend.com/document/detail/zh/Pytorch/710/modthirdparty/torchairuseguide/torchair_00003.html)；`models/deepseek_r1/config/*.yaml` 中 `exe_mode` 字段。

## Links

- [deepseek-r1](../models/deepseek_r1.md)
- [qwen3-5-moe](../models/qwen3_5_moe.md)
- [superkernel](../techniques/superkernel.md)
- [mtp-speculative-decoding](../techniques/mtp_speculative_decoding.md)
- [atlas-a3](../platforms/atlas_a3.md)
- [autofuse](autofuse.md)（Inductor NPU 后端的自动融合路径，与本库的 GE / npugraph_ex 图后端并列）
- [vllm-ascend](../../../training/concepts/frameworks/vllm_ascend.md)（跨域·训练：vLLM-Ascend rollout 用 torchair 图模式(additional_config)）
- [hunyuan3d](../../../spatial/concepts/models/hunyuan3d.md)（跨域·空间智能：Hunyuan3D --full_graph 经 torchair 入图）
- [multi-stream](../techniques/multi_stream.md)（torchair.scope 的 npu_stream_switch / npu_wait_tensor / limit_core_num 是 ge_graph 多流的接口）
- 跨域·具身：[pi0](../../../embodied/concepts/manipulation/pi0.md)、[isaac-gr00t](../../../embodied/concepts/manipulation/isaac_gr00t.md)、[pi05](../../../embodied/concepts/manipulation/pi05.md)、[om-atc-offline](../../../embodied/concepts/techniques/om_atc_offline.md)、[flow-matching-action-expert](../../../embodied/concepts/modules/flow_matching_action_expert.md)（VLA 在线推理经 torchair 整图编译）
