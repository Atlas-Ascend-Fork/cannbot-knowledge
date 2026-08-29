---
type: Runbook
title: 多卡 MTP 推理打点计时抖动 —— 计时前 dist.barrier 对齐各 rank
description: 多卡 MTP 推理打点计时抖动 —— 计时前 dist.barrier 对齐各 rank。多卡 MTP（multi-token prediction / 投机解码）推理做打点计时时，测得耗时与实际执行性能有偏差、抖动异常——main/MTP 小模型的计时不可信。做多卡 MTP 性能回归/profiling 时若数字飘忽，先怀疑这里。
tags:
- task.debugging
- topic.speculative_decoding
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/23
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 多卡 MTP 推理打点计时抖动 —— 计时前 dist.barrier 对齐各 rank

## 信号

多卡 [MTP](../../concepts/techniques/mtp_speculative_decoding.md)（multi-token prediction / 投机解码）推理做打点计时时，测得耗时与实际执行性能有偏差、抖动异常——main/MTP 小模型的计时不可信。做多卡 MTP 性能回归/profiling 时若数字飘忽，先怀疑这里。

## 触发条件 / 根因

MTP 后处理存在大量 H2D 拷贝与 npu sync 操作 → MTP 小模型卡间进度不同步 → 各 rank 在计时区起点未对齐，计时段包含了卡间不同步带来的抖动。典型计时区起点在早退分支之后进入 `torch.npu.synchronize()` + `start_time = time.time()`，此前各 rank 因异步进度不齐。

## 修法

在 `torch.npu.synchronize()` 与 `start_time = time.time()` **之前**插入一次全局 barrier，强制所有 rank 汇合到同一点再启动计时：

```python
dist.barrier()          # 对齐各 rank，剔除卡间异步带来的打点抖动
torch.npu.synchronize()
start_time = time.time()
```

`dist.barrier()` 剔除卡间进度不齐带来的打点抖动，使 main/MTP 模型的计时更真实反映各自执行开销。这是分布式 profiling 的常规做法（计时前对齐各 rank），改变的是**验证/测量方式**、非模型执行路径。

## 边界

参考实现见 [DeepSeek-V3.2-Exp](../../concepts/models/deepseek_v3_2_exp.md) 的 `model_infer.py::Infer`（main + MTP 小模型）。源未给前后计时数字，"barrier 降低打点抖动"是作者陈述意图 + 分布式 profiling 常规，机制自洽但无独立复测，故不写量化收益。MTP 收益与时延度量本身另见 [mtp-benefit-sparse-attention-and-latency-metric](../../optimizations/experience/cases/mtp_benefit_sparse_attention_and_latency_metric.md)。

## Evidence

- `diff 事实`（@11c5c88b）：`import torch.distributed as dist` + `dist.barrier()`（带注释）确在 merged diff、插在计时起点之前。"barrier 降低打点抖动"为作者陈述意图，效果层未并入事实面。
- 溯源下探：[cann-recipes-infer-pr-23-feat-optimize-for-data-process-between-models](https://gitcode.com/cann/cann-recipes-infer/merge_requests/23)

<!-- cannbot:related:start -->
## 相关

- [MTP / 投机解码 decode 计时采集口径：累加每步全部 draft 前向、每 decode 步记一条完整耗时、分「每步」与「每 token」两指标](mtp_decode_timing_collection_granularity.md)（`related`）：- 多卡 MTP 计时前 `dist.barrier` 对齐各 rank、剔除卡间异步抖动见 ［multicard-mtp-timing-barrier］(../validations/multicard_mtp_timing_barrier.md)。；在 `torch.npu.synchronize()` 与 `start_time = time.time()` **之前**插入一次全局 barrier，强制所有 rank 汇合到同一点再启动计时：。采集卡要求每步记录 main 与全部 draft 的完整耗时，barrier 卡补上多卡情况下计时起点对齐的具体插入位置，使该记录不混入 rank 间进度差。
- [MTP / 投机解码 decode 计时：拆「每 step 时延」与「每等效 token 时延」两口径分报](../../optimizations/experience/rules/mtp_decode_timing_two_metric_split.md)（`related`）：“`dist.barrier()` 剔除卡间进度不齐带来的打点抖动，使 main/MTP 模型的计时更真实反映各自执行开销。”；“- **每等效 token 时延**（average equivalent latency of MTP-n）= `time / (累计接受数 + step 数)`：每个真正吐出 token 的有效耗时，反映投机接受的吞吐收益。”。多卡计时先对齐 rank，再按等效 token 分母解释投机收益，避免把同步抖动和指标口径混为一体。
<!-- cannbot:related:end -->
