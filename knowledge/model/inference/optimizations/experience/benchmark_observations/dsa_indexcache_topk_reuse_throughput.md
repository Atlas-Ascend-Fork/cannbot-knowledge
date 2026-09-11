---
type: Optimization
title: DSA/SFA 长序列服务化：跨步复用 top-k 索引（IndexCache）摊薄 indexer 选择开销换吞吐（GLM-5 W8A8 一次观测）
description: 'DSA/SFA 稀疏注意力长序列服务化 decode 的一次可复现性能观测（benchmark_observation）：稀疏注意力每个前向步都要跑 top-k KV 索引选择（Lightning Indexer 从 KV 选参与稀疏注意力的位置），相邻解码步 top-k 索引时间稳定，可跨步复用缓存索引（IndexCache / index_topk_freq）摊薄 indexer 重算换吞吐。参考实现 vllm-ascend（vLLM NPU 适配仓，SFA 昇腾路径 sfa_v1.py + mla.py），开关 --hf-overrides ''{"use_index_cache": true, "index_topk_freq": 4}''（每 4 步重算一次、复用 3/4 索引）。GLM-5 W8A8、random 输入 20480/输出 100 的 vllm bench serve 观测：Concurrency 1 总 token 吞吐 1289.57→1502.87 tok/s（+16.54%）、Mean E2EL -14.19%、Mean TTFT -17.06%；Concurrency 3 吞吐 +16.87%、P99 ITL -22.48%，两组 0 failed。C-Eval 0.9008→0.9063 精度未劣化。数据为 PR 作者自报、无独立复测（doc 披露），仅两组受控配置，不外推其它模型/序列长度/复用频率。昇腾 NPU、W8A8 量化、long_sequence decode 场景。'
tags:
- task.testing
- topic.performance.analysis
- topic.attention
- topic.precision
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/8398
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# DSA/SFA 长序列服务化：跨步复用 top-k 索引（IndexCache）摊薄 indexer 选择开销换吞吐（GLM-5 W8A8 一次观测）

## 适用场景

在 [dsa](../../../concepts/modules/dsa.md)（[lightning-indexer](../../../concepts/kernels/lightning_indexer.md) 选 top-k + [sparse-flash-attention](../../../concepts/kernels/sparse_flash_attention.md) 稀疏注意力）类模型上做**长序列服务化 decode** 时评估「要不要跨解码步复用 top-k KV 索引」的收益，或需要一个该手段的量级参照。

- 背景：走稀疏注意力路径的模型，每个前向步都要跑一次 top-k 索引选择（indexer 从 KV 里选出参与稀疏注意力的位置），这是稀疏注意力 decode 开销的一部分；随序列变长，indexer 选择的总量随之增加。
- 通向该手段的判断：**每 N 步只重算一次、其余步复用上次缓存的 top-k 索引**（IndexCache / `index_topk_freq`），用少量精度冗余换掉大部分 indexer 重算。该手段的一般依据是相邻解码步 top-k 索引的时间稳定性（该类方法的公认前提），本 PR 未直接给出这一测量。已观测量级仅覆盖下述受控配置点。
- 不适用/边界：已观测数字为仓库自报、无独立复测，且只覆盖 GLM-5 W8A8 + 输入 20480 + `index_topk_freq=4`（复用 3/4 索引）这两组受控并发；不外推到其它模型/序列长度/复用频率（更高复用比可能掉精度，须实测）。

## 环境（hw/CANN/框架）

- 框架：vllm-ascend（vLLM 的 NPU 适配仓），vLLM 版本 v0.19.0（按 PR 描述）。昇腾具体卡型 / CANN 版本源未给出。
- 模型：[glm-5](../../../concepts/models/glm_5.md) W8A8（DSA/SFA 稀疏注意力，`tokenizer=/nas/disk1/GLM-5-w8a8`）。
- 手段开关：`--hf-overrides '{"use_index_cache": true, "index_topk_freq": 4}'`——`use_index_cache=true` 打开跨步索引复用；`index_topk_freq=4` 表示每 4 步重算一次 top-k、其余 3/4 步复用缓存索引。baseline 为不开该开关。

## 命令

```bash
vllm bench serve \
  --backend openai-chat --model glm-5 --served-model-name glm-5 \
  --tokenizer /nas/disk1/GLM-5-w8a8 --dataset-name random \
  --max-concurrency {1|3} --num-prompts {10|30} \
  --random-input-len 20480 --random-output-len 100
```

## baseline / optimized / metric

Concurrency 1（10 prompts，baseline → IndexCache `freq=4`）：

| metric | baseline | IndexCache freq=4 | Δ |
|---|---:|---:|---:|
| Benchmark duration (s) | 158.08 | 135.64 | -14.20% |
| Total token throughput (tok/s) | 1289.57 | 1502.87 | **+16.54%** |
| Mean TTFT (ms) | 10757.46 | 8922.62 | -17.06% |
| Mean TPOT (ms) | 57.53 | 52.86 | -8.12% |
| Mean E2EL (ms) | 15807.51 | 13563.86 | -14.19% |

Concurrency 3（30 prompts）：

| metric | baseline | IndexCache freq=4 | Δ |
|---|---:|---:|---:|
| Total token throughput (tok/s) | 1645.72 | 1923.37 | **+16.87%** |
| Mean TTFT (ms) | 13091.83 | 11148.76 | -14.84% |
| Mean TPOT (ms) | 247.58 | 210.51 | -14.97% |
| P99 ITL (ms) | 2300.33 | 1783.22 | -22.48% |
| Mean E2EL (ms) | 37142.37 | 31768.29 | -14.47% |

两组均 0 failed requests。总体量级：长序列（20480 输入）下开 IndexCache `freq=4` 相对 baseline 总 token 吞吐提升约 16.5%、平均 E2E 时延下降约 14%。

## correctness

- C-Eval：baseline 0.9008 → IndexCache `freq=4` 0.9063——复用 3/4 索引精度未劣化（分数不降反略升，属受控点观测，非「复用越多越好」的规律）。

## 参考实现

- 算法层做法：top-k 索引时间稳定时周期性复用——每 N 步只重算一次 top-k、其余步复用上次缓存的索引。
- 该做法在 vllm-ascend 的 SFA 昇腾路径（`vllm_ascend/attention/sfa_v1.py`）+ MLA 封装（`vllm_ascend/ops/mla.py`）落地，前向按 `skip_topk` 分支在复用缓存索引与重跑 top-k 选择之间切换，重跑时把结果写回缓存供后续复用步取用；`skip_topk` / `topk_indices_buffer` 等开关名与 buffer 结构均为该参考实现的细节。
- 数字为仓库自报、无独立复测，属 `doc 披露`。仅陈述上述两组受控配置，不写「频率越大越快」类单调规律。

## 相关经验

- 该手段的机制/前置条件/rollback（`use_index_cache` / `index_topk_freq` / `skip_topk` 前向分支）见配套 rule 型经验（同 PR）。
- DSA decode 的显存构成（indexer 另有 key cache，勿漏算）见 [dsa-decode-memory-budget-indexer-cache](../cases/dsa_decode_memory_budget_indexer_cache.md)。
- 压 Lightning Indexer 单算子时延的另一手段（量化算子选型）见 [quant-lightning-indexer-latency](../rules/quant_lightning_indexer_latency.md)；SFA 上 MTP 收益判断见 [mtp-benefit-sparse-attention-and-latency-metric](../cases/mtp_benefit_sparse_attention_and_latency_metric.md)。

## Evidence

- `doc 披露`：PR body 的 Benchmarking / Accuracy 段（vllm-project/vllm-ascend，合并 2026-05-07，merge commit `ba074eb4bf095264b2d1280447281633ab66e112`）——仓库自报、无独立复测。
- 溯源下探：[vllm-ascend-pr-8398-feature-indexcache-support-for-dsa-models](https://github.com/vllm-project/vllm-ascend/pull/8398)