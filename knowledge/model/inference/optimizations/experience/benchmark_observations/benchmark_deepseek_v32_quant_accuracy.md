---
type: Optimization
title: DeepSeek-V3.2-Exp 各量化档 (W8A8C16 / W8A8C8 / W4A8C8) 精度近 BF16 基准
description: DeepSeek-V3.2-Exp 各量化档 (W8A8C16 / W8A8C8 / W4A8C8) 精度近 BF16 基准。在 DSA 稀疏注意力 MoE 模型（DeepSeek-V3.2-Exp 及同结构）上评估「量化会不会掉精度、该选哪个档」时，用这组仓自报精度作验收目标 / 搜索先验：W8A8C16、W8A8C8、W4A8C8 三档在 MMLU/GPQA/DROP/MGSM 上均近 BF16、无明显回退。即「昇腾侧对该模型做低比特量化，近无损是可达标的预期」；据此可优先选更省显存的档、把评测精度阈值定在 baseline ±0.5 点内，而非一见量化就担心大幅掉分。
tags:
- task.testing
- topic.performance.analysis
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/1
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/8
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/105
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# DeepSeek-V3.2-Exp 各量化档 (W8A8C16 / W8A8C8 / W4A8C8) 精度近 BF16 基准

## 适用场景

在 [DSA](../../../concepts/modules/dsa.md) 稀疏注意力 MoE 模型（[DeepSeek-V3.2-Exp](../../../concepts/models/deepseek_v3_2_exp.md) 及同结构）上评估「量化会不会掉精度、该选哪个档」时，用这组仓自报精度作**验收目标 / 搜索先验**：W8A8C16、[W8A8C8](../../../concepts/quantization/w8a8c8.md)、[W4A8C8](../../../concepts/quantization/w4a8c8.md) 三档在 MMLU/GPQA/DROP/MGSM 上均近 BF16、无明显回退。即「昇腾侧对该模型做低比特量化，近无损是可达标的预期」；据此可优先选更省显存的档、把评测精度阈值定在 baseline ±0.5 点内，而非一见量化就担心大幅掉分。

## 精度基准（baseline = BF16，doc 披露、仓自报、无独立复测）

不同文档版本 / 评测口径下 BF16 baseline 绝对值有两套（见下），量化-BF16 的**差值**结论一致（近无损）。

W8A8C16 档（较早文档版本，KVCache 保持 16-bit）：

| 模型 | MMLU | GPQA | DROP | MGSM |
| ---- | ---- | ---- | ---- | ---- |
| BF16 | 89.9 | 73.6 | 88.9 | 92.4 |
| Int8 (W8A8C16) | 89.8 | 73.5 | 88.7 | 92.3 |

各项 -0.1 / -0.1 / -0.2 / -0.1，四项均在 0.2 点内。指南结论：「精度接近无损的情况下，权重内存占用优化 2 倍，TTFT 和 TPOT 也同步优化」。

W8A8C8 / W4A8C8 档（较晚文档版本，KVCache 也量化到 int8）：

| 模型 | MMLU | GPQA | DROP | MGSM |
| ---- | ---- | ---- | ---- | ---- |
| BF16 | 90.8 | 75.85 | 87.57 | 90.9 |
| W8A8C8 | 90.62 | 75.90 | 87.41 | 90.87 |
| W4A8C8 | 90.66 | 76.5 | 87.68 | 91.3 |

W8A8C8 相对 BF16 各项 -0.18 / +0.05 / -0.16 / -0.03；W4A8C8 各项 -0.14 / +0.65 / +0.11 / +0.4（部分项略高，在评测噪声量级内）。W4A8C8 在 GPQA/DROP/MGSM 上不低于 W8A8C8。

## 口径说明（非矛盾）

两版 BF16 baseline 绝对值不同（89.9… vs 90.8…）系**不同量化档 + 不同文档版本**的独立评测，非同一断言冲突：早版报 W8A8C16、晚版重测报 W8A8C8/W4A8C8，各自与自己的 BF16 baseline 对齐。跨版本比绝对值无意义，只看「量化-BF16 差值近 0」这一结论。

## 边界 / 风险

- 数字均为仓库量化策略文档披露值，**无独立第三方复测**；评测运行命令 / 环境 / 评测脚本源未给（gap），故只作「模型质量结论」，不当可复现 benchmark 命令。
- 能力归因是 cann-recipes-infer / CANN·amct 在昇腾上为该模型提供量化（amct / 仓内量化系数 + convert_model.py），非 DeepSeek 官方「已支持」。
- 性能 benchmark（吞吐 / TTFT / TPOT）不在本精度基准范围内。
- 达到近无损依赖正确的量化布局与离群值抑制手段（选择性层量化、clip/clamp、Hadamard 旋转），见 [precision-quant-convert-model-config-pitfalls](../rules/precision_quant_convert_model_config_pitfalls.md) / [precision-low-bit-quant-clip-clamp-outlier](../rules/precision_low_bit_quant_clip_clamp_outlier.md) / [precision-lightning-indexer-low-bit-quant](../rules/precision_lightning_indexer_low_bit_quant.md)。

## Evidence

- doc 披露 / 仓自报（@cc9e59db7a11）：W8A8C16 精度表出自 `deepseek_v3.2_exp_inference_guide.md` 量化策略段。溯源下探 [cann-recipes-infer-issue-1-rfc-deepseek-v3-2-exp-w8a8c16](https://gitcode.com/cann/cann-recipes-infer/issues/1)
- doc 披露 / 仓自报（@2c45117）：W8A8C8 精度表；早版口径（PR 期 doc）BF16=89.9/73.6/88.9/92.4 并存注记。溯源下探 [cann-recipes-infer-issue-8-rfc-deepseek-v3-2-exp-w8a8c8](https://gitcode.com/cann/cann-recipes-infer/issues/8)
- doc 披露 / 仓自报（@d3c31919e4ac）：W8A8C8/W4A8C8 精度表与 issue 引用逐格一致（引用官方指南、非提问者自测）。溯源下探 [cann-recipes-infer-issue-105-question-dsv3-2-w8a8c8-w4a8c8](https://gitcode.com/cann/cann-recipes-infer/issues/105)