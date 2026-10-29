---
type: Runbook
title: C8 KV-cache 量化前置：MLA 系模型必须 enable_mla_prolog=True，否则 bringup 抛 ValueError
description: C8 KV-cache 量化前置：MLA 系模型必须 enable_mla_prolog=True，否则 bringup 抛 ValueError。给 MLA 系模型（DeepSeekRunner 路径：DeepSeek-R1 / Kimi-K2-Thinking / DeepSeek-V3.2-Exp）开 C8（KV-cache int8）量化且 enable_mla_prolog=False 时，bring-up 阶段主动抛： ValueError("if kv_cache_quant_mode is C8, then enable_mla_prolog must be set to True.")
tags:
- task.debugging
- topic.attention
- topic.precision
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/82
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/90
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-22T10:43:19Z'
platforms:
- agnostic
---

# C8 KV-cache 量化前置：MLA 系模型必须 enable_mla_prolog=True，否则 bringup 抛 ValueError

## 信号（现象）

给 [MLA](../../concepts/modules/mla.md) 系模型（`DeepSeekRunner` 路径：DeepSeek-R1 / Kimi-K2-Thinking / DeepSeek-V3.2-Exp）开 C8（KV-cache int8）量化且 enable_mla_prolog=False 时，bring-up 阶段主动抛：

```
ValueError("if kv_cache_quant_mode is C8, then enable_mla_prolog must be set to True.")
```

## 触发条件

- 量化配置里 KV-cache scheme 非空（即启用 C8 / `kv_cache_quant_mode == "C8"`），而 YAML 的 `model_config.enable_mla_prolog` 为 False。

## 根因

C8 KV-cache 走 [mla-prolog](../../concepts/kernels/mla_prolog.md) 路径——这是仓内 `check_model_cfg` / runner 强制的硬约束：只要检测到 KV-cache scheme 非空而 `enable_mla_prolog` 为 False，bringup 会主动 `raise ValueError`（而非静默走错路径）。这不是 bug，是设计上的前置门禁。

## 修法

- YAML 里把 `model_config.enable_mla_prolog` 置 True 再开 C8。
- 若不想用 mla_prolog，则不要开 C8（改 bf16 / w8a8c16，无此依赖）。

## 风险 / 边界

- 这是 C8 与 mla_prolog 的**耦合前置**；此外 C8 还与 PyPTO Lightning Indexer 互斥（开 C8 则 LI 走不到 PyPTO 快路），是另一条独立约束——同时开 C8 + `enable_pypto` 时 LI 不走 PTO，别误以为 PyPTO 没生效是抢卡。
- 约束系于 `DeepSeekRunner` / `check_model_cfg` 的 MLA 系路径，不外推到非 MLA 模型。

## 相关经验

- C8 与 PyPTO Lightning Indexer 互斥见 [c8-kvcache-disables-pypto-lightning-indexer](../../optimizations/anti_patterns/c8_kvcache_disables_pypto_lightning_indexer.md)。
- C8 scale 的来源/复用/离线预取见 [c8-kv-scale-provenance-reuse-offline](../../optimizations/rules/c8_kv_scale_provenance_reuse_offline.md)。

## Evidence

- `diff 事实`（@b88d340）：DeepSeek-R1 runner 强制 C8 → `enable_mla_prolog=True`，否则 `ValueError`。
- `diff 事实`（@0002ff4）：`check_model_cfg` 检测 KV-cache scheme 非空且 `enable_mla_prolog=False` 时 raise 同一 ValueError。
- 溯源下探：[cann-recipes-infer-pr-82-feat-add-deepseek-r1-c8-quantization-support](https://gitcode.com/cann/cann-recipes-infer/merge_requests/82)、[cann-recipes-infer-pr-90-fix-fix-check-model-cfg-fix-build-dtatset-input](https://gitcode.com/cann/cann-recipes-infer/merge_requests/90)