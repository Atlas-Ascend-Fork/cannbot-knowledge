---
type: Optimization
title: 评估 MTP 推测解码收益：稀疏注意力(DSA)按模块分化、SFA 不吃 MTP + 等效时延度量口径
description: 评估 MTP 推测解码收益：稀疏注意力(DSA)按模块分化、SFA 不吃 MTP + 等效时延度量口径。在稀疏注意力结构上评估「要不要上 MTP、能加速多少」（mtp-speculative-decoding）。MTP 靠一次前向多推 token 提高计算访存比，但收益不是全网均匀：在 dsa（lightning-indexer + sparse-flash-attention）上按模块分化，别对 SFA 期待 MTP 加速。 同时给出 MTP 等效时延的正确度量口径，避免读错加速比。
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
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 评估 MTP 推测解码收益：稀疏注意力(DSA)按模块分化、SFA 不吃 MTP + 等效时延度量口径

## 适用场景
- 在稀疏注意力结构上评估「要不要上 MTP、能加速多少」（[mtp-speculative-decoding](../../../concepts/techniques/mtp_speculative_decoding.md)）。MTP 靠一次前向多推 token 提高计算访存比，但**收益不是全网均匀**：在 [dsa](../../../concepts/modules/dsa.md)（[lightning-indexer](../../../concepts/kernels/lightning_indexer.md) + [sparse-flash-attention](../../../concepts/kernels/sparse_flash_attention.md)）上按模块分化，别对 SFA 期待 MTP 加速。
- 同时给出 MTP 等效时延的正确度量口径，避免读错加速比。

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

- **Lightning Indexer（有效）**：长序列下 LI 耗时占比更高，其 K Cache 搬运与稠密 MLA 相似（KV 搬运量 MTP1 与非 MTP 均为 32MB），MTP 提高其计算访存比。对照：Full-Attention 的 MLA 无论是否 MTP，KV 搬运量相同 → MTP 提升计算访存比；MLA 算子在 MTP1 场景算力利用比可达 70%+。
- **Sparse Flash Attention（无效甚至有害）**：每个 q token 选 2048 个激活 kv token，极端下 MTP1 需搬运的 KV Cache 是非 MTP 的两倍（4.5→9MB），离散访存代价上升，MTP 难获加速。
- **整网（仍有收益）**：DSA 稀疏显著降低长序列计算量、削弱 Attention 占比，剩余算子（Matmul 等）能达更好计算访存比，故整网用 MTP 仍有较可观加速。

→ 结论：DSA 模型上 MTP 收益主要来自 LI 与非 Attention 算子，**不要指望 SFA 吃 MTP 加速**（可能因离散访存变差）。源未给整网 MTP on/off 的端到端加速比数字。

## 等效时延度量口径（读 MTP 加速比别踩坑）
- 度量「等效推理时延」（把多 token 推理折算成单 token 口径 = 实际时延 / 本次被接受的 token 数）时，**归一基数取稳态平均每 batch 接受 token 数（average accepted rate）**，即 `total_tokens = avg_accepted_num + cnt`。
- 反模式：取**首 batch** 的接受 token 数（`total_accepted_num[0]`）为基数——单个 batch 接受数抖动大、不具代表性，投机接受率只有多 batch 平均后才反映稳态，据首 batch 会系统性高/低估等效时延。日志/注释也别沿用「first batch」措辞误导解读。
- 适用面：MTP 等效时延统计（证据覆盖 DeepSeek-R1 与 DeepSeek-V3.2-Exp 两 runner），跨版本对比须同口径才可比。

## 参考实现及其约束
- 收益分析参考 [deepseek-v3.2-exp](../../../concepts/models/deepseek_v3_2_exp.md)（DSA，64K/4batch 这一组分析，非独立端到端复测）；度量口径参考同仓 DeepSeek-R1 / DSV3.2 的 MTP runner。搬运/计算量为 doc 披露的模型学分析量，不外推「越大越…」单调律。

## 相关经验
- [DSA/SFA 长序列服务化：跨步复用 top-k 索引（IndexCache）摊薄 ind](../benchmark_observations/dsa_indexcache_topk_reuse_throughput.md)
- [投机解码接受率低时用熵校验放松拒绝采样阈值：threshold = min(exp(-H·α](../rules/spec_decode_entropy_verify_relax_rejection_threshold.md)

- 另见 [MTP / 投机解码 decode 计时：拆「每 step 时延」与「每等效 token 时延」两口径分报](../rules/mtp_decode_timing_two_metric_split.md)。
- 另见 [MTP / 投机解码 decode 计时采集口径：累加每步全部 draft 前向、每 decode 步记一条完整耗时、分「每步」与「每 token」两指标](../../../runbooks/validations/mtp_decode_timing_collection_granularity.md)。


## Evidence
- `doc 披露`（@fa6892b）：DeepSeek-V3.2-Exp 推理 guide「MTP」小节的机制分析与搬运量/计算量表（首方 doc 分析，非独立复测的端到端 benchmark）。
- `diff 事实` + `评审确认`（@41af2991a3bd）：R1 与 DSV3.2 两 runner 同一改动——等效时延归一基数由首 batch 接受数改为稳态平均接受数、并删去「first batch」注释；评审确认「已经不是 first batch 了」。
- 溯源下探：[cann-recipes-infer-pr-3-feat-add-deepseek-v3-2-exp-model](https://gitcode.com/cann/cann-recipes-infer/merge_requests/3)、[cann-recipes-infer-pr-226-fix-cache-compile-print-time](https://gitcode.com/cann/cann-recipes-infer/merge_requests/226)
- 相关：接入约定见 [mtp-speculative-decode-model-onboarding](../../../guides/experience/interventions/mtp_speculative_decode_model_onboarding.md)；缓存/状态正确性见 [mtp-draft-cache-state-correctness](../rules/mtp_draft_cache_state_correctness.md)。

<!-- cannbot:related:start -->
## 相关

- [MTP / 投机解码 decode 计时采集口径：累加每步全部 draft 前向、每 decode 步记一条完整耗时、分「每步」与「每 token」两指标](../../../runbooks/validations/mtp_decode_timing_collection_granularity.md)（`related`）：度量「等效推理时延」（把多 token 推理折算成单 token 口径 = 实际时延 / 本次被接受的 token 数）；**每个 decode 步记一条完整耗时** `infer_time_main + sum(所有 draft 步耗时)`。前者定义最终折算目标，后者保证输入该指标的每步 main 与全部 draft 耗时完整采集，属于指标计算前后的直接验证链。
- [MTP / 投机解码 decode 计时：拆「每 step 时延」与「每等效 token 时延」两口径分报](../rules/mtp_decode_timing_two_metric_split.md)（`related`）：**归一基数取稳态平均每 batch 接受 token 数（average accepted rate）**；**每等效 token 时延**（average equivalent latency of MTP-n）= `time / (累计接受数 + step 数)`。前者规定等效时延分母中的接受数取值，后者定义该分母所在的指标公式，二者构成同一 MTP 时延度量链。
- [昇腾性能测量失真陷阱：不代表真实访存的测量输入·折算前被截断的度量口径](../anti_patterns/perf_measurement_distortion_input_and_metric.md)（`same_topic`）：折算路径用**浮点**均值，int 截断只允许出现在人读日志里；**归一基数取稳态平均每 batch 接受 token 数（average accepted rate）**。前者约束接受数保留小数，后者约束接受数采用稳态 batch 均值，二者共同决定 MTP 等效时延分母的可信口径。
<!-- cannbot:related:end -->
