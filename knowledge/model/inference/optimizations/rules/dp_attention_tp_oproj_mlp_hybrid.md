---
type: Optimization
title: 已归并：Attention DP 下的 o_proj 与 dense MLP 局部 TP
description: 旧规则保留为引用入口；通用局部 TP 决策统一到 local_tp_memory_heavy_projections，LongCat A3 的切分与通信细节移入独立案例。
tags:
- task.optimization
- topic.attention
- topic.parallelism
status: deprecated
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/0640521a817001f560fc30617acad41af585dfe1/models/longcat-flash/models/modeling_longcat_flash.py
  role: implementation
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/0640521a817001f560fc30617acad41af585dfe1/docs/models/longcat-flash/longcat_flash_optimization.md
  role: primary
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-20T12:49:18Z'
platforms:
- a3
replaced_by: model/inference/optimizations/rules/local_tp_memory_heavy_projections
---

# 已归并：Attention DP 下的 o_proj 与 dense MLP 局部 TP

本卡与已有局部 TP 规则重复，现保留迁移后的历史引用入口，不再独立维护一份规则。

- 选择哪些投影层做 TP、核对哪些条件及如何验证，统一见[局部 TP 决策](local_tp_memory_heavy_projections.md)。
- 固定 LongCat A3 的 o_proj K 轴 TP、dense MLP 分片以及 AllGather / AllToAll / ReduceScatter 细节，见[LongCat 案例](../cases/longcat_dp_tp_projections.md)。

原结论的证据限定 Atlas A3 和固定 LongCat 建模路径，没有独立 before/after；归并不扩大适用范围，也不证明其他模型可直接复用同一通信序列。
