---
type: Guide
title: C8 (KV-cache int8) 量化 scale 是预标定 per-model artifact：来源、离线预取、同构复用与重标定
description: C8 (KV-cache int8) 量化 scale 是预标定 per-model artifact：来源、离线预取、同构复用与重标定。给 MLA 系模型做 W8A8C8 / W4A8C8（含 C8 = KV-cache/MLA int8 量化）部署时，理解 C8 的 KV int8 scale 从哪来、能不能复用、离线怎么办。
tags:
- task.debugging
- topic.attention
- topic.precision
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/80
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/90
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/82
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/281
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/142
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# C8 (KV-cache int8) 量化 scale 是预标定 per-model artifact：来源、离线预取、同构复用与重标定

## 适用场景

给 [MLA](../../../concepts/modules/mla.md) 系模型做 [W8A8C8](../../../concepts/quantization/w8a8c8.md) / [W4A8C8](../../../concepts/quantization/w4a8c8.md)（含 C8 = KV-cache/MLA int8 量化）部署时，理解 C8 的 KV int8 scale 从哪来、能不能复用、离线怎么办。

## 核心事实：C8 scale 是预标定、非从权重现算

MLA 的 KV int8 scale 是一份**预先标定的 per-model 参数、不是从权重转换时现算**。因此：

- **只对已有标定 scale 的模型可用**（本仓最初仅 DeepSeek-R1，scale 从 OBS 下载）；bf16 / [w8a8c16](../../../concepts/quantization/w8a8c8.md) 无此依赖、R1 与 Kimi-K2 通用。
- DeepSeek W8A8 量化中 `kv_b_proj`、`i>=3` 的 `mlp.gate`、`lm_head` 保 bf16 不量化。

## 问题信号 + 处置

### A. 离线/受限网络下 scale 下载超时 → 脚本 exit 1

`weight_convert.sh` 在 `--quant_mode w8a8c8` 分支会从华为 OBS（`cann-ai.obs.cn-north-4.myhuaweicloud.com`）`wget` 下载 MLA C8 scale 包 `mla_c8_scale.tar.gz`；离线/受限网络下下载超时让脚本直接 `exit 1`。

- 修法：**手动预取该包放入运行目录 `./quantization/` 并改脚本跳过 wget**，再离线完成 W8A8C8 转换（维护者确认离线修法）。

### B. 权重快照变了 → 预置 scale 失效，须 amct 重标定

仓为部署提供的预置 W8A8C8/W4A8C8 量化参数（convert 流程下载的 `w4a8c8.zip`）与**特定权重快照绑定**；权重变化后必须用 amct 仓的逐 block PTQ 工具链**重新生成量化参数**，不能直接复用预置包。

### C. 结构同构模型可复用兄弟模型的 scale（但注意未标定的稀疏路径）

- 当新模型与已发布量化系数的模型（DeepSeek-V3.2-Exp）**结构同构**时，其 W8A8C8/W4A8C8 可直接复用后者已发布的系数 zip（配 `--clip`），无需单独标定；GLM-5 即复用 DeepSeek-V3.2-Exp 系数。
- **⚠️ 边界**：GLM-5 的 C8 转换脚本下载并复用的是 DeepSeek-V3.2-Exp 的预置量化参数包（非 GLM-5 自有），且维护者确认 GLM-5 的 SFA（[稀疏注意力](../../../concepts/modules/sparse_flash_attention.md)）部分 C8 当前**未支持**——GLM-5 的现成 C8 转换**不是一条已针对 GLM-5 标定/验证的原生路径**，用它要接受这一未验证面。

## correctness 验证

- 复用/重标定后须跑评测对齐（MMLU/GPQA 等）确认无精度回退，尤其复用兄弟模型 scale 时要覆盖稀疏注意力路径。

## 风险 / rollback

- 复用兄弟模型 scale 属未针对本模型标定的路径，出现掉分回退到 bf16 / w8a8c16（无 scale 依赖）。
- 离线预取要核对 scale 包与权重快照对应，错配比不用更隐蔽。

## 相关经验

- C8 的 mla_prolog 前置约束见 [c8-kvcache-requires-mla-prolog](../../../runbooks/runtime/c8_kvcache_requires_mla_prolog.md)；C8 与 PyPTO Lightning Indexer 互斥见 [c8-kvcache-disables-pypto-lightning-indexer](../../../optimizations/experience/anti_patterns/c8_kvcache_disables_pypto_lightning_indexer.md)。
- 量化制备路径选择见 [quant-weight-conversion-path-selection](quant_weight_conversion_path_selection.md)；结构同构复用见 [structural-isomorphic-model-reuse-stack](../../../optimizations/experience/rules/structural_isomorphic_model_reuse_stack.md)。

## Evidence

- `diff 事实 / 维护者确认`（@2c45117）：`weight_convert.sh` w8a8c8 分支 wget OBS scale 包、离线 exit 1、维护者给离线预取修法。
- `维护者确认`（@2c45117）：预置系数与权重快照绑定、权重变了须 amct 逐 block PTQ 重生成。
- `diff 事实`（@b88d340）：C8 scale 预标定、从 OBS 下载；`kv_b_proj`/`mlp.gate(i>=3)`/`lm_head` 保 bf16。
- `diff 事实 / 维护者确认`（@1ce713f / @2c45117）：GLM-5 复用 DeepSeek-V3.2-Exp 系数、SFA C8 未支持。
- 溯源下探：[cann-recipes-infer-issue-80-bug-report-cann-ai-obs-cn-north-4-myhuaweicloud-com](https://gitcode.com/cann/cann-recipes-infer/issues/80)、[cann-recipes-infer-issue-90-question-deepseek-3-2-w4a8c8](https://gitcode.com/cann/cann-recipes-infer/issues/90)、[cann-recipes-infer-pr-82-feat-add-deepseek-r1-c8-quantization-support](https://gitcode.com/cann/cann-recipes-infer/merge_requests/82)、[cann-recipes-infer-pr-281-glm-5-w8a8-support](https://gitcode.com/cann/cann-recipes-infer/merge_requests/281)、[cann-recipes-infer-issue-142-requirement-glm5-ds32](https://gitcode.com/cann/cann-recipes-infer/issues/142)