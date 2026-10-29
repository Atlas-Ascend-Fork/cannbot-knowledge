---
type: Optimization
title: LongCat A3 SuperKernel 案例：非 KVP 路径的布局融合修复
description: 记录 PR332 将 reshape 下沉分支、恢复 bmm 与 transpose 相邻性的固定修复；不将历史 KVP 分支当作当前能力，也不保证所有算子均可融合。
tags:
- task.optimization
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/0640521a817001f560fc30617acad41af585dfe1/docs/models/longcat-flash/longcat_flash_optimization.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/0640521a817001f560fc30617acad41af585dfe1/models/longcat-flash/README.md
  role: constraint
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/086bbb1c49c0ea1a53e690481dac292b26390257/models/longcat-flash/models/modeling_longcat_flash.py
  role: implementation
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/332
  role: evidence
created_at: '2026-10-20T12:18:12Z'
updated_at: '2026-10-20T12:49:18Z'
platforms:
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
      framework:
      - cann_executor
---

# LongCat A3 SuperKernel 案例：非 KVP 路径的布局融合修复

## 条件与规则入口

本案例补充[SuperKernel 决策](../rules/superkernel_decode_ge_graph_fusion_scope.md)，限定 Atlas A3、LongCat-Flash、Decode GE 路径。优化说明固定 `0640521a817001f560fc30617acad41af585dfe1`，布局修复固定 `086bbb1c49c0ea1a53e690481dac292b26390257`；不是对当前软件全部版本的支持声明。

## 修复差异

PR332 作者说明，非 KVP 路径中 bmm 与 transpose 之间的额外 reshape 使 SuperKernel 融合范围断开。固定源码将该 reshape 下沉到 `kvp_size > 1` 分支；普通路径保留 bmm 后直接进入尾部 transpose，再恢复输出形状。作者称改后可以触发 TransposeBatchMatmul 融合。

结构变化可以静态核对，但本次没有编译图、profiling 或受控 benchmark，不能独立确认融合与收益。这个案例不说明所有 reshape 都不受支持；迁移时应核对具体算子、编译器与必需布局。

## 开关、历史与版本边界

历史文档通过 `enable_superkernel` 控制，并说明 CANN 8.5.0.alpha002 下部分标记算子尚未完全融合、该 LongCat 路径当时不支持 acl_graph。这些是固定实践的描述，不能推导其他后端永久不可用。

源码中用于对照的 KVP 分支属于历史实现；[KVP Concept](../../concepts/parallelism/kvp.md)已说明后续撤回与入口守卫。不能为了复现本修复而按旧配置启用 KVP。

## 验证边界

按规则卡的方法比较开关与编译产物，确认分支输出布局、精度、实际融合及 Decode 时延。回退恢复原始开关与对应编译配置后重测；本次没有运行模型、验证回退或增加 `verified`。
