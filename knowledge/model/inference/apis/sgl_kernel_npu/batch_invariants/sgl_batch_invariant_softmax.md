---
type: API
title: SGLang Batch Invariant Softmax/LogSoftmax：末维限定与逐行一致性
description: 记录softmax_batch_invariant和log_softmax_batch_invariant只支持最后一维的约束、输入dtype及跨batch逐行对比方法。
tags:
- task.implementation
- topic.compute.reduction
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/softmax.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/log_softmax.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/softmax.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/log_softmax.py
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
- softmax_batch_invariant
- log_softmax_batch_invariant
---

# SGLang Batch Invariant Softmax/LogSoftmax：末维限定与逐行一致性

## 接口与 shape

`softmax_batch_invariant(input, dim, *, impl="auto")` 与 `log_softmax_batch_invariant(input, dim, *, impl="auto")` 位于 `sgl_kernel_npu.operators.batch_invariant`。输入为 NPU 上 `[...,V]` 的 FP16/BF16/FP32，返回同 shape、同 dtype 的新张量，不修改 input。

尽管接口暴露 `dim`，当前外部 kernel 只支持最后一维：应传 `-1` 或 `input.dim()-1`。传入中间维不会自动转置或退化为另一实现，而是触发 ACLNN 参数错误。

## 语义与检验

两者分别产生末维的概率和对数概率。上游声明归约顺序与行数无关，因此固定 logits 行在单行调用和大 batch 中对应行的结果逐位相同。检查时应保持该行数值、词表末维和其他参数相同，再按对应输出行作零容差比较；改变词表维内容不属于同一输入。

批不变性比较不等于要求 Softmax 与 LogSoftmax 经过额外 exp/log 后逐位相等，额外浮点运算本身会引入不同舍入路径。普通数值正确性与跨 batch 的确定性应分开验收。

## 来源与验证边界

本接口文档的支持表列出 `batch_invariant_ops` 在 arch22/arch35 可用，安装说明列出 910B/A3/950 的对应设备包。调用前须按[安装指南](/model/inference/guides/integration/sgl_kernel_npu/sgl_batch_invariant_installation.md)安装外部 CANN 算子包与 torch extension；`auto` 与 `batch_invariant_ops` 为同一入口，不提供缺依赖回退。逐位一致性为上游接口契约，本次未执行外部 kernel 的编译、真机、数值、图捕获或性能测试，未声称完成其 Device 实现分析。

## Evidence

- [docs/api/zh/operators/batch_invariant/softmax.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/softmax.md)（primary）
- [docs/api/zh/operators/batch_invariant/log_softmax.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/log_softmax.md)（supporting）
- [python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/softmax.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/softmax.py)（implementation）
- [python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/log_softmax.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/log_softmax.py)（implementation）
- [docs/api/zh/operators/batch_invariant/installation.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/installation.md)（constraint）
