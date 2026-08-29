---
type: Concept
title: Alpamayo-R1（智驾 VLA 推理 · 昇腾 A2）
description: Alpamayo-R1（下文 AR-1）是 NVIDIA 提出的面向 L4/L5 级智能驾驶的视觉-语言-动作（VLA）大模型，cann-recipes-embodied-ai 在昇腾 Atlas A2 上完成其推理迁移与计算逻辑优化。AR-1 融合视觉感知与自然语言指令构建结构化场景理解，并引入显式的因果思维链（Chain-of-Causal-Thinking, CoC）机制，模拟人类驾驶员「观察—分析因果—预判后果—决策」的认知流程，生成稳健可验证的轨迹规划，同时输出自然语言决策解释。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.multimodal
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/navigation/alpamayo-r1/README.md
  role: supporting
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-06-27T00:00:00Z'
platforms:
- a2
---

# Alpamayo-R1（智驾 VLA 推理 · 昇腾 A2）

Alpamayo-R1（下文 **AR-1**）是 NVIDIA 提出的面向 L4/L5 级智能驾驶的视觉-语言-动作（VLA）大模型，`cann-recipes-embodied-ai` 在**昇腾 Atlas A2** 上完成其推理迁移与计算逻辑优化。AR-1 融合视觉感知与自然语言指令构建结构化场景理解，并引入显式的**因果思维链**（Chain-of-Causal-Thinking, CoC）机制，模拟人类驾驶员「观察—分析因果—预判后果—决策」的认知流程，生成稳健可验证的轨迹规划，同时输出自然语言决策解释。

> 论文：Alpamayo-R1: Bridging Reasoning and Action Prediction for Generalizable Autonomous Driving in the Long Tail（arXiv:2511.00088）。上游仓 https://github.com/NVlabs/alpamayo （pin `e0e2ac32`），仓内通过 `navigation/alpamayo-r1/patches/ar-1.patch` 适配昇腾 A2。权重 `nvidia/Alpamayo-R1-10B`（约 10B 参数）。

## 推理形态与产出

- 单次推理入口 `src/alpamayo_r1/test_inference.py`，输出 **10 组驾驶轨迹预测序列 + CoC 思维链文本**。
- 优化后单次推理时间下降至 **7.32 s**（达到该样例的推理时间优化目标）。
- 依赖链：CANN 8.5.0（toolkit + Atlas-A2 kernels）、Python 3.11、`uv` 虚拟环境；另需手动安装 `physical-ai-av 0.1.0`（需 patch 适配 python311）。

模型本体基于 Qwen3-VL 类多模态主干（VLM）+ 扩散式动作头（flow matching 积分），属 VLA 架构；动作生成方式与 [flow-matching-action-expert](../modules/flow_matching_action_expert.md)（Pi0 系流匹配动作专家）同源但模型不同（AR-1 为智驾轨迹预测、Pi0 为机械臂操作）。

## 精度验证（minADE）

在 Physical-AI-AV-Dataset 的 `chunk_0000` 共 100 个 clips 上，以 **minADE**（最小平均位移误差，越低越好）验证昇腾 A2 推理精度，按预测轨迹数对比：

| 预测轨迹数 | 平台 | minADE |
|:---:|:---:|:---:|
| 1 | 昇腾 A2 | 2.2026 |
| 3 | 昇腾 A2 | 0.9498 |
| 5 | 昇腾 A2 | 0.8514 |
| 10 | 昇腾 A2 | 0.5676 |

预测轨迹数越多，minADE 越低（多模态轨迹覆盖更全）；样例默认输出 10 组轨迹。

## 昇腾计算逻辑优化

来源 `docs/navigation/alpamayo-r1/README.md`。五项优化均属算子级改写，目标是减少 kernel launch、显存读写与冗余计算：

| 优化项 | 类型 | 主要技术 | 收益（文档定性） |
|---|---|---|---|
| **FA 替换** | 注意力融合 | `torch_npu.npu_fusion_attention`（设 `config.attn_implementation='flash_attention_2'`） | 降显存、提速、支持更长序列 |
| **布尔索引优化** | 算子优化 | `patched_get_placeholder_mask`：用 `special_image_mask.sum().item()` 比对替代低效布尔索引；`apply_qwen3vl_patches()` 应用 | 减少冗余计算、提升索引效率 |
| **RMSNorm 融合** | 算子融合 | `torch_npu.npu_rms_norm` 替换手写 `x*rsqrt(mean(x²)+eps)` | 减少 kernel launch、优化内存访问 |
| **ADD 融合** | 算子融合 | 扩散积分 `x = x + dt*v` 改 `torch.addcmul(x, dt, v)` | 减少内存读写与 kernel launch |
| **Slice+Concat 优化** | 内存优化 | `action_in_proj.py` 预分配 `batch_feats` + 索引赋值，替代多次 `torch.cat` | 减少内存分配/拷贝、提升缓存效率 |

布尔索引优化 before/after（`qwen3vl_optimization.py`，原文）——避免对 `inputs_embeds[special_image_mask]` 取 `.numel()` 的低效布尔索引：

```python
# 原始：布尔索引取 numel 比对
if image_features is not None and inputs_embeds[special_image_mask].numel() != image_features.numel():
# 优化：先 sum().item() 数掩码元素，仅在不匹配时报错
n_masked_elements = special_image_mask.sum().item()
if image_features is not None and n_masked_elements != image_features.numel():
    raise ValueError(...)
```

关键代码位置：
- FA 实现切换在 `src/alpamayo_r1/models/base_model.py` 模型初始化（`config.attn_implementation='flash_attention_2'`）。
- 布尔索引补丁在新增文件 `src/alpamayo_r1/qwen_patches/qwen3vl_optimization.py`。
- RMSNorm 在 `src/alpamayo_r1/models/action_in_proj.py` 的 `RmsNorm` 类（注意 `npu_rms_norm` 返回元组，取 `[0]`）。
- ADD 融合在 `src/alpamayo_r1/diffusion/flow_matching.py` 的 `flow_matching_euler` 积分步进。
- Slice+Concat 在 `action_in_proj.py` 的 `PerWaypointActionInProjV2.forward`。

> FA 与 RMSNorm 两项复用昇腾的注意力/归一化融合能力，对照 cann-infer 的注意力融合 [fused-infer-attention-score](../../../inference/concepts/kernels/fused_infer_attention_score.md)；在 AR-1 上的应用即「把 Qwen3-VL 主干的小算子 attention 替换为 `npu_fusion_attention` 融合调用、把手写 RMSNorm 替换为 `npu_rms_norm`」。AR-1 当前样例未使用 OM 离线或 torchair 整图编译（区别于 Pi0 系）。

## Links

- 同源动作生成结构：[flow-matching-action-expert](../modules/flow_matching_action_expert.md)
- 同域运动控制模型：[lqc](../locomotion/lqc.md)
- 跨域：[fused-infer-attention-score](../../../inference/concepts/kernels/fused_infer_attention_score.md)（FA/注意力融合）
- 源：[cann-recipes-embodied-ai](https://gitcode.com/cann/cann-recipes-embodied-ai/tree/aed7a4788dfe94f6b90084f16ce493f9969471b1)

<!-- cannbot:related:start -->
## 相关

- [Flow-Matching Action Expert（流匹配动作专家）](../modules/flow_matching_action_expert.md)（`related`）：模型本体基于 Qwen3-VL 类多模态主干（VLM）+ 扩散式动作头（flow matching 积分），属 VLA 架构；Pi0 把机器人策略表示为一个**条件去噪扩散 / 流匹配过程**，整体拆成「慢系统」VLM 主干 + 「快系统」动作专家两段；Alpamayo-R1 的智驾轨迹头与 Pi0 动作专家都由 VLM 条件驱动流匹配生成连续动作，后者给出理解前者慢系统与快系统边界的架构参照。
- [npu_fused_infer_attention_score (v1 / v2)](../../../inference/concepts/kernels/fused_infer_attention_score.md)（`related`）：FA 实现切换在 `src/alpamayo_r1/models/base_model.py` 模型初始化（`config.attn_implementation='flash_attention_2'`）。；昇腾推理侧的通用 FlashAttention 融合算子（简称 **FIA**），覆盖 Softmax-Attention 的主体计算；Alpamayo-R1 的注意力实现切换需要昇腾 FlashAttention 能力，FIA 卡解释融合注意力主体计算、布局与缓存入口，可辅助选择和验证该类替换。
<!-- cannbot:related:end -->
