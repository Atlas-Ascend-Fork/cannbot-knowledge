---
type: Concept
title: Cosmos-Transfer2.5-2B 视频风格转换世界模型（昇腾 A3）
description: Cosmos-Transfer2.5-2B 是 NVIDIA Cosmos 平台的世界基础模型之一，是面向物理 AI 的多控制网络（multi-controlnet）视频风格转换模型：基于深度图、语义分割、边缘检测等多种控制信号，对输入视频做 video-to-video 的风格迁移与内容转换，输入可同时接收 RGB / depth / segmentation / edge 等多模态结构化信号，用于自动驾驶场景模拟、机器人视觉仿真、视频内容创作。cann-recipes-embodied-ai 提供昇腾 Atlas A3 上的 NPU 适配优化，重点是 CFG 并行 + 上下文并行 + NPU 融合算子适配。
tags:
- task.design
- topic.model_architecture
- topic.multimodal
- topic.diffusion
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/world_model/cosmos-transfer2.5/README.md
  role: supporting
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-09-03T13:55:44Z'
platforms:
- a3
---

# Cosmos-Transfer2.5-2B 视频风格转换世界模型（昇腾 A3）

## Summary

Cosmos-Transfer2.5-2B 是 NVIDIA Cosmos 平台的世界基础模型之一，是面向物理 AI 的**多控制网络（multi-controlnet）视频风格转换模型**：基于深度图、语义分割、边缘检测等多种控制信号，对输入视频做 video-to-video 的风格迁移与内容转换，输入可同时接收 RGB / depth / segmentation / edge 等多模态结构化信号，用于自动驾驶场景模拟、机器人视觉仿真、视频内容创作。`cann-recipes-embodied-ai` 提供昇腾 Atlas A3 上的 NPU 适配优化，重点是**CFG 并行 + 上下文并行 + NPU 融合算子适配**。

> 模型本体来自 NVIDIA 官方仓 `nvidia-cosmos/cosmos-transfer2.5`（checkout `8b0e6af4...`）。昇腾适配来自 `cann-recipes-embodied-ai/world_model/cosmos-transfer2.5/`，与 [cosmos-predict2.5](cosmos_predict2_5.md) **共用** `cann-recipes-embodied-ai/docs/world_model/Cosmos/README.md` 多卡并行优化文档。

## 架构定位

- **DiT 扩散主干**：去噪网络为 DiT（`cosmos_transfer2/_src/predict2/networks/minimal_v4_dit.py`），并叠加多控制网络分支（`minimal_v4_lvg_dit_control_vace_patch.py`，VACE 风格 control 注入）；参见 cann-infer [dit](../../../inference/concepts/modules/dit.md)。
- **VLM 文本编码器**：Qwen2.5-VL 系（`cosmos_transfer2/_src/reason1/networks/qwen2_5_vl.py`）。

## 昇腾 NPU 适配（与 Predict 的差异）

适配同样靠 `npu_adapt.sh` 触发的 patch 文件（非侵入式），`adaptor_patches/` 下含 `inference_patch.py` / `graph_patch.py` / `minimal_v4_dit_patch.py` / `minimal_v4_lvg_dit_control_vace_patch.py` / `qwen2_5_vl_patch.py`。

### 融合算子（与 Predict 对照）

下表对照的是 **VLM 文本编码器（Qwen2.5-VL）的注意力路径**与 DiT 侧的归一化/旋转编码算子，**不是 DiT 去噪注意力**：

| 算子 | Transfer 侧 | 与 Predict 差异 |
|------|------------|----------------|
| VLM(Qwen2.5-VL)注意力 | `qwen2_5_vl_patch.py` 把 `Qwen2_5_VLFlashAttention2.forward` 替换为走原生 `F.scaled_dot_product_attention(..., is_causal=True)`（旁路 FlashAttention-2） | Predict 同样 patch `Qwen2_5_VLFlashAttention2.forward`，但走 `torch_npu.npu_fusion_attention(..., input_layout='BNSD', sparse_mode=2)` 融合算子；**两侧都是 VLM 注意力替换，Transfer 走 SDPA、Predict 走融合 FA** |
| RMSNorm（DiT） | `torch_npu.npu_rms_norm` | 与 Predict 一致 |
| Rotary（DiT） | `torch_npu.npu_rotary_mul` | 与 Predict 一致 |

> **DiT 去噪注意力不在本表对照范围**：Transfer 与 Predict 的 DiT 注意力两侧都走 `minimal_v4_dit_patch.py` 的 `Attention.compute_qkv`（backend `transformer_engine`，经 VACE patch 重定向为 `minimal_a2a`），既未换成 SDPA 也未换成 `npu_fusion_attention`。VLM 侧 FA / SDPA 路径选择见 cann-infer [fused-infer-attention-score](../../../inference/concepts/kernels/fused_infer_attention_score.md)。

DiT 侧 RMSNorm/Rotary 两个融合算子是 Transfer/Predict 共用的算子适配核心，承重机制：`minimal_v4_dit_patch.py` 用自定义 `class RMSNorm`（forward `torch_npu.npu_rms_norm(x, self.weight.float(), epsilon=self.eps)[0]`）替换 TransformerEngine 的 `te.pytorch.RMSNorm`，并重写 `apply_rotary_pos_emb`（`cos=torch.cos(radians); sin=torch.sin(radians)` 后 `torch_npu.npu_rotary_mul(x, cos, sin)`）经 `Attention.compute_qkv = patch_compute_qkv` 落地；`npu_adapt.sh` 第一步用 `sed 's/te.pytorch.RMSNorm/RMSNorm/g'` 并删 TE 版本判断块，整体剥离 transformer_engine 依赖。

### 计算图捕获

`adaptor_patches/graph_patch.py` 重写了 TransformerEngine 的 `make_graphed_callables`，使其适配 **inference-only** 计算图捕获（基于 `torch._C._graph_pool_handle` 的 CUDA-graph 式静态图复用）。这是 Transfer 独有的计算逻辑优化，**与昇腾 torchair 图模式不是同一机制**（不要与 [npu-graph-mode](../../../inference/concepts/techniques/npu_graph_mode.md) 混淆）。该图捕获把多个 callable 编排为可复用图，配合多流可降低分发开销，思路与 cann-infer [multi-stream](../../../inference/concepts/techniques/multi_stream.md) 的调度优化目标相通。

## 多卡并行使能（CFG 并行核心改造在本模型）

`enable_cfg_parallel` 的实现位于 **Transfer 的 `inference_patch.py`**：

- 配置层 `cosmos_transfer2/config.py` 的 `SetupArguments` 新增 `enable_cfg_parallel: bool = False`。
- 推理层 `Control2WorldInference.__init__` 改造：当 `enable_cfg_parallel=True` 时，`parallel_state.initialize_model_parallel(context_parallel_size = args.context_parallel_size // 2)` —— 把总卡对半分，一半跑 conditional、一半跑 unconditional 去噪；`enable_cfg_parallel=False` 时全部卡用于上下文并行。例如 8 卡：CFG 并行模式下 `context_parallel_size=4`（4 卡 condition + 4 卡 unconditional）。
- `cfg_parallel` 标志下传给 `ControlVideo2WorldInference` 流水线。

```bash
ASCEND_RT_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 torchrun --nproc_per_node=8 --master_port=12341 \
  examples/inference.py -i assets/robot_example/multicontrol/robot_multicontrol_spec.json \
  -o outputs/multicontrol --disable-guardrails
```

- **CFG 并行**：原理见 cann-infer [cfg-parallel](../../../inference/concepts/parallelism/cfg_parallel.md)，本模型用于条件/无条件去噪分组扩展集群。
- **上下文并行**：跨设备切分长序列视频帧，见 cann-infer [context-parallel](../../../inference/concepts/parallelism/context_parallel.md)（序列并行变体 [ulysses](../../../inference/concepts/parallelism/ulysses.md) / [ring-attention](../../../inference/concepts/parallelism/ring_attention.md)）。

## 精度验证

- 与 NVIDIA 平台输出视频逐帧对比观察一致性。
- **PAI-Bench-C（Conditional Video Generation）** 评估，README 参考分数区间：blur_ssim [0.82,0.84]、canny_f1_score [0.32,0.35]、depth_si_rmse [0.90,0.95]、seg_m_iou [0.66,0.68]。PAI-Bench 为外部基准框架。

## 环境要点

- CANN `8.3.RC1`（cann-toolkit + Atlas-A3 cann-kernels）；`uv sync`；ffmpeg 4.4.2 + decord 0.6.0 + libGL（euler `yum install libGL libGLU libEGL libX11-devel`）。

## 相关页面

- 同族视频生成模型：[cosmos-predict2.5](cosmos_predict2_5.md)
- 机械臂世界模型：[agibot-arm-world-model](agibot_arm_world_model.md)
- DiT 模块：[dit](../../../inference/concepts/modules/dit.md)｜FA 融合：[fused-infer-attention-score](../../../inference/concepts/kernels/fused_infer_attention_score.md)
- 并行：[cfg-parallel](../../../inference/concepts/parallelism/cfg_parallel.md)｜[context-parallel](../../../inference/concepts/parallelism/context_parallel.md)
- 平台：[atlas-a3](../../../inference/concepts/platforms/atlas_a3.md)
- 源：[cann-recipes-embodied-ai](https://gitcode.com/cann/cann-recipes-embodied-ai/tree/aed7a4788dfe94f6b90084f16ce493f9969471b1)
