---
type: Optimization
title: LongCat 多流控核案例（已并入优化规则）
description: 保留原案例入口；拖尾信号、分核机制、实施风险和证据统一见 Decode 多流控核规则，避免重复维护。原 agnostic 声明不作为跨平台依据，已核验主结论限定 Atlas A3。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.graph_execution
- topic.implementation.synchronization
status: deprecated
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/longcat_flash_optimization.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:24:39Z'
platforms:
- a3
replaced_by: model/inference/optimizations/rules/decode_multi_stream_overlap_core_balance
---

# LongCat 多流控核案例（已并入优化规则）

本案例与[Decode 多流控核规则](../rules/decode_multi_stream_overlap_core_balance.md)描述同一个优化决策。原案例的双流拖尾信号、分核风险、AFD 边界和示例差异已并入该规则；后续从规则入口阅读和维护，避免两份同义正文产生分歧。

原卡的 `agnostic` 不构成跨平台证据。已核验的主结论限定固定 LongCat 实现及官方文档声明的 Atlas A3 范围；当前 AFD 与非 AFD 分支的区别由替代卡维护。本入口保留历史引用，未新增平台验证或性能复现结论。
