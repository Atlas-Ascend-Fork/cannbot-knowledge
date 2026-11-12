---
type: API
title: SGLang Batch Invariant MM/Matmul：矩阵维、广播与转置视图
description: 区分mm_batch_invariant的二维矩阵乘与matmul_batch_invariant的batch广播，明确固定K归约顺序下的逐行一致性及外部实现边界。
tags:
- task.implementation
- topic.compute.composite
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/matmul.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/mm.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/matmul.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/mm.py
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
- mm_batch_invariant
- matmul_batch_invariant
---

# SGLang Batch Invariant MM/Matmul：矩阵维、广播与转置视图

## 两个接口不可混淆

| 接口 | 计算与输入 |
| --- | --- |
| `mm_batch_invariant(input, mat2, *, impl="auto")` | 二维 `[N,K] @ [K,M] -> [N,M]` |
| `matmul_batch_invariant(input, other, *, impl="auto")` | `[...,N,K] @ [...,K,M]`，前置 batch 维按广播规则对齐 |

二者从 `sgl_kernel_npu.operators.batch_invariant` 导入，接受 NPU 上 FP16/BF16/FP32，右操作数与左操作数同 dtype、同设备。mm 文档要求 N、K 为正；右操作数允许转置后的非连续视图，不能为了“对齐”未经语义确认交换 K/M。

公开函数直接转发参数，不自行验证全部 shape。结果为新张量，不改输入；外部库缺失时第一次调用报错，不自动选择普通 torch.mm。

## 不变量来自 K 维归约

数学上仍为普通矩阵乘，区别在上游声明 K 维归约顺序不随独立行数 N 或 batch 大小变化。验证时固定同一行、同一权重与 K/M，在单行计算与完整 batch 结果中比较对应行；matmul 还应分别覆盖广播前置维、非连续右矩阵视图和实际 batch 切片。

这不保证更换精度、权重布局、K 或设备后仍得到完全相同位模式，也不要求不同 matmul 库都采用同样的舍入。

## 来源与验证边界

本接口文档的支持表列出 `batch_invariant_ops` 在 arch22/arch35 可用，安装说明列出 910B/A3/950 的对应设备包。调用前须按[安装指南](/model/inference/guides/integration/sgl_kernel_npu/sgl_batch_invariant_installation.md)安装外部 CANN 算子包与 torch extension；`auto` 与 `batch_invariant_ops` 为同一入口，不提供缺依赖回退。逐位一致性为上游接口契约，本次未执行外部 kernel 的编译、真机、数值、图捕获或性能测试，未声称完成其 Device 实现分析。

## Evidence

- [docs/api/zh/operators/batch_invariant/matmul.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/matmul.md)（primary）
- [docs/api/zh/operators/batch_invariant/mm.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/mm.md)（supporting）
- [python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/matmul.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/matmul.py)（implementation）
- [python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/mm.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/mm.py)（implementation）
- [docs/api/zh/operators/batch_invariant/installation.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/installation.md)（constraint）
