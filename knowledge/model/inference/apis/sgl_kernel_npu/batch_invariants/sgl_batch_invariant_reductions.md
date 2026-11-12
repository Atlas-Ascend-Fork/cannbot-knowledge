---
type: API
title: SGLang Batch Invariant ReduceSum/ReduceMean：单维归约与批维边界
description: 给出reduce_sum_batch_invariant与reduce_mean_batch_invariant的单维参数、输出规则和逐位一致性前提，排除把沿batch归约误当批不变的用法。
tags:
- task.implementation
- topic.compute.reduction
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/reduce_sum.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/reduce_mean.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/reduce_sum.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/reduce_mean.py
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
- reduce_sum_batch_invariant
- reduce_mean_batch_invariant
---

# SGLang Batch Invariant ReduceSum/ReduceMean：单维归约与批维边界

## 公开接口

从 `sgl_kernel_npu.operators.batch_invariant` 导入 `reduce_sum_batch_invariant` 或 `reduce_mean_batch_invariant`，二者签名为 `(input, dim, keepdim=False, *, impl="auto")`。封装分别转发给 `torch.ops.batch_invariant_ops.npu_reduce_sum_batch_invariant` 和 `npu_reduce_mean_batch_invariant`。

输入为 NPU 上 FP16/BF16/FP32 张量。`dim` 只能是一个 int，可用负维索引，不支持维度列表；`keepdim=False` 移除归约维，`True` 将该维保留为 1。返回新分配、与 input 相同 dtype 的张量，不修改输入。

## 逐位一致性的比较对象

固定归约顺序不随独立行数改变，因此对 `[B,H]` 沿特征维 H 归约时，同一行单独计算与在大 batch 中计算的结果应逐位一致。若沿 B 归约，多行本来就参与同一个数学结果；改变 batch 同时改变输入集合，不属于这个保证。

验证可固定一行的值，将它放到不同 B 中，对 feature reduction 的对应输出用 `atol=0, rtol=0` 比较，并独立检查 mean 的除数。不能将 batch 轴减少后的结果与完整 batch 的结果强行要求一致，也不能由任意浮点基线误差推断批不变性失败。

## 来源与验证边界

本接口文档的支持表列出 `batch_invariant_ops` 在 arch22/arch35 可用，安装说明列出 910B/A3/950 的对应设备包。调用前须按[安装指南](/model/inference/guides/integration/sgl_kernel_npu/sgl_batch_invariant_installation.md)安装外部 CANN 算子包与 torch extension；`auto` 与 `batch_invariant_ops` 为同一入口，不提供缺依赖回退。逐位一致性为上游接口契约，本次未执行外部 kernel 的编译、真机、数值、图捕获或性能测试，未声称完成其 Device 实现分析。

## Evidence

- [docs/api/zh/operators/batch_invariant/reduce_sum.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/reduce_sum.md)（primary）
- [docs/api/zh/operators/batch_invariant/reduce_mean.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/reduce_mean.md)（supporting）
- [python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/reduce_sum.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/reduce_sum.py)（implementation）
- [python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/reduce_mean.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/reduce_mean.py)（implementation）
- [docs/api/zh/operators/batch_invariant/installation.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/installation.md)（constraint）
