---
type: Optimization
title: LongCat A3 Decode 权重预取：QBMM 与 MLA_Prolog 的相邻排布
description: 记录固定 LongCat-Flash/A3 实现中的预取空间取舍、enable_prefetch 开关和验证边界；不提供独立控变量收益，也不继承
  vLLM 的 token 门控或比例。
tags:
- task.optimization
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/0640521a817001f560fc30617acad41af585dfe1/docs/models/longcat-flash/longcat_flash_optimization.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/0640521a817001f560fc30617acad41af585dfe1/models/longcat-flash/models/modeling_longcat_flash.py
  role: implementation
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/0640521a817001f560fc30617acad41af585dfe1/models/longcat-flash/README.md
  role: constraint
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/longcat-flash/models/modeling_longcat_flash.py
  role: supporting
created_at: '2026-10-20T11:23:20Z'
updated_at: '2026-10-22T01:37:00Z'
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
      execution_mode:
      - ge_graph
      framework:
      - cann_executor
      model_features:
        all_of:
        - mla
---
# LongCat A3 Decode 权重预取：QBMM 与 MLA_Prolog 的相邻排布

## 条件与规则入口

本案例补充[权重预取决策](../rules/decode_weight_prefetch_ordering.md)的 LongCat-Flash 实施证据，范围限定 Atlas A3、Decode、GE 图模式和固定模型提交 `0640521a817001f560fc30617acad41af585dfe1`。通用判断维护在规则卡，这里只记录实现差异。

## 实施差异

官方文档说明 MLA_Prolog 含多个 matmul、搬运压力较大，因此提前预取其前置 QBMM 的权重，为 MLA_Prolog 留出更大的预取空间。模型的 `LongcatFlashMLP` 根据权重规模、量化分支和 dense TP 数计算预取范围；多流前向还包含 attention 及后续层权重的预取调用，使用 `o_proj`、`dsq`、`down_proj` 等张量表达依赖。

这些排布和范围是固定实现的参数，不直接复用为其他模型的缓存预算。本案例没有 vLLM 的“96 token”或“0.8 比例”条件，不能从另一个实现拼接参数。

## 开关与回退

文档声明通过 `enable_prefetch` 开关使能。迁移或回退时保存原始配置，关闭该开关并核对图编译、依赖和输出。本次未执行模型，也没有验证回退后的性能。

## 观测与验证边界

来源没有“只改变预取”得到的 before/after。整模型 benchmark 还包含 MTP2、perfect EPLB 等配置，不能归因为预取。

复现时固定工作负载和其他开关，检查发起/消费的时间线、缓存与带宽竞争、Decode 单步时延或 TPOT，以及输出精度；记录重复次数与波动。这些是后续验证方法，不是已完成的实验。没有确认 Prefill 或其他平台的同等收益，不增加 `verified`。

## Evidence

- [LongCat 优化文档](https://gitcode.com/cann/cann-recipes-infer/blob/0640521a817001f560fc30617acad41af585dfe1/docs/models/longcat-flash/longcat_flash_optimization.md)：核对 Atlas A3 范围、“权重预取”章节及整模型 benchmark 限制。
- [LongCat 模型源码](https://gitcode.com/cann/cann-recipes-infer/blob/0640521a817001f560fc30617acad41af585dfe1/models/longcat-flash/models/modeling_longcat_flash.py)：静态核对 `LongcatFlashMLP`（约 L169–L245）及多流前向（约 L1153–L1238）中的权重、依赖与范围计算。
- [LongCat README](https://gitcode.com/cann/cann-recipes-infer/blob/0640521a817001f560fc30617acad41af585dfe1/models/longcat-flash/README.md)：核对该固定实践的 Atlas A3 产品声明；没有独立真机复测。

## 历史实现的依赖示意

LongCat-Flash 模型对访存 bound 的算子如 **QuantBatchMatmul (QBMM)、MLAProlog、Matmul** 等算子提前预取了对应的权重。其中 **MLAProlog 算子包含了多个矩阵乘计算，搬运 bound 较大，因此提前预取了前置的 QBMM 的权重**，为 MLAProlog 提供了更大的预取空间，获取较大的性能收益。具体的预取大小及预取位置，可在 `models/modeling_longcat_flash.py` 中搜索 `npu_prefetch` 接口查看。

`modeling_longcat_flash.py` 中这些预取大小为硬编码的承重参数：router `classifier.weight`固定源码中的字节范围、下一段 attention 的 `q_a_proj`固定源码中的字节范围、`q_b_proj`固定源码中的字节范围、`kv_a_proj_with_mqa`固定源码中的字节范围。设计上以**前一算子的输出作为预取触发依赖**（`npu_prefetch` 的 dependency tensor）——router 预取依赖 `o_proj`、本段 attention 权重预取依赖 `dsq`、跨层预取**下一层** attention（`next_layer.self_attn[0]`）权重时则以 `down_proj` 为依赖锚点，从而构成跨层流水的预取链。

![LongCat-Flash 的预取位置](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/longcat-flash/figures/prefetch.png)
*来源：[`docs/models/longcat-flash/figures/prefetch.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/longcat-flash/figures/prefetch.png)（cann-recipes-infer @ 2f82d10）*

这些来自历史 2f82d10 实现，不代替本卡主版本的参数；具体预取字节数按固定代码与权重、量化分支计算。
