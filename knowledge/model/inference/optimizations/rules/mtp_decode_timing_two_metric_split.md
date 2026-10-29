---
type: Optimization
title: MTP / 投机解码 decode 计时：拆「每 step 时延」与「每等效 token 时延」两口径分报
description: MTP / 投机解码 decode 计时：拆「每 step 时延」与「每等效 token 时延」两口径分报。给 MTP（multi-token prediction，一次前向出 next-n 步草稿）或任意投机解码做 decode 阶段计时、想读出投机接受带来的加速收益时（技术见 mtp-speculative-decoding）。 症状：只报了一个「平均推理时延」，却看不出投机解码到底加速了多少、每步开销又是多少——「吞吐收益」与「每步成本」两件事被一个数糊在一起，加速比读不出来。
tags:
- task.optimization
- topic.speculative_decoding
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/211
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/226
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-22T10:41:05Z'
platforms:
- agnostic
---

# MTP / 投机解码 decode 计时：拆「每 step 时延」与「每等效 token 时延」两口径分报

## 适用场景 / 条件

- 给 MTP（multi-token prediction，一次前向出 next-n 步草稿）或任意投机解码做 decode 阶段计时、想读出投机接受带来的加速收益时（技术见 [mtp-speculative-decoding](../../concepts/techniques/mtp_speculative_decoding.md)）。
- 症状：只报了一个「平均推理时延」，却看不出投机解码到底加速了多少、每步开销又是多少——「吞吐收益」与「每步成本」两件事被一个数糊在一起，加速比读不出来。

## 规则：两口径分别上报

对同一段 decode 计时 `time`，并列产出两个量、分开上报：

- **每 loop step 时延** = `time / step 数`：一次 decode 迭代的原始耗时（每步成本，与是否投机无关）。
- **每等效 token 时延**（average equivalent latency of MTP-n）= `time / (累计接受数 + step 数)`：每个真正吐出 token 的有效耗时，反映投机接受的吞吐收益。

两者是**不同的量，必须并列分报**。把它们混成一个数（如按 `time / (接受数 + step 数)` 算却标成「average inference time」）会让 MTP 场景下含义不清——它属于等效 token 时延，但名称未表达其分母；单独上报又不能同时体现每步成本，无法据此区分吞吐收益与迭代开销。

## 依据 / 为什么

- 投机解码的价值是「一步 decode 吐出 >1 个被接受 token」。所以吞吐收益只有把耗时除以「实际吐出的 token 数」（接受数 + step 数）才看得见；而每步的原始耗时（除以 step 数）反映的是单次迭代成本，与投机与否无关。两个视角回答两个不同问题，缺一则无法对比。
- 归属推论：主模型 / MTP 草稿 / warm-up、prefill / decode 的计时日志要按前缀区分，避免把主模型与 MTP 草稿的耗时混在一条统计里读花。
- 多 batch 统计时，接受数采用对应计时区间的平均接受数，不取首 batch 的接受数代替全批统计。来源 PR226 将 `total_accepted_num[0]` 改为平均接受数后计算 `total_tokens = avg_accepted_num + cnt`；平均的维度、是否排除 warm-up 均应与计时区间一致。

## 反例（勿做）

- 只上报一个混算数并标成「average inference time」：MTP 下语义不清，读者无从判断加速比。
- 计时日志不加前缀、把 main / MTP 草稿 / warm-up 的耗时混记：warm-up 与草稿开销会污染主模型 decode 读数。

## 参考实现及其约束

- 参考实现在 cann-recipes-infer 的 DeepSeek-R1 MTP 计时路径：`models/deepseek-r1/models/mtp.py::InferMTP.obtain_mtp_stats` 并列计算 `equivalent_infer_time = time/(accepted_num+cnt)` 与 `avg_infer_time = time/len(infer_time_rec)`，作为两个分别上报的量；`runner_deepseek.py::DeepSeekRunner.model_inference` 的计时日志按 `prefix` / `warm_up` 前缀化。
- 这是该参考实现在 DeepSeek-R1 上的具体落法；两口径拆分与日志前缀化本身是通用于任意 MTP / 投机解码 decode 计时的度量规则，迁移时不受该模型代码约束。

## Evidence

- `diff 事实`（@5801542bb6d5）：`mtp.py::InferMTP.obtain_mtp_stats` 计时整改后并列计算 `equivalent_infer_time = time/(accepted_num+cnt)` 与 `avg_infer_time = time/len(infer_time_rec)`；`runner_deepseek.py::DeepSeekRunner.model_inference` 计时日志按 `prefix`/`warm_up` 前缀化。核心断言（两口径公式并列上报）为读到且对上的 diff 事实，范围限定 MTP 投机解码 decode 计时路径，未外推为通用律。
- 平均接受数的修正来源：[PR226](https://gitcode.com/cann/cann-recipes-infer/merge_requests/226)；原案例中的这项计时约定集中在本规则维护。
- 溯源下探：[cann-recipes-infer-pr-211-feat-r1-yaml](https://gitcode.com/cann/cann-recipes-infer/merge_requests/211)
- 相关：MTP 收益按模块分化 + 等效时延归一基数（取稳态平均接受数、非首 batch）见 [mtp-benefit-sparse-attention-and-latency-metric](../cases/mtp_benefit_sparse_attention_and_latency_metric.md)；多卡 MTP 计时前 `dist.barrier` 对齐各 rank 见 [multicard-mtp-timing-barrier](../../runbooks/validations/multicard_mtp_timing_barrier.md)。

## Executor 固定版本的统计字段

> 来源：`docs/design/mtp_design.md` "3. MTP 指标介绍"；`executor/offline/offline_inference.py:149-184`、`executor/offline/infer.py:64-102`（`log_results`）。

MTP 启用时框架统计三个核心指标，用于量化 decode 阶段的收益（`next_n` = MTP draft 数）：

| 指标 | 公式 | 含义 |
|------|------|------|
| 平均接受率 `avg_accept_rate` | `total_accept_tokens / total_spec_tokens` | MTP 预测准确程度，越高表示 MTP 模型与主模型越一致 |
| 平均接受长度 `avg_accept_length` | `total_accept_tokens / spec_num_forward_ct + 1` | 平均每次 decode 迭代实际产出的 token 数 |
| 平均等效时延 `avg_equivalent_time` | `avg_decode_time / avg_accept_length` | 等效于每生成一个有效 token 的平均耗时 |

其中：

- `total_spec_tokens = sum(spec_num_forward_ct) × next_n`：MTP 模型推测的总 token 数。
- `total_accept_tokens = sum(spec_num_accepted_tokens)`：主模型验证后接受的总 token 数。
- `spec_num_forward_ct`（求和后）：前向传播次数；接受长度公式的 `+1` 表示主模型每次验证至少产出 1 个有效 token（含主模型本身那个 token）。
- `avg_decode_time`：decode 阶段平均前向耗时，包括一次主模型推理 + `next_n` 次 MTP 模型推理（`infer.py` 中取 `infer_time[1:]` 的均值，跳过首步 prefill）。

**指标来源（offline 推理）**：`offline_inference.py` 在请求完成后逐请求收集 `mtp_stats`（`spec_num_accepted_tokens` / `spec_num_forward_ct` / `valid_output_len`，仅 `request.mtp_info` 存在时收集）；`infer.py` 的 `log_results` 在 `next_n > 0` 时据此算出三指标并打印（accept length / accept rate / equivalent latency）。

**指标来源于 executor 侧逐轮累计**：每请求的 `spec_num_accepted_tokens` 由 `update_mtp_info(accepted_num, ...)` 以 `+= accepted_num` 累计（`forward_data_info.py:164-165`），其中 `accepted_num` 是 [cann-executor](../../concepts/frameworks/cann_executor.md) / MTPInfo 侧记录的「当轮被接受 token 数」（与上文 `MTPInfo.accepted_num` 同口径）。各模型路径里同名/同概念的「被接受 draft token 数」（如 Qwen3-Next GDN 融合算子的 `num_accepted_tokens`）以各自代码为准、未必是同一变量。指标的直观意义：接受长度越大 → 一次前向多产出有效 token → 等效时延越低，这是 MTP decode 加速的量化口径。

统计字段已对照 [固定 offline `log_results`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/executor/offline/infer.py) 核对；其 `infer_time[1:]` 排除首步是该入口约定，不代表其他在线或框架计时天然相同。零草稿/零前向不应代入这些分式，汇报为不可计算并检查输入。
