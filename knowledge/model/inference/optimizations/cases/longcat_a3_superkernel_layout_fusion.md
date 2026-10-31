---
type: Optimization
title: LongCat A3 SuperKernel 案例：非 KVP 路径的布局融合修复
description: 当前 LongCat GE SuperKernel 的分段、后端拒绝条件与布局审查；撤下旧 KVP 分支和跨版本修复示例。
tags:
- task.optimization
- topic.graph_execution
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/longcat_flash_optimization.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py
  role: implementation
created_at: '2026-10-20T12:18:12Z'
updated_at: '2026-10-29T13:44:43Z'
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

# LongCat A3 SuperKernel 的布局与范围

## 当前状态

model_config.custom_params.enable_superkernel 只支持 ge_graph；eager 与 npugraph_ex 会被模型校验拒绝。当前多流前向按 part1、part2_moe、part2_main 划分 scope，与流和控核边界对应。

## 布局约束

当前 Attention 的投影链保持 bmm/transpose 等真实语义，o_proj 根据 TP/Attention-SP 做必要的 AllToAll、ReduceScatter 或 AllReduce。旧 KVP 分支已不存在，不能继续拿旧 KVP/non-KVP 分支和多个提交对比解释当前布局。

reshape、transpose 和分片均需按实际数据布局保留。减少无用布局变换可能扩大融合机会，但 scope 标记不保证内部所有节点均融合。最新 README 仍提示部分标记算子可能不完全融合。

## 验证

遵循[SuperKernel 规则](../rules/superkernel_decode_ge_graph_fusion_scope.md)，固定输入、后端和其他优化，比较图产物、实际融合、输出与 TPOT。本次未执行编译或性能验证。


## Evidence

- [longcat_flash_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/longcat_flash_optimization.md)（primary）
- [modeling_longcat_flash.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py)（implementation）
