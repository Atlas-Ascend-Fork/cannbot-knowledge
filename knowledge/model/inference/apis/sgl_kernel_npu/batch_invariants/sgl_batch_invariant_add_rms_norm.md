---
type: API
title: SGLang Batch Invariant AddRmsNorm：三返回值与残差边界
description: 定义add_rms_norm_batch_invariant的残差相加、末维RMS归一化、rstd与residual_out形状及输入不修改契约。
tags:
- task.implementation
- topic.compute.normalization
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/add_rms_norm.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/add_rms_norm.py
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
- add_rms_norm_batch_invariant
---

# SGLang Batch Invariant AddRmsNorm：三返回值与残差边界

## 接口与计算

`add_rms_norm_batch_invariant(x, residual, weight, eps, *, impl="auto")` 先令 `S=x+residual`，再逐行计算 `rstd=1/sqrt(mean(S*S,dim=-1)+eps)` 与 `output=S*rstd*weight`。公开入口位于 `sgl_kernel_npu.operators.batch_invariant`，转发到 `torch.ops.batch_invariant_ops.npu_add_rms_norm_batch_invariant`。

x 与 residual 均为 NPU 上 `[B,H]`，weight 为 `[H]`；三者使用相同 FP16/BF16 dtype，x 与 residual 同设备。eps 为调用方显式给出的 float，例如 `1e-6`。

## 返回值与别名边界

返回 `(output,rstd,residual_out)`：output 为 `[B,H]` 且与 x 同 dtype；rstd 为浮点 `[B,1]`；residual_out 为 `[B,H]` 的残差和 S。来源文档只将 rstd 说明为浮点，不据此自行固定为 BF16 或 FP32。三个结果均为新分配张量，输入不会被修改；不能套用另一种 in-place fused AddRmsNorm 的别名约定。

上游声明逐行归约顺序不随 B 变化，逐位一致性同时覆盖三个返回值。验收应在不同 B 下固定同一输入行、残差行和 weight/eps，分别比较对应行的归一化输出、rstd 和残差和，并额外确认原 x/residual 未改变。

## 来源与验证边界

本接口文档的支持表列出 `batch_invariant_ops` 在 arch22/arch35 可用，安装说明列出 910B/A3/950 的对应设备包。调用前须按[安装指南](/model/inference/guides/integration/sgl_kernel_npu/sgl_batch_invariant_installation.md)安装外部 CANN 算子包与 torch extension；`auto` 与 `batch_invariant_ops` 为同一入口，不提供缺依赖回退。逐位一致性为上游接口契约，本次未执行外部 kernel 的编译、真机、数值、图捕获或性能测试，未声称完成其 Device 实现分析。

## Evidence

- [docs/api/zh/operators/batch_invariant/add_rms_norm.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/add_rms_norm.md)（primary）
- [python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/add_rms_norm.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/batch_invariant/add_rms_norm.py)（implementation）
- [docs/api/zh/operators/batch_invariant/installation.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/batch_invariant/installation.md)（constraint）
