---
type: Optimization
title: C8 量化参数规则：绑定权重快照，离线预取与重新标定
description: 说明 C8 参数包与模型权重的绑定关系、受限网络下的预取方法，以及结构相似仍不能确认适用的边界。
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
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/utils/weight_convert.sh
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:29:36Z'
platforms:
- agnostic
---

# C8 量化参数规则：绑定权重快照，离线预取与重新标定

## 适用场景

给 [MLA](../../concepts/modules/mla.md) 系模型做 [W8A8C8](../../concepts/quantization/w8a8c8.md) / [W4A8C8](../../concepts/quantization/w4a8c8.md)（含 C8 = KV-cache/MLA int8 量化）部署时，理解 C8 的 KV int8 scale 从哪来、能不能复用、离线怎么办。

## 核心事实：C8 scale 是预标定、非从权重现算

MLA 的 KV int8 scale 是一份**预先标定的 per-model 参数、不是从权重转换时现算**。因此：

- **只对已有标定 scale 的模型可用**（本仓最初仅 DeepSeek-R1，scale 从 OBS 下载）；bf16 / [w8a8c16](../../concepts/quantization/w8a8c8.md) 无此依赖、R1 与 Kimi-K2 通用。
- DeepSeek W8A8 量化中 `kv_b_proj`、`i>=3` 的 `mlp.gate`、`lm_head` 保 bf16 不量化。

## 问题信号 + 处置

### A. 离线/受限网络下 scale 下载超时 → 脚本 exit 1

`weight_convert.sh` 在 `--quant_mode w8a8c8` 分支会从华为 OBS（`cann-ai.obs.cn-north-4.myhuaweicloud.com`）`wget` 下载 MLA C8 scale 包 `mla_c8_scale.tar.gz`；离线/受限网络下下载超时让脚本直接 `exit 1`。

- 修法：**手动预取该包放入运行目录 `./quantization/` 并改脚本跳过 wget**，再离线完成 W8A8C8 转换（维护者确认离线修法）。

### B. 权重快照变了 → 预置 scale 失效，须 amct 重标定

仓为部署提供的预置 W8A8C8/W4A8C8 量化参数（convert 流程下载的 `w4a8c8.zip`）与**特定权重快照绑定**；权重变化后必须用 amct 仓的逐 block PTQ 工具链**重新生成量化参数**，不能直接复用预置包。

### C. 兄弟模型脚本中的系数 URL 不构成适用性证据

当前GLM-5转换脚本仍引用DeepSeek-V3.2-Exp的系数包。Issue142的支持状态属于历史事件；最新代码已有浮点KV/LI分支，仍须逐条验证指定量化路径与系数。不能由结构同构或脚本可执行推导“无需标定即可复用”；应确认目标权重、量化路径和精度验收。未知时保留未验证状态，不将该包作为 GLM-5 的部署建议。

## correctness 验证

- 复用/重标定后须跑评测对齐（MMLU/GPQA 等）确认无精度回退，尤其复用兄弟模型 scale 时要覆盖稀疏注意力路径。

## 风险 / rollback

- 复用兄弟模型 scale 属未针对本模型标定的路径，出现掉分回退到 bf16 / w8a8c16（无 scale 依赖）。
- 离线预取要核对 scale 包与权重快照对应，错配比不用更隐蔽。

## 相关经验

- C8 的 mla_prolog 前置约束见 [c8-kvcache-requires-mla-prolog](../../runbooks/runtime/c8_kvcache_requires_mla_prolog.md)；C8 与 PyPTO Lightning Indexer 互斥见 [c8-kvcache-disables-pypto-lightning-indexer](../anti_patterns/c8_kvcache_disables_pypto_lightning_indexer.md)。
- 量化制备路径选择见 [quant-weight-conversion-path-selection](../../guides/deployment/quant_weight_conversion_path_selection.md)；结构同构复用见 [structural-isomorphic-model-reuse-stack](structural_isomorphic_model_reuse_stack.md)。

## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/issues/80)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/issues/90)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/82)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/281)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/issues/142)（evidence）
- [weight_convert.sh](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/utils/weight_convert.sh)（implementation）
