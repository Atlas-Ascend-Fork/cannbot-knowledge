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
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/models/indexer.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_5/models/modeling_qwen3_5_moe.py
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:29:36Z'
platforms:
- agnostic
---

# 结构同构模型直接复用已支持模型的建模栈与优化路径，无需从零建模

## 条件 → 优先尝试什么

给一个新模型做昇腾 bringup / 推理优化时，**先比对它的结构签名和已支持模型是否同构**；若关键子结构（注意力形态 + 归一化 + MoE 形态 + 投机头）一致，则**直接复用已支持模型的建模栈、kernel 与 technique 经验，不从零建模、不另起算子路径**。这是把 bringup 成本从「重写」降到「适配类名/config/权重命名」的最有效先验。

## 判「同构」看什么（结构签名）

对齐这几个维度即视为可复用：

- **注意力**：是否同为 [MLA](../../concepts/modules/mla.md)（q/kv LoRA + rope/nope 拆头）+ [DSA](../../concepts/modules/dsa.md) 稀疏注意力（[lightning-indexer](../../concepts/kernels/lightning_indexer.md)）；或同为 GatedDeltaNet 线性注意力 + 交错 full-attention。
- **MoE**：前若干层 dense、其余细粒度 MoE、是否含 shared expert。
- **投机解码**：是否带 1 层 MTP。

## 参考实现（两组同构族）

- **`glm_moe_dsa` 族 ≈ DeepSeek-V3.2-Exp**：GLM-5（`model_type="glm_moe_dsa"`）与 DeepSeek-V3.2-Exp 同构——同一套 MLA + DSA lightning-indexer + MoE(含 shared expert) + MTP。GLM-5 即以复用 DeepSeek-V3.2-Exp 建模栈与优化路径落地，无需另写算子。
- **Qwen3.5-MoE ≈ Qwen3-Next**：两者共用「GatedDeltaNet 线性注意力 + 交错 full-attention + sparse-MoE」混合架构；decode实现仍需逐模块适配，当前Qwen3.5已是独立建模副本；可参考的关键原语（[recurrent-gated-delta-rule](../../concepts/kernels/recurrent_gated_delta_rule.md) 递推核、RMSNormGated 融合、GDN-CP、MoE 多流）在两族间可迁移。做 Qwen3.5-MoE decode 适配应从 Qwen3-Next 的 GDN 工具链起步。

## 复用的粒度与仍需改的点

复用到「建模栈 + kernel/technique 经验」层，但仍需逐点适配（**这些是复用时最容易踩的坑**）：

- **类名 / 函数名 / config 字段名**：新模型的类名与 config 键常不同，须映射。
- **config 默认值陷阱**：沿用源模型的 Config 类会带来源模型的默认值（如 RoPE base），迁移期可能静默取错——见 [transformers-5-breaking-changes-vendored-hf-modeling](../../runbooks/compilation/transformers_5_breaking_changes_vendored_hf_modeling.md)。
- **停止符 / eos**：不同模型 eos token 集不同，见 [decode-eos-termination-registration](../../runbooks/runtime/decode_eos_termination_registration.md)。
- **量化系数**：结构同构仅提供建模适配线索，量化系数必须绑定目标权重快照、量化路径和校准依据（见下）。

## 量化系数须独立核对来源与校准

结构同构不能证明目标模型可直接复用 W8A8C8/W4A8C8 系数或免标定。先确认目标权重快照、具体量化路径支持、系数生成依据与精度验收；来源要求重新生成时应重新校准。历史工作项中GLM-5的C8状态不能替代当前代码核对；当前GLM5已有FP8 LI与KV分支，但脚本中的DS3.2系数URL仍不证明适用于GLM5权重，DS3.2权重变化也需重新生成参数；细节与证据由 [C8 scale 来源规则](c8_kv_scale_provenance_reuse_offline.md)统一维护。

## 风险 / 边界

- 「同构 → 可复用」的适用面按证据限定到上面两组模型族，不外推为「任意 MoE/MLA 模型都能互换栈」。
- 复用不等于零改动：类名/config/权重命名/停止符/量化标定各点须逐一核对，漏一处即在加载期或解码期出错。

## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/issues/148)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/281)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/288)（evidence）
- [indexer.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/models/indexer.py)（implementation）
- [modeling_qwen3_5_moe.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_5/models/modeling_qwen3_5_moe.py)（implementation）
