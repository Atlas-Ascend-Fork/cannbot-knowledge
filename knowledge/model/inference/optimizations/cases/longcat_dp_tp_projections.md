---
type: Optimization
title: LongCat A3 局部 TP 案例：o_proj 与 dense MLP 的 DP/TP 边界
description: 记录固定 LongCat A3 Decode 在 Attention DP 下的 o_proj K 轴切分、dense MLP 切分和布局转换；沿用局部 TP 规则，不将模型通信序列泛化为统一实现。
tags:
- task.optimization
- topic.attention
- topic.parallelism
status: stable
platforms:
- a3
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/0640521a817001f560fc30617acad41af585dfe1/docs/models/longcat-flash/longcat_flash_optimization.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/0640521a817001f560fc30617acad41af585dfe1/models/longcat-flash/models/modeling_longcat_flash.py
  role: implementation
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/0640521a817001f560fc30617acad41af585dfe1/models/longcat-flash/README.md
  role: constraint
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
      objective:
      - memory
      - latency
      - tpot
      model_features:
        all_of:
        - mla
        - moe
      parallelism:
        all_of:
        - dp
      framework:
      - cann_executor
created_at: '2026-10-20T11:49:50Z'
updated_at: '2026-10-20T12:49:18Z'
---

# LongCat A3 局部 TP 案例：o_proj 与 dense MLP 的 DP/TP 边界

## 条件与规则入口

本案例补充[局部 TP 决策](../rules/local_tp_memory_heavy_projections.md)的 LongCat-Flash 实施细节，来源固定在 `0640521a817001f560fc30617acad41af585dfe1`，平台限定 Atlas A3，主结论针对 Decode 的 Attention-DP 路径。优化选择与复现方法由规则卡维护；本卡只记录该模型的切分和通信。

## o_proj：输入维分片与布局恢复

源码在 `o_proj_tp_size > 1` 且 `attn_tp_size == 1` 时，把 Attention 输出按 head/输入特征重排，执行 `all_to_all_single`，使每个 rank 获得自己负责的输入特征段。o_proj 沿输入 K 轴分片，本地线性投影后通过 `reduce_scatter_tensor` 合并部分和并恢复 batch 分布。

输入维与分片大小必须吻合。这个守卫描述本案例的 DP 路径，不是所有 LongCat 版本或其他模型对 Attention TP 的总限制；也不能把历史 KVP 的 AllReduce 分支拼接到这条 AllToAll/ReduceScatter 路径。

## dense MLP：列切与行切配合

`gate_proj` 与 `up_proj` 合为列并行 `gate_up_proj`，`down_proj` 沿输入 K 轴做行并行。Attention DP 与 dense TP 的分布不同，MLP 前 AllGather、后 ReduceScatter，完成布局转换。这里的通信依赖 `dense_tp_group`，不能仅调整权重分片而省掉边界通信。

## 观测、收益与失效边界

文档以减少单 rank 权重占用和读取为优化目标，但没有只改变这项 TP 配置的独立 before/after。新增通信是否带来净收益需要实际测量；本次没有运行模型、复测性能或验证新配置。

跨模型复用时，检查 o_proj 输入布局与整除、MLP 分片方向、通信组和恢复后的 batch/特征维。若这些条件不吻合，应回到规则卡重新选型，不照搬本案例的通信序列。

## Evidence

- [优化文档](https://gitcode.com/cann/cann-recipes-infer/blob/0640521a817001f560fc30617acad41af585dfe1/docs/models/longcat-flash/longcat_flash_optimization.md)：o_proj 与 MLP TP 的设计说明。
- [固定模型源码](https://gitcode.com/cann/cann-recipes-infer/blob/0640521a817001f560fc30617acad41af585dfe1/models/longcat-flash/models/modeling_longcat_flash.py)：`LongcatFlashMLP`、`o_proj_forward` 与通信组构造；静态核对 AllGather、AllToAll 和 ReduceScatter 的位置。
- [固定 README](https://gitcode.com/cann/cann-recipes-infer/blob/0640521a817001f560fc30617acad41af585dfe1/models/longcat-flash/README.md)：Atlas A3 产品范围；没有独立真机复测。
