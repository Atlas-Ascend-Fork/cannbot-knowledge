---
type: Optimization
title: DSA 长序列 Decode 中 MTP 收益按模块分化的分析案例
description: 保留 DeepSeek-V3.2-Exp 在 64K、4 batch 下的 MLA、LI、SFA 搬运量和计算量分析；计时定义统一引用 MTP 计时规则，不将模块分析外推为整网实测加速比。
tags:
- task.optimization
- topic.attention
- topic.speculative_decoding
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/3
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/226
  role: evidence
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/deepseek_v3.2_exp_inference_guide.md
  role: supporting
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:24:39Z'
platforms:
- agnostic
---


# DSA 长序列 Decode 中 MTP 收益按模块分化的分析案例

## 适用场景
- 在稀疏注意力结构上评估「要不要上 MTP、能加速多少」（[mtp-speculative-decoding](../../concepts/techniques/mtp_speculative_decoding.md)）。MTP 靠一次前向多推 token 提高计算访存比，但**收益不是全网均匀**：在 [dsa](../../concepts/modules/dsa.md)（[lightning-indexer](../../concepts/kernels/lightning_indexer.md) + [sparse-flash-attention](../../concepts/kernels/sparse_flash_attention.md)）上按模块分化，SFA 的收益需按所列访存条件另验。
- 阅读本案例前，先按 [MTP 计时规则](../rules/mtp_decode_timing_two_metric_split.md) 对齐指标。

## 收益按模块分化（DSA / 长序列 decode）
以 64K 序列、4batch 的搬运/计算量分析（doc 原表）：

| 模块 | 场景 | KV 搬运量(MB) | Cube 计算量(GFlops) | QKᵀ 搬运量(MB) |
|---|---|---:|---:|---:|
| MLA | 非MTP | 144 | 19.33 | 32 |
| MLA | MTP1 | 144 | 38.65 | 64 |
| SFA | 非MTP | 4.5 | 0.60 | 1 |
| SFA | MTP1 | 9 | 1.21 | 2 |
| LI | 非MTP | 32 | 2.15 | 16 |
| LI | MTP1 | 32 | 4.29 | 32 |

- **Lightning Indexer（潜在收益）**：长序列下 LI 耗时占比更高，其 K Cache 搬运与稠密 MLA 相似（KV 搬运量 MTP1 与非 MTP 均为 32MB），MTP 提高其计算访存比。对照：Full-Attention 的 MLA 无论是否 MTP，KV 搬运量相同 → MTP 提升计算访存比；固定来源的 Atlas A3/CANN MLA 实践自报 MTP1 算力利用比可达 70%+，不是跨平台预期。
- **Sparse Flash Attention（访存可能增长）**：每个 q token 选 2048 个激活 kv token，极端下 MTP1 需搬运的 KV Cache 是非 MTP 的两倍（4.5→9MB），离散访存代价上升，MTP 难获加速。
- **整网（仍需验收）**：DSA 稀疏显著降低长序列计算量、削弱 Attention 占比，剩余算子（Matmul 等）能达更好计算访存比，来源判断整网可能受益，但未提供本组MTP开/关的独立端到端测量。

→ 结论：DSA 模型上 MTP 收益主要来自 LI 与非 Attention 算子，SFA应按每q独立TopK的访存条件验收，不能从本组分析推出所有DSA场景均无收益。源未给整网 MTP on/off 的端到端加速比数字。

## 如何衡量本案例的收益

每步成本、每等效 token 时延以及平均接受数的定义统一见 [MTP 计时规则](../rules/mtp_decode_timing_two_metric_split.md)。本案例只保留 DSA 模块分析；比较 MTP on/off 时应采用同一计时范围和接受数口径。

## 参考实现及其约束
- 收益分析参考 [deepseek-v3.2-exp](../../concepts/models/deepseek_v3_2_exp.md)（DSA，64K/4batch 这一组分析，非独立端到端复测）；度量口径参考当前统一 Executor 的 offline 统计。搬运/计算量为 doc 披露的模型学分析量，不外推「越大越…」单调律。

## 相关经验
- [DSA IndexCache 跨层 top-k 复用观测（草稿）](../benchmark_observations/dsa_indexcache_topk_reuse_throughput.md)
- [投机解码接受率低时用熵校验放松拒绝采样阈值：threshold = min(exp(-H·α](../rules/spec_decode_entropy_verify_relax_rejection_threshold.md)

- 另见 [MTP / 投机解码 decode 计时：拆「每 step 时延」与「每等效 token 时延」两口径分报](../rules/mtp_decode_timing_two_metric_split.md)。
- 另见 [MTP / 投机解码 decode 计时采集口径：累加每步全部 draft 前向、每 decode 步记一条完整耗时、分「每步」与「每 token」两指标](../../runbooks/validations/mtp_decode_timing_collection_granularity.md)。


## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/3)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/226)（evidence）
- [deepseek_v3.2_exp_inference_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/deepseek_v3.2_exp_inference_guide.md)（supporting）
