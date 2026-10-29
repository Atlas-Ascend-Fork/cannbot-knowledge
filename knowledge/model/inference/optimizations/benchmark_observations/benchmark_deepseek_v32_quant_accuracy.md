---
type: Optimization
title: DeepSeek-V3.2-Exp 三档量化精度的来源观测与评测缺口
description: 记录 W8A8C16、W8A8C8、W4A8C8 的两版来源自报精度表；各自对照对应 BF16 基线，保留平台、评测命令与重复测量缺口，不据此制定跨模型验收阈值。
tags:
- task.testing
- topic.performance.analysis
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/1
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/8
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/105
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_inference_guide.md
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/cc9e59db7a11b5bc897bef8f452e6baaa9aef7c7/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_inference_guide.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/d3c31919e4ac5dba45e38b7b16b80fcce1841974/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_inference_guide.md
  role: supporting
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-22T03:20:00Z'
platforms: []
---

# DeepSeek-V3.2-Exp 三档量化精度的来源观测与评测缺口

## 适用场景

评估 [DeepSeek-V3.2-Exp](../../concepts/models/deepseek_v3_2_exp.md) 的量化方案时，可参考下面两版来源自报精度表。它们提供该模型的历史观测，不证明其他同结构模型的精度，也不规定 baseline ±0.5 点等验收阈值。验收应在目标平台、权重和评测配置下另行确定。

具体评测平台、运行命令和重复测量资料尚未核验，因此本卡保持 draft、`platforms: []`，不把缺失平台写成硬件无关。

## 精度基准（baseline = BF16，doc 披露、仓自报、无独立复测）

不同文档版本 / 评测口径下 BF16 baseline 绝对值有两套（见下），量化-BF16 的差值分别列出；“近无损”为来源判断，不能由几行数字替代目标任务精度验收。

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

W8A8C8 相对 BF16 各项 -0.18 / +0.05 / -0.16 / -0.03；W4A8C8 各项 -0.14 / +0.65 / +0.11 / +0.4（部分项略高；没有重复测量资料，不能判断统计显著性）。W4A8C8 在 GPQA/DROP/MGSM 上不低于 W8A8C8。

## 口径说明

两版 BF16 基线绝对值不同，来源对应的文档版本和量化档也不同；评测配置不足以证明差异原因。分别保留每张表及其对应 BF16，不把两版拼成同一次受控实验，也不跨表比较绝对分数。

## 边界 / 风险

- 数字均为仓库量化策略文档披露值，**无独立第三方复测**；评测运行命令 / 环境 / 评测脚本源未给（gap），只保留来源观测，不称为已复现的模型质量结论。
- 能力归因是 cann-recipes-infer / CANN·amct 在昇腾上为该模型提供量化（amct / 仓内量化系数 + convert_model.py），非 DeepSeek 官方「已支持」。
- 性能 benchmark（吞吐 / TTFT / TPOT）不在本精度基准范围内。
- 达到近无损依赖正确的量化布局与离群值抑制手段（选择性层量化、clip/clamp、Hadamard 旋转），见 [precision-quant-convert-model-config-pitfalls](../rules/precision_quant_convert_model_config_pitfalls.md) / [precision-low-bit-quant-clip-clamp-outlier](../rules/precision_low_bit_quant_clip_clamp_outlier.md) / [precision-lightning-indexer-low-bit-quant](../rules/precision_lightning_indexer_low_bit_quant.md)。

## Evidence

- doc 披露 / 仓自报（@cc9e59db7a11）：W8A8C16 精度表出自 `deepseek_v3.2_exp_inference_guide.md` 量化策略段。溯源下探 [cann-recipes-infer-issue-1-rfc-deepseek-v3-2-exp-w8a8c16](https://gitcode.com/cann/cann-recipes-infer/issues/1)
- doc 披露 / 仓自报（@2c45117）：W8A8C8 精度表；早版口径（PR 期 doc）BF16=89.9/73.6/88.9/92.4 并存注记。溯源下探 [cann-recipes-infer-issue-8-rfc-deepseek-v3-2-exp-w8a8c8](https://gitcode.com/cann/cann-recipes-infer/issues/8)
- doc 披露 / 仓自报（@d3c31919e4ac）：W8A8C8/W4A8C8 精度表与 issue 引用逐格一致（引用官方指南、非提问者自测）。溯源下探 [cann-recipes-infer-issue-105-question-dsv3-2-w8a8c8-w4a8c8](https://gitcode.com/cann/cann-recipes-infer/issues/105)

固定 `2f82d10467e6fe8dae81c97a2cdac78d733a6703` 指南的后版精度表已与本卡W8A8C8/W4A8C8逐格核对。具体评测硬件、命令和重复测量仍未补齐，保持draft和未知平台。

## 本轮来源核对与剩余缺口

已将早版 `cc9e59db7a11` 和后版 `d3c31919e4ac` 解析成完整提交并重新读取原表：早版 W8A8C16 的 89.9/73.6/88.9/92.4 基线及后版三档分数均可追溯到固定指南，不再只依赖 Issue 转述。

Issue #8 的评论写有“A3 8机”，但对应内容是 64K/1K、每卡 batch 8、MTP1 的算子预期时延，不能用来绑定这两张模型精度表。指南中的 A3 部署/性能说明也不是精度评测运行日志。硬件、权重与评测配置、重复样本仍缺失，因此保留 draft 与空平台，不新增 Scope/verified。
