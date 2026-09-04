---
type: Concept
title: Cosmos-Predict2.5-2B 视频生成世界基础模型（昇腾 A3）
description: Cosmos-Predict2.5-2B 是 NVIDIA 推出的世界基础模型（World Foundation Model），面向物理 AI（Physical AI）场景的世界模拟，cann-recipes-embodied-ai 提供昇腾 Atlas A3 上的 NPU 适配优化与多卡并行实现。模型基于流匹配（Flow Matching）架构，结合 Cosmos-Reason1 物理 AI 视觉语言模型作为文本编码器，生成高质量、物理一致的视频世界，用于机器人操作、自动驾驶等动态场景的模拟与预测。支持文本 / 图像 / 视频三种条件输入模式（Text2World / Image2World / Video2World）；单段生成视频长约 5.8 秒，逐段生成拼接可实现 30-120 秒长时序一致视频。整体评分据适配 README 与参数量大 7 倍的 Wan2.2-27B-A14B 相当（PAI-Bench 外部基准，无独立复测结果）。昇腾优化重点是多卡并行推理 + NPU 融合算子适配。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.multimodal
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/world_model/cosmos-predict2.5/README.md
  role: supporting
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-09-03T13:55:44Z'
platforms:
- a3
---

# Cosmos-Predict2.5-2B 视频生成世界基础模型（昇腾 A3）

## Summary

Cosmos-Predict2.5-2B 是 NVIDIA 推出的世界基础模型（World Foundation Model），面向物理 AI（Physical AI）场景的世界模拟，`cann-recipes-embodied-ai` 提供昇腾 Atlas A3 上的 NPU 适配优化与多卡并行实现。模型基于**流匹配（Flow Matching）**架构，结合 **Cosmos-Reason1 物理 AI 视觉语言模型作为文本编码器**，生成高质量、物理一致的视频世界，用于机器人操作、自动驾驶等动态场景的模拟与预测。支持文本 / 图像 / 视频三种条件输入模式（Text2World / Image2World / Video2World）；单段生成视频长约 5.8 秒，逐段生成拼接可实现 30-120 秒长时序一致视频。整体评分据适配 README 与参数量大 7 倍的 Wan2.2-27B-A14B 相当（PAI-Bench 外部基准，无独立复测结果）。昇腾优化重点是**多卡并行推理 + NPU 融合算子适配**。

> 模型本体来自 NVIDIA 官方仓 `nvidia-cosmos/cosmos-predict2.5`（checkout `173b0fe9...`）；昇腾适配来自 `cann-recipes-embodied-ai/world_model/cosmos-predict2.5/`。

## 架构定位

- **DiT 扩散主干**：Cosmos-Predict2.5 的去噪网络为 DiT 结构（实现见 `cosmos_predict2/_src/predict2/networks/minimal_v4_dit.py`），是昇腾适配的核心算子热点。
- **流匹配生成**：以 Flow Matching 作为视频生成范式（区别于操作类 VLA 的 flow-matching 动作专家——同名范式、不同生成对象，见本域 [flow-matching-action-expert](../modules/flow_matching_action_expert.md)）。
- **VLM 文本编码器**：用 Cosmos-Reason1（基于 Qwen2.5-VL，实现见 `cosmos_predict2/_src/reason1/networks/qwen2_5_vl.py`）做条件编码。

## 昇腾 NPU 适配（一手）

适配通过 **Monkey Patch** 机制动态生效：执行 `npu_adapt.sh` 后由 `adaptor_patches/monkey_patch.py` 在运行期替换关键实现，无需侵入式改官方源码。`monkey_patch.py` 顶部 `from torch_npu.contrib import transfer_to_npu` + `setup_npu_device()` 按 `LOCAL_RANK` 绑定 `npu:{rank}`。

### 融合算子替换（Predict 侧）

| 原实现 | 昇腾替换 | 位置 |
|--------|---------|------|
| FlashAttention | `torch_npu.npu_fusion_attention`（`input_layout="BNSD"`, `sparse_mode=2`, `pre/next_tockens=2147483647`, `keep_prob=1`） | `_src/reason1/networks/qwen2_5_vl.py` |
| 自定义 RMSNorm | `torch_npu.npu_rms_norm(x, weight.float(), epsilon=eps)[0]` | `_src/predict2/networks/minimal_v4_dit.py` |
| TransformerEngine `apply_rotary_pos_emb` | `torch_npu.npu_rotary_mul(x, cos, sin)`（freqs→cos/sin 后旋转） | `_src/predict2/networks/minimal_v4_dit.py` |

> 注意 Predict 与 [cosmos-transfer2.5](cosmos_transfer2_5.md) 的注意力路径不同：**Predict 用 `npu_fusion_attention` 融合算子**，Transfer 走原生 `F.scaled_dot_product_attention`。RMSNorm / Rotary 融合两模型一致。FA 融合详见 cann-infer 的 [fused-infer-attention-score](../../../inference/concepts/kernels/fused_infer_attention_score.md)。Qwen-VL FA 替换还在 `Qwen2_5_VLFlashAttention2.__init__` 预建 `2048×2048` 上三角因果掩码（`torch.triu(ones, diagonal=1).bool()`，配合 `sparse_mode=2` 作 `atten_mask` 喂入），并把 `qwen2_5_vl.is_flash_attn_2_available` 强制置 `return False` 以禁用原生 flash 路径，确保 `npu_fusion_attention` 生效——下游做 FA 精度/形状回归会关心这两点。
>
> 此外 `monkey_patch.py` 还**重载了 DiT `Attention.compute_qkv`**（`patched_compute_qkv`，去掉 `tensor_format`/`fused` 多余参数）：self-attn 且 `use_wan_fp32_strategy` 时，先把 q/k 升 `fp32` 再做 `apply_rotary_pos_emb`（只传 q/k 与 `rope_emb`）后降回——该适配改变了 DiT NPU 上 RoPE 的计算精度，非单纯算子替换。

## 多卡并行推理（一手）

运行 `npu_adapt.sh` 后即可在 NPU 多卡并行推理。单卡：
```bash
python examples/inference.py -i assets/base/robot_pouring.json -o outputs/base_video2world \
  --inference-type=video2world --model="2B/post-trained" --disable_guardrails
```
多卡（`torchrun` 8 卡）：
```bash
ASCEND_RT_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 torchrun --nproc_per_node=8 --master_port=12341 \
  examples/inference.py -i assets/base/robot_pouring.json -o outputs/base_video2world \
  --inference-type=video2world --model="2B/post-trained" --disable_guardrails
```
- **上下文并行（Context Parallelism）**：跨设备切分长序列视频帧以支持超长视频生成；`cann-recipes-embodied-ai/docs/world_model/Cosmos/README.md` 明确 Cosmos 系列使能 CP，参见 cann-infer [context-parallel](../../../inference/concepts/parallelism/context_parallel.md)（及其序列并行变体 [ulysses](../../../inference/concepts/parallelism/ulysses.md) / [ring-attention](../../../inference/concepts/parallelism/ring_attention.md)）。
- **CFG 并行**：将 NPU 分两组分别跑 conditional / unconditional 去噪分支。上述优化文档中 `enable_cfg_parallel` 的代码改造落在 [cosmos-transfer2.5](cosmos_transfer2_5.md)（Transfer 的 `inference_patch.py`）；Predict 侧 README 未单列 CFG 并行开关。CFG 并行原理见 cann-infer [cfg-parallel](../../../inference/concepts/parallelism/cfg_parallel.md)。

8 卡 `torchrun` 上一次机器人倒水视频（`robot_pouring`）生成端到端耗时约 **920 秒**（`cann-recipes-embodied-ai` 的 Predict README 实测值）。

## 精度验证（一手）

- 与 NVIDIA 平台生成视频逐帧对比观察一致性。
- **PAI-Bench-G（Video Generation）** 评估 `robot_pouring` 输出，README 给出参考分数区间：aesthetic_quality [0.63,0.66]、background_consistency [0.97,1.00]、imaging_quality [0.70,0.73]、motion_smoothness [0.98,1.00]、subject_consistency [0.98,1.00]。PAI-Bench 为外部基准框架，`cann-recipes-embodied-ai` 未附实测结果文件。

## 环境要点

- 环境：CANN `8.3.RC1` + `uv`，详见 `cann-recipes-embodied-ai/world_model/cosmos-predict2.5/README.md`。

## 相关页面

- 同族风格转换模型：[cosmos-transfer2.5](cosmos_transfer2_5.md)（共用 `cann-recipes-embodied-ai/docs/world_model/Cosmos` 优化文档）
- 机械臂世界模型（A2 训练）：[agibot-arm-world-model](agibot_arm_world_model.md)
- DiT 模块：[dit](../../../inference/concepts/modules/dit.md)｜FA 融合：[fused-infer-attention-score](../../../inference/concepts/kernels/fused_infer_attention_score.md)
- 并行：[context-parallel](../../../inference/concepts/parallelism/context_parallel.md)｜[cfg-parallel](../../../inference/concepts/parallelism/cfg_parallel.md)
- 平台：[atlas-a3](../../../inference/concepts/platforms/atlas_a3.md)
- 源：[cann-recipes-embodied-ai](https://gitcode.com/cann/cann-recipes-embodied-ai/tree/aed7a4788dfe94f6b90084f16ce493f9969471b1)
