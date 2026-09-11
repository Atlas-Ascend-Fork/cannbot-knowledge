---
type: Optimization
title: decode ge_graph 低时延融合：SuperKernel 调度融合的启用前提、融合范围坑与冷启动缓存
description: decode ge_graph 低时延融合：SuperKernel 调度融合的启用前提、融合范围坑与冷启动缓存。时延敏感的静态图 decode 想进一步压调度开销时，考虑 SuperKernel（按分核/分流范围标定 scope、优化任务调度等待与调度开销）。用它前先确认两件事：它只在特定路径生效，且融合范围有"相邻性"约束——中间夹一个不支持的算子就断融合。冷启动首编译慢再叠 cache_compile 降重启时延。
tags:
- task.optimization
- topic.attention
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/124
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/332
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# decode ge_graph 低时延融合：SuperKernel 调度融合的启用前提、融合范围坑与冷启动缓存

## 适用场景

时延敏感的静态图 decode 想进一步压调度开销时，考虑 [SuperKernel](../../../concepts/techniques/superkernel.md)（按分核/分流范围标定 scope、优化任务调度等待与调度开销）。用它前先确认两件事：**它只在特定路径生效**，且**融合范围有"相邻性"约束**——中间夹一个不支持的算子就断融合。冷启动首编译慢再叠 [cache_compile](torchair_cache_compile_persisted_graph.md) 降重启时延。

## 启用前提：仅 decode 启用 ge_graph 时生效

- SuperKernel **仅在 decode 启用 ge_graph 图模式时生效**（eager 无效）；**当前暂不支持 acl_graph**，静态图路径走 ge_graph。
- 版本天花板：某些 CANN 版本下 SuperKernel 标记范围内**部分算子尚不支持完全融合**（是该版本已知限制、需后续社区版本解决）；上此优化时按当前 CANN 版本预期收益，别默认已全融合。
- rollback：`enable_superkernel: False` 或退回 eager。

## 融合范围坑：可融合算子对间夹不支持算子会断融合

- **现象**：两个本应融合成一个 SuperKernel 的算子（如 [MLA](../../../concepts/modules/mla.md) 注意力输出路径的 value 上投影 bmm 与其后的输出 transpose，本可融成 **TransposeBatchMatmul**），若在它们之间保留一个 `reshape`，融合不会发生。
- **根因**：部分 tbe 算子（此处即中间 `reshape`）暂不支持在 GE 图模式下使能 SuperKernel；夹在中间即把 SuperKernel 的融合范围在此断开，使前后两个可融合算子无法相邻、不满足融合触发条件。
- **修法**：让欲融合的算子对（bmm ↔ transpose）在数据流上**直接相邻**，不在它们之间插 `reshape` 等不支持 SuperKernel 的中间算子。若某中间 `reshape` 只有部分路径（如 KVP AllToAll 需 NBSD 布局）才用得到，就把它从公共路径**移出、下沉到那条真正需要它的分支**；其余路径（如 `kvp_size==1`）保持 bmm 直接接 transpose 恢复融合的相邻条件。各分支特有布局差异在分支末尾补一步 `view` 对齐后再走统一尾部 transpose。

## 配合 cache_compile 降 decode 冷启动

同为 decode ge_graph 下的低时延手段：对静态图 decode 用 `tng.inference.cache_compile(..., ge_cache=True, dynamic=False, fullgraph=True)` 把编译产物落盘，服务重启直接加载缓存图而非重编译 → 削掉冷启动首次推理/首 token 时延。带 MTP 时 spec 模型需**独立缓存条目**（单独 cache_dir）。调用约定与缓存失效见 [torchair-cache-compile-persisted-graph](torchair_cache_compile_persisted_graph.md)。

## 参考实现及其约束

参考实现：LongCat-Flash 的 `runner_longcat_flash`（cache_compile + SuperKernel、A3、CANN 8.5.0.alpha002 融合限制）与 `LongcatFlashAttention.fused_infer_attention_score`（中间 reshape 下沉、尾部 permute→transpose 恢复 TransposeBatchMatmul 融合）。"reshape 属不支持 SuperKernel 的 tbe 算子""改后触发 TransposeBatchMatmul 融合"为作者陈述机制（无独立 profile），结构改动为 diff 事实；CANN 版本融合限制为该版本观测、迁新版复核；"SuperKernel 仅 decode ge_graph 生效、融合范围要求算子相邻"是可迁移约束。AscendC 自定义算子被 SuperKernel 融合的编译选项见 [superkernel-ascendc-relocatable-binary](superkernel_ascendc_relocatable_binary.md)。

## Evidence

- diff 事实 + doc 披露（@0640521a8170）：cache_compile ge_cache 降冷启动、MTP 独立缓存条目；SuperKernel 仅 decode ge_graph 生效、acl_graph 暂不支持、CANN 8.5.0.alpha002 部分算子未完全融合（仓自报）。溯源下探 [cann-recipes-infer-pr-124-feat-support-longcat-flash-inference](https://gitcode.com/cann/cann-recipes-infer/merge_requests/124)
- diff 事实 + 作者陈述机制（@086bbb1c49c0）：中间 `reshape` 从公共路径移出下沉 KVP 分支、尾部 permute→transpose，使 `kvp_size==1` 路径 bmm 与 transpose 相邻恢复融合条件；无 benchmark 数字。溯源下探 [cann-recipes-infer-pr-332-fix-modify-fused-infer-attention-score-for-longcat-to-fix-superkernel-sc](https://gitcode.com/cann/cann-recipes-infer/merge_requests/332)