---
type: API
title: SGLang Batch Invariant Linear Online Max/Sum：词表分片与打包掩码
description: 整理词表并行线性层的六项返回值、本地词表区间和uint8位打包target_mask，限定online统计的逐位比较方式。
tags:
- task.implementation
- topic.compute.reduction
- topic.parallelism
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/fused_linear_online_max_sum.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/fused_linear_online_max_sum.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/installation.md
  role: constraint
created_at: '2026-11-08T11:02:02Z'
updated_at: '2026-11-08T11:02:02Z'
platforms:
- a2
- a3
- '950'
aliases:
- fused_linear_online_max_sum_batch_invariant
---

# SGLang Batch Invariant Linear Online Max/Sum：词表分片与打包掩码

## 输入与词表区间

`fused_linear_online_max_sum_batch_invariant(input,weight,target,vocab_start_index,vocab_end_index,return_logits=False,*,impl="auto")` 在本 rank 计算词表并行线性层及交叉熵所需 online max/sum 统计。input 为 FP16/BF16 `[M,K]`，weight 为同 dtype 的本地 `[N,K]`，计算本地 logits `input @ weight.T`。target 是 `[M]` 的全局词表整数 ID；本地分片区间为 `[vocab_start_index,vocab_end_index)`。

权重布局固定为 `[N,K]`，不能因普通 matmul 习惯先变成 `[K,N]` 再交给本接口。

## 六项返回值

| 名称 | 形状 / dtype | 消费边界 |
| --- | --- | --- |
| `logits_max` | `[M]` FP32 | 与 online sum 成对使用 |
| `sum_exp_logits` | `[M]` FP32 | kernel 的 online 统计，不要求与朴素 exp/sum 逐位一致 |
| `predicted_logits` | `[M]` FP32 | 目标位置 logit |
| `target_mask` | `[(M+7)//8]` uint8 | 每字节对应 8 个 token，非 `[M]` bool 向量 |
| `masked_target` | `[M]`，与 target 同 dtype | 损失计算使用的本地下标 |
| `vocab_parallel_logits` | `[M,N]`，与 input 同 dtype | 仅 `return_logits=True` 时有效，否则可为未定义 tensor |

输入不会被修改。target_mask 的位打包约定意味着对完整 batch 的原始字节直接作 `full[:1] == single` 不等价于比较第一个 token；应按目标 token 位比较并屏蔽与被测 token 无关的位。

## 不变量与检验方法

上游保证每个 token 的统计不随 M 改变。验收时固定同一 token、权重、本地词表区间与 target，分别比较前几项逐 token 值，并解码 packed mask；可选 logits 只在两次调用均开启时比较。不要将 kernel 的 online 统计与朴素 `max/exp/sum` 逐位一致作为该接口承诺，也不要把本 rank 统计直接当作已完成跨 rank 全局交叉熵。

## 来源与验证边界

本接口文档的支持表列出 `batch_invariant_ops` 在 arch22/arch35 可用，安装说明列出 910B/A3/950 的对应设备包。调用前须按[安装指南](/model/inference/guides/integration/sgl_kernel_npu/sgl_batch_invariant_installation.md)安装外部 CANN 算子包与 torch extension；`auto` 与 `batch_invariant_ops` 为同一入口，不提供缺依赖回退。逐位一致性为上游接口契约，本次未执行外部 kernel 的编译、真机、数值、图捕获或性能测试，未声称完成其 Device 实现分析。

## Evidence

- [docs/api/zh/operators/batch_invariant/fused_linear_online_max_sum.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/fused_linear_online_max_sum.md)（primary）
- [python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/fused_linear_online_max_sum.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/fused_linear_online_max_sum.py)（implementation）
- [docs/api/zh/operators/batch_invariant/installation.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/installation.md)（constraint）
