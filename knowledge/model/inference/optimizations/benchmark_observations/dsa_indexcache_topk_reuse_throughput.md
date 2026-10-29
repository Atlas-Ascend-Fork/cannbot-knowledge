---
type: Optimization
title: DSA IndexCache 跨层 top-k 复用的 GLM-5 来源观测（平台待核验）
description: GLM-5 W8A8 的来源自报吞吐与精度数据；index_topk_freq 按层控制 top-k 重算，不能解释为跨解码步缓存。卡型及实际
  vLLM 依赖版本仍待补。
tags:
- task.testing
- topic.performance.analysis
- topic.attention
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/8398
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ba074eb4bf095264b2d1280447281633ab66e112/vllm_ascend/attention/sfa_v1.py
  role: evidence
- resource: https://github.com/vllm-project/vllm/blob/faab18955407f256c7ced2d227ce097f472db16d/docs/features/index_cache.md
  role: supporting
- resource: https://github.com/vllm-project/vllm/blob/faab18955407f256c7ced2d227ce097f472db16d/vllm/model_executor/models/deepseek_v2.py
  role: supporting
- resource: https://github.com/vllm-project/vllm/blob/faab18955407f256c7ced2d227ce097f472db16d/vllm/model_executor/layers/mla.py
  role: supporting
- resource: https://github.com/vllm-project/vllm/blob/6f786f2c506cb07f4566771fdc62e640e2c4a176/vllm/model_executor/models/deepseek_v2.py
  role: supporting
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-10-22T03:20:00Z'
platforms: []
---

# DSA IndexCache 跨层 top-k 复用的 GLM-5 来源观测（平台待核验）

## 适用场景与机制

评估 GLM-5 W8A8 服务化请求中的 DSA 索引选择开销时，可参考 PR8398 的两组自报结果。IndexCache 是同一次前向的跨层 top-k 索引复用：Full 层计算并写入索引，后续 Shared 层读取该 buffer；`index_topk_freq=4` 按层指定重算频率，不表示每四个生成 token 或解码步重算一次。

固定上游实现用 `layer_id` 与 `index_topk_freq` 决定 `skip_topk`，首层等边界按源码处理；不能把“约四分之一层重算”当作无边界例外的计数承诺。来源没有提供独立的层间索引相似度测量，不据此保证精度。

## 环境与依赖缺口

PR 自报模型 `/nas/disk1/GLM-5-w8a8`、vLLM v0.19.0，未提供具体卡型和完整 CANN 环境。配置为 `use_index_cache=true`、`index_topk_freq=4`；baseline 不启用复用。

PR 标注的 vLLM main 是 `6f786f2c506cb07f4566771fdc62e640e2c4a176`。该提交的 `deepseek_v2.py` 尚未包含后来上游 PR37735 引入的 `use_index_cache/index_topk_freq` 选层逻辑；上游合并提交是 `faab18955407f256c7ced2d227ce097f472db16d`。本卡引用后者解释机制，不把它补写成 PR8398 的真实实验依赖。GLM-5 实际使用的模型适配代码和完整依赖组合仍待原始记录确认，保留 draft、空平台和缺省 Scope。

## 来源命令

并发 1、10 个请求的原始命令：

```bash
vllm bench serve \
  --backend openai-chat --model glm-5 --served-model-name glm-5 \
  --tokenizer /nas/disk1/GLM-5-w8a8 --dataset-name random \
  --max-concurrency 1 --num-prompts 10 \
  --random-input-len 20480 --random-output-len 100
```

另一组将并发设为 3、请求数设为 30。上述是客户端命令，不代替缺少的服务端启动和模型依赖记录。

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


- C-Eval：baseline 0.9008 → IndexCache `freq=4` 0.9063——该次报告分数未下降；没有重复测量资料，不据此保证复用的精度或统计显著性。


## 固定实现与边界

Ascend 合并版本 `ba074eb4bf095264b2d1280447281633ab66e112` 的 MLA 构造参数携带 `skip_topk`，SFA 路径在复用时读取 `topk_indices_buffer`，非复用层计算后更新它。该结构确认层间共享索引，不证明相邻解码时刻的索引保持不变。buffer 的 token 对齐、模型选层和每次前向的更新边界必须与实际模型适配共同核对。

仅保留两组来源数据，不将 Prefill/Decode 的收益互相外推，也不因 C-Eval 单点没有下降就保证质量。未披露 warmup、重复次数、方差或完整服务端基线，未独立复测。

## 验证与回退

先补真实卡型、模型代码和 vLLM 依赖，再确认 Full/Shared 层分布与共享 buffer 的读写顺序；检查不同请求和前向之间没有读到旧索引。按同输入、并发、权重和评测配置比较精度及端到端指标。输出异常或无净收益时关闭 `use_index_cache`，回到逐层重新选择；未在本仓执行回退。

相关内存预算见 [DSA 显存规则](../rules/dsa_decode_memory_budget_indexer_cache.md)，量化选型见 [LI 量化规则](../rules/quant_lightning_indexer_latency.md)。

## Evidence

- [Ascend PR8398](https://github.com/vllm-project/vllm-ascend/pull/8398)：GLM-5 数据与自报依赖。
- [上游 IndexCache 文档](https://github.com/vllm-project/vllm/blob/faab18955407f256c7ced2d227ce097f472db16d/docs/features/index_cache.md)：明确跨层复用与按层频率。
- [上游模型选层实现](https://github.com/vllm-project/vllm/blob/faab18955407f256c7ced2d227ce097f472db16d/vllm/model_executor/models/deepseek_v2.py)与[MLA 说明](https://github.com/vllm-project/vllm/blob/faab18955407f256c7ced2d227ce097f472db16d/vllm/model_executor/layers/mla.py)：按 layer_id 决定 skip_topk。
- [Ascend SFA 实现](https://github.com/vllm-project/vllm-ascend/blob/ba074eb4bf095264b2d1280447281633ab66e112/vllm_ascend/attention/sfa_v1.py)：读取/更新共享索引。
