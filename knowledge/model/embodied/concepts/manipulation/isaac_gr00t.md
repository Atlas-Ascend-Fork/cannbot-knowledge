---
type: Concept
title: Isaac GR00T N1.6（双系统 VLA · A3 推理图模式优化）
description: cann-recipes-embodied-ai 的操作类通用机器人基础模型样例：NVIDIA Isaac GR00T N1.6 在 Atlas A3 上的昇腾迁移与推理性能优化。一手源：manipulation/Isaac-GR00T/README.md 与 docs/manipulation/GR00T N1.6/README.md。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.graph_execution
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-embodied-ai/21a5ed789ceb2a4b72277573f5ec5ec531b92ee1/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-embodied-ai/21a5ed789ceb2a4b72277573f5ec5ec531b92ee1/manipulation/Isaac-GR00T/README.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-embodied-ai/21a5ed789ceb2a4b72277573f5ec5ec531b92ee1/docs/manipulation/GR00T N1.6/README.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-embodied-ai/21a5ed789ceb2a4b72277573f5ec5ec531b92ee1/manipulation/Isaac-GR00T/adaptor_patches/modeling_siglip2_patch.py
  role: implementation
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-10-29T15:24:37Z'
platforms:
- a3
---

# Isaac GR00T N1.6（双系统 VLA · A3 推理图模式优化）

`cann-recipes-embodied-ai` 的操作类通用机器人基础模型样例：**NVIDIA Isaac GR00T N1.6** 在 **Atlas A3** 上的昇腾迁移与推理性能优化。一手源：`manipulation/Isaac-GR00T/README.md` 与 `docs/manipulation/GR00T N1.6/README.md`。

> GR00T N1.6（2025-12 发布）是通用人形机器人基础模型，旨在突破传统 VLA 在长程具身操作中的泛化瓶颈、解决小样本下动作生成的时序一致性问题。论文 arXiv:2503.14734。上游 https://github.com/NVIDIA/Isaac-GR00T，样例固定 commit `e29d8fc50b0e4745120ae3fb72447986fe638aa6`，再覆盖本仓 `manipulation/Isaac-GR00T/*` 适配文件。CANN `8.3.RC1`，目标平台 **Atlas A3 系列**（[atlas-a3](../../../inference/concepts/platforms/atlas_a3.md)，torch 在线推理 + 图模式；非 310P OM 离线）。

## 双系统结构

GR00T N1.6 由 **慢系统 + 快系统** 两部分串行组成（源 doc）：

- **慢系统**：`Cosmos-Reason-2B`，含视觉编码器、多模态投影适配器、LLM 基座解码器、跨模态双向融合层四部分；
- **快系统**：一个 **扩散 Transformer（DiT）** 模型，并行去噪生成动作序列。

动作生成属扩散动作范式（对照 [flow-matching-action-expert](../modules/flow_matching_action_expert.md) 的流匹配、[action-chunking](../modules/action_chunking.md) 的整段块预测）。DiT 结构详见 [dit](../../../inference/concepts/modules/dit.md)。

测试输入：单视角 RGB 图像 + 机器人本体状态 + 语言文本指令（docs 推荐 `demo_data/gr1.PickNPlace`，4 去噪步；脚本 `standalone_inference_script.py` argparse 内置默认实为 `demo_data/robot_sim.PickNPlace/`）；输出：每步 `16×29` 关节角度序列（双手、双臂、腰等关节）。

## 昇腾迁移（开箱打通）

基于 `torch_npu` 自动适配原始代码（`import torch_npu; from torch_npu.contrib import transfer_to_npu`），并把 flash-attention 相关算子替换为昇腾融合算子、把 NPU 不支持的 `float64` 替换为 `float32`，即可快速打通推理并保证精度达标。

## 性能优化（A3 单卡）

开箱 profiling（torch_npu.profiler + MindStudio Insight）发现：空闲时间占比过大、计算占比不到 20%，device 一直等待指令下发，存在 **host-bound** 问题；`AI_CORE` 算子占比小（昇腾亲和的融合大算子少，未发挥 Cube 单元），`transpose`/`cast` 等算子分别占约 16%/10%。优化策略：

- **图模式使能（torchair）**：backbone 含大量动态操作无法整图编译，仅对 **action head** 部分编译后一次性下发指令，减少 device 等待。`standalone_inference_script.py` 对 `policy.model.action_head.model` 用 `torch.compile(..., backend="npugraphs", fullgraph=True, dynamic=False)`；`adaptor_patches/gr00t_n1d6_patch.py` 另用 `torchair.get_npu_backend(compiler_config=...)`（`frozen_parameter=True`、`tiling_schedule_optimize=True`）。首步推理增加约两分钟图编译时间，后续推理步大幅提速。在线图模式详见 [npu-graph-mode](../../../inference/concepts/techniques/npu_graph_mode.md)、[torchair](../../../inference/concepts/frameworks/torchair.md)。
- **FA 融合算子替换**：在 `modeling_siglip2.py` 用猴子补丁换 `npu_fused_infer_attention_score` 融合算子，复用 NPU 快速 attention 计算。跨链 [fused-infer-attention-score](../../../inference/concepts/kernels/fused_infer_attention_score.md)。
- **RoPE sin/cos 计算逻辑优化**：改写 `apply_rope`，用 `torch_npu.npu_rotary_mul` 融合算子，固定 apply_rope_npu 对 Q、K 分别调用一次 npu_rotary_mul，没有先合并再拆分，并把 sin/cos 计算提到 for 循环外统一计算、减少重复。
- **LayerNorm 原生算子优化**：把 layernorm+add 替换为 `npu_add_rms_norm` 融合算子，`layer.input_layernorm` 用昇腾原生 `npu_rms_norm`（`NpuRMSNorm` 模块在 NPU 上走 `torch_npu.npu_rms_norm`）。注：`npu_add_rms_norm` 系 docs 表述；当前钉定版代码仅落地 `npu_rms_norm`（`NpuRMSNorm.forward` 调 `torch_npu.npu_rms_norm`），add 融合未在 patch 中体现。

**优化结果**：基于 MindStudio Insight profiling，A3 上计算时间总占比从开箱 <20% 提升至约 **70%**，单次推理计算总耗时从开箱 **280ms 降至 82ms**。

## 关联

- 双系统动作生成范式对照：[flow-matching-action-expert](../modules/flow_matching_action_expert.md)、[action-chunking](../modules/action_chunking.md)
- 同走 torch 在线 + 昇腾算子化路线：[spirit-v1.5](spirit_v1_5.md)、[openvla](openvla.md)
- cann-infer 复用概念：[dit](../../../inference/concepts/modules/dit.md)、[npu-graph-mode](../../../inference/concepts/techniques/npu_graph_mode.md)、[torchair](../../../inference/concepts/frameworks/torchair.md)、[fused-infer-attention-score](../../../inference/concepts/kernels/fused_infer_attention_score.md)
- 源：[cann-recipes-embodied-ai](https://gitcode.com/cann/cann-recipes-embodied-ai/tree/21a5ed789ceb2a4b72277573f5ec5ec531b92ee1)
