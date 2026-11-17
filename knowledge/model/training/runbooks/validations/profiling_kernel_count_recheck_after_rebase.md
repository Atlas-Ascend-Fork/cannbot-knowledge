---
{
  "type": "Runbook",
  "title": "rebase 后核对 kernel 计数：先匹配设计代次与采样口径",
  "description": "保留 POST-rebase 的逐算子计数与复采方法；旧设计的 PRE 汇总不与当前终态强行配成 A/B，计数相同也不能证明精度或总性能不回归。",
  "tags": [
    "task.implementation",
    "topic.performance.analysis"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": []
}
---
# rebase 后核对 kernel 计数：先匹配设计代次与采样口径

## 适用场景

torchtitan-npu 编译/override 优化分支在 rebase 后的 profiling 复核；需固定 backend、卡数、采样步和统计脚本。

## 触发与观测

不同设计代次的 trace 都被标成“优化后”，直接比较容易出现假回归。

## 探针与操作

先对照代码、设计代次和采样配置，再逐项比较算子总数与命中次数；保留原始 trace 与统计脚本版本。

POST-rebase 的原始逐算子统计：

```text
=== POST-rebase fu (rb_trace_fu) === kernels total: 65899
  aclnnChunkCat_ChunkCat_ChunkCat                                  90      234.2 ms
  aclnnInplaceCopy_SliceAiCore_Slice                             2393      108.1 ms
  InplacePartialRotaryMul                                         636       84.3 ms
  aclnnInplaceCopy_TensorMoveAiCore_TensorMove                   2106       65.6 ms
  aclnnPowTensorScalar_TensorMoveAiCore_TensorMove                 44       19.3 ms
  aclnnCat_ConcatD_ConcatD                                        888        5.9 ms
  aclnnCat_SliceAiCore_Slice                                      168        1.5 ms
  aclnnStack_PackAiCore_Pack                                       42        0.5 ms
  aclnnStack_ConcatD_ConcatD                                        4        0.0 ms
  aclnnCat_ConcatD_ConcatDV2                                        1        0.0 ms
```

## 机制与判别

本次 POST-rebase 表给出特定设计的 kernel 图景。需要先找同代次的旧终态，不能把不同 TensorMove 设计的 PRE 表当作等价基线；单个 POST 表本身不能证明 rebase 前后全部计数相等。

## 验证信号

POST-rebase fu 表报告总 kernel 65899，其中 InplacePartialRotaryMul 636、InplaceCopy_Slice 2393、TensorMove 2106、Cat_ConcatD 888 等。原混合 PRE 汇总不再用于声称完全一致。

## 适用与失效边界

kernel 计数不代表 loss、梯度、显存或端到端时延都通过；这些需要各自同口径对照。不同 profile step、并行度和设计代次不能混比。
