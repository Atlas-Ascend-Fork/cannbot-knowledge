---
type: Runbook
title: MTP / 投机解码 decode 计时采集口径：累加每步全部 draft 前向、每 decode 步记一条完整耗时、分「每步」与「每 token」两指标
description: MTP / 投机解码 decode 计时采集口径：累加每步全部 draft 前向、每 decode 步记一条完整耗时、分「每步」与「每 token」两指标。给开启 MTP（多 token 预测 / 投机解码）的 decode 采集时延统计时，日志里的 decode 时延数值失真——无报错、无异常，只是数不对：单步耗时被系统性低估、按记录数算的平均和 IQR 离群过滤口径被打乱、拿到一个含义模糊的 "average inference time cost" 分不清是每步还是每 token。
tags:
- task.debugging
- topic.speculative_decoding
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/61
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# MTP / 投机解码 decode 计时采集口径：累加每步全部 draft 前向、每 decode 步记一条完整耗时、分「每步」与「每 token」两指标

## 信号（现象）

给开启 [MTP](../../concepts/techniques/mtp_speculative_decoding.md)（多 token 预测 / 投机解码）的 decode 采集时延统计时，日志里的 decode 时延数值失真——无报错、无异常，只是数不对：单步耗时被系统性低估、按记录数算的平均和 IQR 离群过滤口径被打乱、拿到一个含义模糊的 "average inference time cost" 分不清是每步还是每 token。

## 触发条件 / 根因

一个 decode 步 = 1 次 main 前向 + `next_n` 次 draft(MTP) 前向，产出 `1 + accepted_num` 个 token。若计时采集有以下缺陷即失真：

1. **只回传最后一个 draft 步的耗时**：draft 循环里把当轮耗时赋给标量、每轮覆盖，结束只返回最后一轮 → 前 `next_n-1` 个 draft 前向耗时被丢弃，单步耗时被低估。
2. **main 与 draft 耗时被拆成两条独立记录追加**：于是 `len(rec) == 2 × 步数`，每条记录只是「半个 step」（纯 main 或单个 draft），混进按记录数的平均（`总时间 / token_count`，`avg_token_per_round = token_count / len(rec)`）与 IQR 离群过滤，统计口径被打乱。
3. **只输出一个泛化标注的时延**：无法区分「每 decode 步时延」与「每生成 token 时延」这两个语义不同的量。

## 修法

- **累加一个 decode 步内所有 draft 前向的耗时**（把「返回标量」改成「返回逐步耗时 list」），不要只留最后一个。
- **每个 decode 步记一条完整耗时** `infer_time_main + sum(所有 draft 步耗时)`，令 `len(rec) == 步数`，使按记录的平均与 IQR 离群过滤口径正确。
- **分两个语义不同的指标上报**：
  - 每步平均时延 = 总时间 / 步数；
  - MTP-N 等效单 token 时延 = 总时间 / 生成 token 数（`total_tokens = 被接受的 draft token 数 + main token 数`）——反映投机解码相对单 token 解码的加速收益。

## 可迁移原则

- 给投机解码 / MTP 做计时：一个 decode 步 = 1 main + N draft，**别只计一个 draft、别把 main 与 draft 拆成两条「半步」记录**，否则按记录数的平均与离群过滤全部失真。每步一条 `main + sum(draft)` 完整记录是正确的采集粒度。
- 投机解码要分「每步时延」与「等效单 token 时延」两个口径报——前者是执行开销、后者才反映加速收益，混用会读错加速比。
- 这类缺陷静默失真（不 crash），只能靠核对采集逻辑发现；性能回归时若 MTP 时延数飘忽 / 不合理，先查采集粒度。

## 参考实现及其约束

参考 cann-recipes-infer DeepSeek-V3.2-Exp（[deepseek-v3.2-exp](../../concepts/models/deepseek_v3_2_exp.md)）的 MTP 计时路径（`model_infer.py` 的 `mtp_post_process` / `obtain_mtp_stats`、executor 的 `process_infer_time`：跳过首条 prefill、按 IQR 上界剔离群后返回 `总时间 / token_count`）。等效单 token 时延的**归一基数**另有讲究（取稳态平均接受数而非首 batch）见下「相关经验」。源未给修复前后 ms 数值。

## 相关经验

- MTP 等效时延的归一基数（用稳态平均接受 token 数、别用首 batch）与 DSA 上 MTP 收益按模块分化（SFA 不吃 MTP）见 [mtp-benefit-sparse-attention-and-latency-metric](../../optimizations/cases/mtp_benefit_sparse_attention_and_latency_metric.md)。
- 多卡 MTP 计时前 `dist.barrier` 对齐各 rank、剔除卡间异步抖动见 [multicard-mtp-timing-barrier](../validations/multicard_mtp_timing_barrier.md)。

## Evidence

- `diff 事实`（@4444dbc5）：`model_infer.py`（+18/-10）三处改动——draft 耗时改累加 list、采集改 `infer_time_main + sum(mtp)` 单条记录、`obtain_mtp_stats` 拆「每步平均」与「MTP-N 等效单 token」双指标；`process_infer_time` 的 `总时间 / token_count` 语义确认两指标口径。归因主语为本仓 DeepSeek-V3.2-Exp 建模脚本 / 该修复，非模型厂商；无 benchmark 数值故不作加速比断言。溯源下探：[cann-recipes-infer-pr-61-fix-fix-mtp-time-collection-bug](https://gitcode.com/cann/cann-recipes-infer/merge_requests/61)