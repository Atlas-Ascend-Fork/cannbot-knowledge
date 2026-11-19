---
type: Guide
title: 原生Padding的NPU限制：模式、dtype与高维开销
description: 区分constant/非constant及具体Pad类的支持表，保留文档差异、高维性能提示与ZeroPad2d CPU回退；含 Reflection/Replication/Constant Pad 的 Eager 包装层：生成命令、FP4/高维边界与 acl_op 回退内部；含 reflection/replication_pad3d 生成层 wrapper 实际行为：无 DO_COMPATIBILITY 的直发合同与 4D/5D 尺寸 helper。并含 constant_pad_nd 的FP4/FP8测试合同：主线FP8(e4m3fn/e5m2) pad支持面、950门控与主线与发布两版本测试内容差。
tags:
- task.optimization
- topic.precision
- topic.data_pipeline
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn-functional.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ConstantPadNdKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ConstantPadNdKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/PadKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ReflectionPad1dKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ReflectionPad1dBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ReflectionPad2dKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ReflectionPad2dBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ReplicationPad1dKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ReplicationPad1dBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ReplicationPad2dKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ReplicationPad2dBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ConstantPadNdKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ConstantPadNdKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/PadKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ReflectionPad1dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ReflectionPad1dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ReflectionPad2dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ReflectionPad2dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ReplicationPad1dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ReplicationPad1dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ReplicationPad2dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ReplicationPad2dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/struct_codegen.py
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/model.py
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/templates/StructKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/struct/struct_codegen.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/struct/model.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/struct/templates/StructKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_constant_pad_nd.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_constant_pad_nd.py
  role: example
created_at: '2026-11-09T10:11:05Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 原生Padding的NPU限制：模式、dtype与高维开销

## 固定版本与用途

依据TorchNPU固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 中PyTorch2.7.1、2.9至2.14的完整条目，产品为A2/A3训练系列与950DT，不扩大950PR或发布基线。它们是同一提交中的分版本文档，差异不直接证明发行历史或实际包回归；具体版本按下文区分。未执行上游、设备、精度或性能实验，文档所称“已验证”属于上游口径。

Padding用于卷积/视觉接线时，应保留边界取值与后续有效长度语义，不能只为切换到可用dtype就修改模式或填充值。以下七版本相应限制一致，仍需按具体入口消费。

## Functional入口

F.pad在constant模式列BF16、FP16/32/64、UINT8、INT8/16/32/64、BOOL；非constant仅列FP16/32/64。x达到六维或以上时可能性能下降，这是来源的条件提示，不是给出的固定减速比例或所有shape的实测结论。

## 具体Pad类不能套用同一并集

| 入口 | input/shape条目 |
| --- | --- |
| ReflectionPad1d/2d | FP16/FP32 |
| ReplicationPad1d/2d | FP16/FP32、complex64/128 |
| ZeroPad1d | BF16、FP16/32/64、complex64/128，仅2..3维 |
| ZeroPad3d | 同类dtype集合，仅5..6维 |
| ConstantPad1d | 条目仅列INT8/BOOL，达到六维或以上可能降速 |
| ConstantPad2d | BF16、FP16/32/64、UINT8、INT8/16/32/64、BOOL、complex64/128；达到六维或以上可能降速 |
| ConstantPad3d | FP16/FP32、UINT8、INT8/16/32/64、BOOL、complex64/128；达到六维或以上可能降速 |

ConstantPad1d的窄dtype表、ConstantPad2d/3d与F.pad的complex差异明显，保留为各自清单事实及待核对项；不能据功能相似合并为已确认支持矩阵，也不能为适配这张窄表把浮点模型激活强制转整数。

ReflectionPad3d、ReplicationPad3d、CircularPad1d/2d/3d只列产品，未给另一份dtype细表；这不是所有rank或模式都已验证。ZeroPad2d明确标注可能CPU回退，不能因其他ZeroPad没有该句就推断完全无Host活动。

## 开销与验证边界

区分实际数值计算、Host控制、CPU回退及H2D/D2H；用相同padding规则比较输出和梯度，再比较维度/布局、分配、数据转移与稳态时间。禁止fallback不会自动生成缺失的NPU实现，调用成功也不证明没有隐藏搬运。

- [CPU回退的范围](../../inference/guides/optimization/torch_npu/torch_npu_cpu_fallback_and_compatible_impl.md)
- [视觉重采样](torch_npu_native_vision_resampling.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn.md)（primary）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn-functional.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn-functional.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn-functional.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn-functional.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn-functional.md)（constraint）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn-functional.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn-functional.md)（primary）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-nn.md)（constraint）

## Reflection/Replication/Constant Pad 的 Eager 包装层

本节把上文docs表的pad族核对到两版OpPlugin固定树的Eager包装层。yaml登记（主线与发布两版本逐字相同）：`reflection_pad1d/2d`与`replication_pad1d/2d`的前向+`.out`+`_backward`+`.grad_input`全家`acl_op: [v2.1, newest]`+`op_api: [v2.1, newest]`，生成层exec `aclnnReflectionPad1d/2d`、`aclnnReplicationPad1d/2d`（含Backward），前向out尺寸经`*_npu_out_size(self, padding)`、反向grad_input尺寸=self dtype=self（主线4122–4176、4294–4348；发布4009–4063、4176–4230）。**`reflection_pad3d`与`replication_pad3d`的前后向全家只有`op_api: [v2.1, newest]`、无acl_op条目**（主线4182–4207、4354–4378；发布4069–4095、4236–4261），且来源 `op_plugin/ops/` 主线与发布两版本均无对应aclops实现文件（find零命中）——这两族的acl_op回退在源集内不存在，DO_COMPATIBILITY语义不外推。

| 入口 | 实际门槛与动作 | 关键边界 |
| --- | --- | --- |
| constant_pad_nd（手写opapi） | `DO_COMPATIBILITY(aclnnConstantPadNd, acl_op::…)`；pad长度为偶、不超过2*rank；输出维度逐项非负；**FP4特例**：`ACL_FLOAT4_E2M1/E1M2`输入要求pad[0]/pad[1]为偶数且末维pad_add减半；输入或输出任一numel==0时`op_api::fill_(result, value)`快捷返回（不下发命令）；否则EXEC aclnnConstantPadNd | FP4打包粒度只按字面记录；快捷路径fill_与pad命令是两种设备动作 |
| constant_pad_nd（acl_op回退） | 正/负pad符号分类（0全零/1正/2负/3混合）；正路径：value经`at::empty({1})+acl_op::fill_`变成1元素设备输入后走ACE命令`PadV3`（mode constant、paddings_contiguous true），**输入rank>8时追加`_exclude_engines="AiCore"`**；纯负路径：`npu_indexing`逐维切片（负值置0后按维调begin/end）；混合路径：先PadV3再对结果切片；"输出某维为0且存在正pad"TORCH_CHECK硬拒 | PadV3的pads向量由正值截断+逆序对展开构成；切片路径不经过pad命令 |
| npu_pad（acl_op自定义入口） | `op_infer::pad_npu_output_size`推尺寸后ACE命令`Pad`：paddings补零到2*rank后作为**设备输入**（非attr） | 这是仓内其他算子可复用的自定义pad入口，非aten constant_pad_nd的登记路径 |
| reflection_pad1d(±backward)（acl_op） | 纯委托2d：`unsqueeze(0)`+paddings{p0,p1,0,0}+`squeeze_`；padding长度≥2检查 | 1D回退复用2D命令，多出的padding元素被丢弃 |
| reflection_pad2d(±backward)（acl_op） | 前向：尺寸helper要求rank≥3、padding≥4，out_nocheck恒要求padding==4；ACE命令`MirrorPad`（mode REFLECT）——paddings列表resize(2*rank,0)后**按逆序对**组成vector_int作为Int设备输入；反向：**全0 padding快捷`grad_input.copy_(grad_output)`**，否则ACE命令`PadV3Grad`（mode reflect、paddings_contiguous true）；rank3在命令前后unsqueeze/squeeze（反向对grad_input原地unsqueeze_） | CheckOut按self校验、check_match不符走format_contiguous/fresh_view；逆序对展开与前向torch语义的对应不在此断言 |
| replication_pad1d(±backward)（acl_op） | 同型委托2d（unsqueeze+{p0,p1,0,0}+squeeze） | 与reflection对称；只取前两项padding |
| replication_pad2d(±backward)（acl_op） | 前向：ACE命令`PadV3`（mode edge）**三输入**——self、Int pads（逆序对展开）、value=0的1元素常量（以self dtype构造）；反向：全0快捷copy_，否则`PadV3Grad`（mode edge） | 三输入形态与MirrorPad两输入不同；0常量输入对edge模式是占位 |
| reflection_pad3d/replication_pad3d全家 | 仅生成层登记（exec aclnnReflectionPad3d/ReplicationPad3d±Backward），源集内无手写文件、无aclops文件 | 本层只到登记面；实际生成wrapper行为与SDK约束未核对，留未核对 |

图模式侧的constant_pad_nd/reflection_pad2d/replication_pad1d行为见[GE padding/采样卡](../../inference/guides/optimization/torchair/torchair_ge_padding_sampling_lowering.md)（torchair转换器，与本文Eager层不互推）。

### Pad 包装层补充证据

- [ConstantPadNdKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ConstantPadNdKernelNpuOpApi.cpp)（primary）：21–95；完整函数体（FP4分支、空tensor快捷）。
- [ConstantPadNdKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ConstantPadNdKernelNpu.cpp)（primary）：21–212；check_negetive/check_params/do_indexing/PadV3全路径。
- [PadKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/PadKernelNpu.cpp)（primary）：21–34；npu_pad完整函数体。
- [ReflectionPad1d/1dBackward/2d/2dBackward d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ReflectionPad2dKernelNpu.cpp)（primary）：1d 20–40、1dBackward 20–46、2d 21–97、2dBackward 21–102；均为完整函数体。
- [ReplicationPad1d/1dBackward/2d/2dBackward d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ReplicationPad2dKernelNpu.cpp)（primary）：1d 20–40、1dBackward 20–46、2d 21–75、2dBackward 21–102；均为完整函数体。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（primary）：4122–4207、4294–4378；reflection/replication全家条目；1800–1804为constant_pad_nd（该文件已列于frontmatter来源）。
- 发布版本对应文件（ConstantPadNd opapi 59行、aclops 197行、Pad 35行、四个pad文件42/45/95/100/42/45/82/100行，行数见manifest source_meta）：逐文件与主线**去空白字符流相同**（仅版权头换行/排版差异）；yaml发布4009–4095、4176–4261、1741–1745与主线逐字相同。
- 负向证据：主线与发布两版本 `op_plugin/ops/`全树find `*Pad3*`/`*ReflectionPad3*`/`*ReplicationPad3*` 零命中——3D族无acl_op实现文件；`PadKernelNpu.cpp`的调用方未逐个展开（npu_pad消费者不在本节范围）。

## reflection/replication_pad3d 生成层 wrapper 的实际行为

上文 Pad 包装层一节把 3D 两族记为“仅生成层登记（exec aclnn*），源集内无手写文件、无 aclops 文件”；本节按主线与发布两版本 的 gen_opapi 生成器模板把 wrapper 实际行为读到模板层：`torchnpugen/struct/struct_codegen.py`（ACLNN_FUNCTIONS_DEFINITION 模板与 compute_op_api_definition）、`torchnpugen/struct/model.py`（ResInfo 解析与 cmd_args 展开）、`torchnpugen/struct/templates/StructKernelNpuOpApi.cpp`（文件骨架）。模板骨架文件主线与发布两版本 逐字节相同；struct_codegen.py/model.py 主线为超集（多 integral_identity_guard/cpu_scalar_* 特性槽位），3D 两族条目未配置这些键、生成体不受影响——本节按模板静态推导，生成代码不随仓提交、未运行 gencode（与[激活精度卡](torch_npu_native_activation_precision.md)_add_relu 同口径）。yaml 主线与发布两版本 逐字相同：functional 与 backward 均为 `structured_inherit`（分别继承 .out 与 .grad_input 的 gen_opapi 配置，生成独立函数体而非委托）；.out 声明 size=`*_pad3d_npu_out_size(self, padding)`、dtype=self；.grad_input 声明 size=self、dtype=self；exec 分别 aclnnReflectionPad3d(Backward)/aclnnReplicationPad3d(Backward)（主线4182–4207、4354–4378；发布4069–4095、4236–4261）。

| 入口 | 生成 wrapper 实际行为（模板推导） | 边界 |
| --- | --- | --- |
| reflection/replication_pad3d（functional） | 按继承的 out 配置生成：`at::Tensor out = apply_tensor_without_format(reflection_pad3d_npu_out_size(self, padding), self.options().dtype(self.scalar_type()))` 后单次 `EXEC_NPU_CMD(aclnnReflectionPad3d, self, padding, out)`，return out（replication 同构换命令与 helper） | **无 DO_COMPATIBILITY**——yaml 无 acl_op 登记时模板不生成符号探测/回退行，与上文 1d/2d 族（登记 acl_op、缺符号走生成层声明的 aclops 回退）机制不同；aclnn 符号缺失时的行为在加载/链接层，本层不可见不外推 |
| reflection/replication_pad3d.out | `check_tensor({self}, out, self.scalar_type(), reflection_pad3d_npu_out_size(self, padding))` 后 EXEC（out 作命令输出） | check_tensor 内部契约见[输出准备卡](../../inference/guides/optimization/torch_npu/torch_npu_out_preparation_resize_and_overlap.md)；dtype/尺寸参照=self |
| reflection/replication_pad3d_backward（functional） | 按继承的 grad_input 配置生成：`apply_tensor_without_format(self.sizes(), grad_output.options().dtype(self.scalar_type()))`——**options 骨架跟第一个输入张量 grad_output、dtype 覆写为 self.scalar_type()**；单次 `EXEC_NPU_CMD(aclnnReflectionPad3dBackward, grad_output, self, padding, grad_input)` | 反向输出形状恒=self.sizes()（padding 不改变反向形状）；同设备/布局时与 self.options() 等价，跨设备输入的覆写行为按实际部署核对 |
| reflection/replication_pad3d_backward.grad_input | `check_tensor({grad_output, self}, grad_input, self.scalar_type(), self.sizes())` 后 EXEC（同命令，grad_input 作输出） | 同上 |
| 尺寸 helper（KernelNpuOutputSize.cpp 主线1138–1167、1284–1313；发布983–1012、1130–1159） | `reflection_pad3d_npu_out_size`/`replication_pad3d_npu_out_size` 同构：TORCH_CHECK `padding.size() == 6`（原文"padding length should be 6"，PARAM）与 `self.dim() == 4 或 == 5`（原文"self should be 4D or 5D"，PARAM）；5D(N,C,D,H,W)→`{N, C, D+pf+pb, H+pt+pb, W+pl+pr}`、4D(C,D,H,W)→`{C, Do, Ho, Wo}` | 两维长直接相加：**负 padding 得到更小尺寸、无 clamp/非负检查**（本层按原文记录）；schema 为 SymInt[6]，符号维度的取值范围不在本层 |

跨节两条：其一，**3D 族是 pad 家族唯一的“无 acl_op 回退”支线**——1d/2d 走 DO_COMPATIBILITY→aclops（MirrorPad/PadV3(Grad)），3D 生成层直发 aclnn 专用命令，两条路互不推导；上文 1d/2d 的“缺符号回退 slow/acl_op”结论不得搬到 3D。其二，**反向形状合同与 helper 无关**——backward 的 grad_input 尺寸登记为 `self`（不经 `*_pad3d_npu_out_size`），与前向尺寸公式解耦；生成层登记面（yaml）与模板行为在本节核对到“申请/检查+单命令”粒度，aclnnReflectionPad3d(Backward)/aclnnReplicationPad3d(Backward) 设备侧语义（负 padding、越界行为）仍未核对。

### pad3d 生成层补充证据

- [struct_codegen.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/struct_codegen.py)（primary）：43–58（ACLNN_FUNCTIONS_DEFINITION：integral_identity_guard/do_compatibility/new_params/size-dtype/check-apply/exec 槽位）、108–157（filt_op_branch：gen_opapi+版本过滤+structured 约束）、295–476（compute_op_api_definition：out/inplace/functional 三种 check-apply 形态与 cmd_args 组装）。
- [struct_codegen.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/struct/struct_codegen.py)（implementation）：同文件发布侧（404 行）；整文件 diff -u 核对——主线超集差异为 integral_identity_guard/CpuScalarOp/cpu_scalar_h2d 槽位与 PYTORCH_VERSION 校验，模板主链（DO_COMPATIBILITY 条件生成、APPLY_TENSOR/CHECK_TENSOR、EXEC_NPU_CMD）主线与发布两版本 一致。
- [struct/model.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/model.py)（primary）：40–105（ResInfo.parse：out 变体缺省 size/dtype=结果名、输入张量名转 .sizes()/.scalar_type()、option=首输入张量）、139–283（StructInfo.from_yaml：structured_inherit 对 functional 换配置、inplace 才走 DELEGATE、exec 单元素按 schema 参数序补全）。
- [struct/model.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/struct/model.py)（implementation）：同文件发布侧（268 行）；diff -u 核对——差异为 STRUCTURED_GEN_OPAPI_ALLOWED_KEYS/CpuScalarOp 主线新增与排版，ResInfo/cmd_args 主链一致。
- [StructKernelNpuOpApi.cpp 模板 d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/templates/StructKernelNpuOpApi.cpp)（primary）：1–25；完整文件；与发布逐字节相同（sha256 一致）。
- [KernelNpuOutputSize.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1138–1167、1284–1313；reflection/replication_pad3d 两个尺寸 helper 完整函数体（该文件已列于 frontmatter 来源）。
- [KernelNpuOutputSize.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：983–1012、1130–1159；发布侧同 helper 完整函数体（该文件已列于 frontmatter 来源）。
- 负向证据：主线与发布两版本 `op_plugin/ops/`（opapi+aclops）无 *Pad3*/ReflectionPad3*/ReplicationPad3* 实现文件（上文 Pad 包装层一节已 find 零命中，本节不重复计）；canonical 与全部 batch*/staged rg `reflection_pad3d_npu_out_size|aclnnReflectionPad3d` 零命中（canonical 对 aclnnReplicationPad3d 的唯一命中在 ops/ascendc 设备内核卡，另一域另一层，不属本卡）——本节为 3D 两族 wrapper 行为的首个推导级小节。

## constant_pad_nd 的 FP4/FP8 测试合同与主线 FP8 支持

上文Eager包装层小节已闭FP4特例（ACL_FLOAT4_E2M1/E1M2要求pad[0]/pad[1]偶数、末维pad_add减半）与空输入`op_api::fill_`快捷路。本节补主线测试文件三段类合同，并新增**FP8支持面**：主线`test/test_base_ops/test_constant_pad_nd.py`（265行）含`TestConstantPadNdFp4`与`TestConstantPadNdFp8`两个测试类，全部`@SupportedDevices(['Ascend950'])`；发布版本同文件仅19行（保留基础负pad用例，`torch.npu.set_compile_mode(jit_compile=True)`前置），无FP4/FP8/空输入段——该内容差为主线与发布两版本按原文记录事实。

| 测试段 | 合同（测试断言） | 与包装层关系 |
| --- | --- | --- |
| 空输入 | 输入numel==0（含pad后仍0、pad后非0）CPU/NPU结果等值 | 对应上文快捷路：任一为空时`fill_(result, value)`不下发pad命令；测试为CPU参照对照 |
| FP4（float4_e2m1fn_x2，INT8字节打包两值） | pad[0]/pad[1]须偶数；末维输出=`(原维*2+pad左+pad右)//2`；奇数/全奇pad断言RuntimeError；负偶pad与负奇pad也断言RuntimeError | 偶数要求与上文wrapper TORCH_CHECK一致；**负偶pad报错超出wrapper的非负输出维检查**（如(-2,0)于(4,8)输出维8≥0仍报错），机制在未核对的aclnnConstantPadNd设备侧——按原文记录为测试断言合同，未运行验证 |
| FP8（float8_e4m3fn/float8_e5m2） | 标准每字节一值、无奇偶约束、pad后dtype保持、负pad断言RuntimeError（如(-1,-2)于(4,8)，输出维5≥0） | wrapper无FP8特例分支（FP8走通用路）；负pad报错机制同上在设备侧，测试断言先于wrapper检查——这是FP8负pad与上文1d/2d通用负pad路径（允许输出维非负）的**已观察差异候选**，未执行不改写上文结论 |

FP8（e4m3fn/e5m2）pad在主线测试为950门控新支持面；上文支持表未含FP8，本节不据此扩写公开支持矩阵，只记录固定pin静态事实。全部断言未在本卡执行。

### constant_pad_nd 测试补充证据

- [test_constant_pad_nd.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_constant_pad_nd.py)（example）：全文265行；三段类逐条读（空输入、FP4偶/奇/负合同、FP8 e4m3/e5m2各形态）。
- [test_constant_pad_nd.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_constant_pad_nd.py)（constraint）：全文19行；发布简版（基础负pad用例+jit_compile=True前置），diff确认无FP4/FP8/空输入段。
- 实现文件`ConstantPadNdKernelNpuOpApi.cpp`（21–95完整函数体）已列于上文包装层小节，本节不重复计；负pad报错的设备侧机制未核对，归实现分账。
