---
type: Optimization
title: 结构同构模型直接复用已支持模型的建模栈与优化路径，无需从零建模
description: 结构同构模型直接复用已支持模型的建模栈与优化路径，无需从零建模。给一个新模型做昇腾 bringup / 推理优化时，先比对它的结构签名和已支持模型是否同构；若关键子结构（注意力形态 + 归一化 + MoE 形态 + 投机头）一致，则直接复用已支持模型的建模栈、kernel 与 technique 经验，不从零建模、不另起算子路径。这是把 bringup 成本从「重写」降到「适配类名/config/权重命名」的最有效先验。
tags:
- task.optimization
- topic.attention
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/148
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/281
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/288
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 结构同构模型直接复用已支持模型的建模栈与优化路径，无需从零建模

## 条件 → 优先尝试什么

给一个新模型做昇腾 bringup / 推理优化时，**先比对它的结构签名和已支持模型是否同构**；若关键子结构（注意力形态 + 归一化 + MoE 形态 + 投机头）一致，则**直接复用已支持模型的建模栈、kernel 与 technique 经验，不从零建模、不另起算子路径**。这是把 bringup 成本从「重写」降到「适配类名/config/权重命名」的最有效先验。

## 判「同构」看什么（结构签名）

对齐这几个维度即视为可复用：

- **注意力**：是否同为 [MLA](../../../concepts/modules/mla.md)（q/kv LoRA + rope/nope 拆头）+ [DSA](../../../concepts/modules/dsa.md) 稀疏注意力（[lightning-indexer](../../../concepts/kernels/lightning_indexer.md)）；或同为 GatedDeltaNet 线性注意力 + 交错 full-attention。
- **MoE**：前若干层 dense、其余细粒度 MoE、是否含 shared expert。
- **投机解码**：是否带 1 层 MTP。

## 参考实现（两组同构族）

- **`glm_moe_dsa` 族 ≈ DeepSeek-V3.2-Exp**：GLM-5（`model_type="glm_moe_dsa"`）与 DeepSeek-V3.2-Exp 同构——同一套 MLA + DSA lightning-indexer + MoE(含 shared expert) + MTP。GLM-5 即以复用 DeepSeek-V3.2-Exp 建模栈与优化路径落地，无需另写算子。
- **Qwen3.5-MoE ≈ Qwen3-Next**：两者共用「GatedDeltaNet 线性注意力 + 交错 full-attention + sparse-MoE」混合架构；decode 关键原语（[recurrent-gated-delta-rule](../../../concepts/kernels/recurrent_gated_delta_rule.md) 递推核、RMSNormGated 融合、GDN-CP、MoE 多流）在两族间可迁移。做 Qwen3.5-MoE decode 适配应从 Qwen3-Next 的 GDN 工具链起步。

## 复用的粒度与仍需改的点

复用到「建模栈 + kernel/technique 经验」层，但仍需逐点适配（**这些是复用时最容易踩的坑**）：

- **类名 / 函数名 / config 字段名**：新模型的类名与 config 键常不同，须映射。
- **config 默认值陷阱**：沿用源模型的 Config 类会带来源模型的默认值（如 RoPE base），迁移期可能静默取错——见 [transformers-5-breaking-changes-vendored-hf-modeling](../../../runbooks/compilation/transformers_5_breaking_changes_vendored_hf_modeling.md)。
- **停止符 / eos**：不同模型 eos token 集不同，见 [decode-eos-termination-registration](../../../runbooks/runtime/decode_eos_termination_registration.md)。
- **量化系数**：结构同构时量化系数也可复用（见下），但要注意某些稀疏路径的量化未必已标定。

## 顺带：量化系数也可随同构复用

当新模型与已发布量化系数的模型结构同构时，其 W8A8C8/W4A8C8 量化可直接复用后者已发布的系数 zip（配 `--clip`），无需为新模型单独标定——细节与「未针对新模型标定/验证」的告警见 [c8-kv-scale-provenance-reuse-offline](../../../guides/experience/interventions/c8_kv_scale_provenance_reuse_offline.md)。

## 风险 / 边界

- 「同构 → 可复用」的适用面按证据限定到上面两组模型族，不外推为「任意 MoE/MLA 模型都能互换栈」。
- 复用不等于零改动：类名/config/权重命名/停止符/量化标定各点须逐一核对，漏一处即在加载期或解码期出错。

## Evidence

- `diff 事实`（@1ce713f / @b451d3e）：GLM-5（`glm_moe_dsa`）复用 DeepSeek-V3.2-Exp 的 MLA+DSA+MoE(shared)+MTP 建模栈落地。
- `维护者确认`（@2c45117）：Qwen3.5-MoE 与 Qwen3-Next 共用 GDN + 交错 full-attention + sparse-MoE，decode 原语可迁移。
- 溯源下探：[cann-recipes-infer-issue-148-requirement-qwen3-5-27b-v10-910b-fp32](https://gitcode.com/cann/cann-recipes-infer/issues/148)、[cann-recipes-infer-pr-281-glm-5-w8a8-support](https://gitcode.com/cann/cann-recipes-infer/merge_requests/281)、[cann-recipes-infer-pr-288-glm-5-adapt-class-name-and-function-name-support-bf16-fix-bug-caused-by](https://gitcode.com/cann/cann-recipes-infer/merge_requests/288)
