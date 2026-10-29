---
type: Optimization
title: SuperKernel 决策：按依赖、流与编译结果确定融合范围
description: 集中已有 A3 MoE Decode GE 实践的 SuperKernel 决策：按数据依赖、流和资源边界选择范围并检查实际融合；LongCat 相邻算子修复与 Qwen/SGLang 门控分别进入案例。
tags:
- task.optimization
- topic.attention
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/0640521a817001f560fc30617acad41af585dfe1/docs/models/longcat-flash/longcat_flash_optimization.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/50e41b5b8220284f6721223e9f0d3471cd0b0944/models/qwen3-moe-sglang/README.md
  role: constraint
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/50e41b5b8220284f6721223e9f0d3471cd0b0944/models/qwen3-moe-sglang/patches/0009-feat-support-superkernel.diff
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/332
  role: evidence
created_at: '2026-07-06T00:00:00Z'
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
      execution_mode:
      - ge_graph
---

# SuperKernel 决策：按依赖、流与编译结果确定融合范围

## 适用场景与问题信号

本卡是 SuperKernel 优化决策的统一入口，范围限已有 Atlas A3、MoE、Decode、GE 图模式证据。在合法图路径中仍有任务调度等待、碎片化调度或预期融合未发生时，结合图和时间线评估[SuperKernel](../../concepts/techniques/superkernel.md)。这不是所有平台、后端或算子的可用性声明。

## 范围选择与机制

按数据依赖、流切换和分核范围选择候选段，核对编译器与算子支持，再查看真实成图/融合结果。写了 scope 标记不代表段内全部融合，也不证明端到端收益。

候选段可以按 attention/MoE 等功能划分；是否跨段或包整层要结合实现和编译结果。不能从某个 patch 的分段调用点得出“只能按功能段”的通用限制，也不能无条件把整层作为最优范围。

若预期的一对算子没有融合，检查中间布局变换、支持情况和分支路径。LongCat 的历史 reshape 修复说明一个具体断点，不证明所有 reshape 都会阻断融合，也不允许只为相邻而删除必要的数据变换。

## 实施与证据入口

- [LongCat A3 融合修复案例](../cases/longcat_a3_superkernel_layout_fusion.md)：记录固定非 KVP 路径的 bmm/transpose 相邻性修复与版本边界。
- [Qwen3-MoE A3/SGLang 门控案例](../cases/qwen3_moe_a3_superkernel_scopes.md)：记录功能段 scope、整层入口和关闭分支的实际含义。

编译缓存解决重复编译与冷启动问题，复用[缓存规则](torchair_cache_compile_persisted_graph.md)，不在本卡维护第二套调用约定或把冷启动收益归因于 SuperKernel。

## 收益、风险与验证

来源提供优化目标与整模型数据，没有隔离 SuperKernel 的独立 before/after。作用范围过宽、跨流依赖不当、版本不支持或标记静默失效都可能使预期落空；关闭分支返回空上下文只表示不发起该 scope，不代表 Python 零开销。

验证时固定模型、编译器与运行库版本、负载、并行和其他开关，检查编译图/融合产物、调度与通信时间线、Decode 时延或 TPOT，以及输出。记录 warmup、重复次数与波动；本次未运行这些实验，没有新增 `verified`。

## 回退与适用边界

保存原配置，按案例的真实开关关闭 SuperKernel 并重核编译产物、缓存和输出，不把直接切 eager 等同于只关闭一个优化。LongCat 文档的 acl_graph 不支持、CANN 8.5.0.alpha002 部分算子未完全融合只描述固定版本，不能当作当前所有实现的永久限制。
