---
type: Optimization
title: LongCat-Lite A2/A3 入图案例：NgramEmbedding host gap 与精度边界
description: 记录固定报告的 NgramEmbedding 图外时间和 GE 入图收益，区分 A2/A3 数据、稳态条件与 token 分歧；报告的语义等价判断不作为本次精度验收。
tags:
- task.optimization
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/8fd8db72e333d38e15e54b8907a45da6134fa8fc/models/longcat_flash_lite/optimization_report.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/8fd8db72e333d38e15e54b8907a45da6134fa8fc/models/longcat_flash_lite/README.md
  role: constraint
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/8fd8db72e333d38e15e54b8907a45da6134fa8fc/models/longcat_flash_lite/models/modeling_longcat_flash_lite.py
  role: implementation
created_at: '2026-10-20T12:16:14Z'
updated_at: '2026-10-20T12:49:18Z'
platforms:
- a2
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
      objective:
      - latency
      - tpot
      model_features:
        all_of:
        - moe
        - mla
      execution_mode:
      - ge_graph
      quantization:
      - bf16
      parallelism:
        all_of:
        - tp
      framework:
      - cann_executor
---

# LongCat-Lite A2/A3 入图案例：NgramEmbedding host gap 与精度边界

## 条件与规则入口

本案例补充[图模式决策](../rules/graph_mode_enable_decision_profiling.md)，证据固定 `8fd8db72e333d38e15e54b8907a45da6134fa8fc`。README 明确支持 Atlas A2/A3；本例讨论 LongCat-Flash-Lite、BF16、TP8、Decode GE 图路径，不能用来预测其他模型的收益。

## 触发与实施差异

报告在设备 profile 中看到 NgramEmbedding 占比小于 5%，随后用同步分段计时报告图外 embedding 约 11.20 ms、已编译 Decode 约 7.06 ms。作者将多小算子、Python 下发与通信 launch 等列为原因；本次没有原始时间线，不把差值视为已经独立归因的纯下发开销。

报告描述将 Ngram 上下文改为 buffer、原地更新，把带 host 数据依赖的 shift-right 路径改写，并将 embedding 纳入编译范围。固定建模源码可见 `ngram_context` buffer、`init_ngram_cache`、`copy_` 及 eager/图路径不同的向量化实现；本次没有闭合整个执行器调用图或运行模型。

## 来源报告的结果

报告给出以下同阶段对比，均为来源自报：

| 平台 | Ngram 在图外 | Ngram 入图后 | 指标 |
|---|---:|---:|---|
| A2 / 910B 32GB | 18.50 ms | 7.14 ms | Decode 平均每 token 时间 |
| A3 / 910_93 64GB | 12.01 ms | 5.86 ms | Decode 平均每 token 时间 |

报告的主要工作负载为 TP8、BF16、batch=1、输入 1024、输出 128；文档说明稳态剔除 warmup，部分阶段记录三轮、该增量记录连续多次/两组值，未提供完整原始样本、方差或完整软件包版本。不能用后续 MLA-Prolog 优化后的数字替代本次对比，也不能将稳态 Prefill 当成冷启动耗时。

## 精度与适用边界

报告承认阶段 3.5 前约 20 个 token 一致，之后出现 token 分歧，并将其解释为 BF16 累加顺序改变、语义等价。该解释是作者判断，不是本次精度验证；不能由 BF16 或“文本看起来合理”直接认定无回归。后续 A3 MLA-Prolog 阶段还另有分歧，不能与本次对比混用。

复现时独立验收 logits/任务精度及业务允许误差，并比较 warmup 后的重复测量。若输出不满足要求，恢复对应版本原执行路径、配置与缓存后重测。本次未执行性能、精度或回退实验，也未新增 `verified`。
