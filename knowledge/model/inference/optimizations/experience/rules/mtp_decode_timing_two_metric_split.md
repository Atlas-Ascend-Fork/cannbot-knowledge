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
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# MTP / 投机解码 decode 计时：拆「每 step 时延」与「每等效 token 时延」两口径分报

## 适用场景 / 条件

- 给 MTP（multi-token prediction，一次前向出 next-n 步草稿）或任意投机解码做 decode 阶段计时、想读出投机接受带来的加速收益时（技术见 [mtp-speculative-decoding](../../../concepts/techniques/mtp_speculative_decoding.md)）。
- 症状：只报了一个「平均推理时延」，却看不出投机解码到底加速了多少、每步开销又是多少——「吞吐收益」与「每步成本」两件事被一个数糊在一起，加速比读不出来。

## 规则：两口径分别上报

对同一段 decode 计时 `time`，并列产出两个量、分开上报：

- **每 loop step 时延** = `time / step 数`：一次 decode 迭代的原始耗时（每步成本，与是否投机无关）。
- **每等效 token 时延**（average equivalent latency of MTP-n）= `time / (累计接受数 + step 数)`：每个真正吐出 token 的有效耗时，反映投机接受的吞吐收益。

两者是**不同的量，必须并列分报**。把它们混成一个数（如按 `time / (接受数 + step 数)` 算却标成「average inference time」）会让 MTP 场景下含义不清——既不是纯每步成本、也不是纯等效时延，无法从中区分吞吐收益与每步开销。

## 依据 / 为什么

- 投机解码的价值是「一步 decode 吐出 >1 个被接受 token」。所以吞吐收益只有把耗时除以「实际吐出的 token 数」（接受数 + step 数）才看得见；而每步的原始耗时（除以 step 数）反映的是单次迭代成本，与投机与否无关。两个视角回答两个不同问题，缺一则无法对比。
- 归属推论：主模型 / MTP 草稿 / warm-up、prefill / decode 的计时日志要按前缀区分，避免把主模型与 MTP 草稿的耗时混在一条统计里读花。
- 归一细节（配套）：等效时延的「接受数」应取稳态平均、非首 batch（单 batch 接受数抖动大）——见 [mtp-benefit-sparse-attention-and-latency-metric](../cases/mtp_benefit_sparse_attention_and_latency_metric.md)。

## 反例（勿做）

- 只上报一个混算数并标成「average inference time」：MTP 下语义不清，读者无从判断加速比。
- 计时日志不加前缀、把 main / MTP 草稿 / warm-up 的耗时混记：warm-up 与草稿开销会污染主模型 decode 读数。

## 参考实现及其约束

- 参考实现在 cann-recipes-infer 的 DeepSeek-R1 MTP 计时路径：`models/deepseek-r1/models/mtp.py::InferMTP.obtain_mtp_stats` 并列计算 `equivalent_infer_time = time/(accepted_num+cnt)` 与 `avg_infer_time = time/len(infer_time_rec)`，作为两个分别上报的量；`runner_deepseek.py::DeepSeekRunner.model_inference` 的计时日志按 `prefix` / `warm_up` 前缀化。
- 这是该参考实现在 DeepSeek-R1 上的具体落法；两口径拆分与日志前缀化本身是通用于任意 MTP / 投机解码 decode 计时的度量规则，迁移时不受该模型代码约束。

## Evidence

- `diff 事实`（@5801542bb6d5）：`mtp.py::InferMTP.obtain_mtp_stats` 计时整改后并列计算 `equivalent_infer_time = time/(accepted_num+cnt)` 与 `avg_infer_time = time/len(infer_time_rec)`；`runner_deepseek.py::DeepSeekRunner.model_inference` 计时日志按 `prefix`/`warm_up` 前缀化。核心断言（两口径公式并列上报）为读到且对上的 diff 事实，范围限定 MTP 投机解码 decode 计时路径，未外推为通用律。
- 溯源下探：[cann-recipes-infer-pr-211-feat-r1-yaml](https://gitcode.com/cann/cann-recipes-infer/merge_requests/211)
- 相关：MTP 收益按模块分化 + 等效时延归一基数（取稳态平均接受数、非首 batch）见 [mtp-benefit-sparse-attention-and-latency-metric](../cases/mtp_benefit_sparse_attention_and_latency_metric.md)；多卡 MTP 计时前 `dist.barrier` 对齐各 rank 见 [multicard-mtp-timing-barrier](../../../runbooks/validations/multicard_mtp_timing_barrier.md)。
