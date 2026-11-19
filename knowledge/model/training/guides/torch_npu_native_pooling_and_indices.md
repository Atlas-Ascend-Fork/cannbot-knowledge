---
type: Guide
title: 原生池化NPU契约：索引、反池化与版本差异
description: 按版本区分950DT AvgPool3d支持，核对MaxPool的dilation、INT32索引、兼容实现及类函数dtype差异；含 AvgPool/MaxPool/AdaptivePool 的 Eager 包装层：双命令路由、indices 三形态与 acl_op 回退内部。并含 im2col/col2im：SoC 门、空输出短路的 pin 差与 ND→NCHW 桥。
tags:
- task.optimization
- topic.precision
- topic.memory
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
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AdaptiveMaxPool3dKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AdaptiveMaxPool3dBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AdaptiveMaxPool3dKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AdaptiveMaxPool3dBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AdaptiveAvgPool2dKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AvgPool2dKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AvgPool2dBackwardKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AvgPool3dKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AvgPool3dBackwardKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MaxPool2dWithIndicesKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MaxPool2dWithIndicesBackwardKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MaxPool3dWithIndicesKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MaxPool3dWithIndicesBackwardKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AdaptiveAvgPool2dKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AdaptiveAvgPool2dBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AdaptiveAvgPool3dKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AdaptiveAvgPool3dBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AdaptiveMaxPool2dKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AdaptiveMaxPool2dBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AvgPool2dKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AvgPool2dBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AvgPool3dKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AvgPool3dBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MaxPool2dWithIndicesKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MaxPool2dWithIndicesBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MaxPool3dWithIndicesKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MaxPool3dWithIndicesBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AdaptiveAvgPool2dKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AvgPool2dKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AvgPool2dBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AvgPool3dKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AvgPool3dBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MaxPool2dWithIndicesKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MaxPool2dWithIndicesBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MaxPool3dWithIndicesKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MaxPool3dWithIndicesBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AdaptiveAvgPool2dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AdaptiveAvgPool2dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AdaptiveAvgPool3dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AdaptiveAvgPool3dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AdaptiveMaxPool2dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AdaptiveMaxPool2dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AvgPool2dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AvgPool2dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AvgPool3dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AvgPool3dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MaxPool2dWithIndicesKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MaxPool2dWithIndicesBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MaxPool3dWithIndicesKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MaxPool3dWithIndicesBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation

- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/Im2colKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/Im2colKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/Col2imKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/Im2colKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/Im2colKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/Col2imKernelNpu.cpp
  role: implementation

created_at: '2026-11-09T10:11:05Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 原生池化NPU契约：索引、反池化与版本差异

## 固定版本与范围

依据TorchNPU固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 中PyTorch2.7.1、2.9至2.14的完整条目，产品为A2/A3训练系列与950DT，不扩大950PR或发布基线。它们是同一提交中的分版本文档，差异不直接证明发行历史或实际包回归；具体版本按下文区分。未执行上游、设备、精度或性能实验，文档所称“已验证”属于上游口径。

## 不能合并的950DT支持标记

F.avg_pool3d在2.7.1及2.9..2.12页列950DT支持，2.13/2.14页明确改为不支持；同提交nn.AvgPool3d类条目却在七版本均列支持。保留类/函数和文档版本差异，不从类名支持推定当前functional可用，也不把旧页当作新包支持证明。A2/A3在上述条目均列支持。

## MaxPool、indices与内存一致性

F.max_pool1d input仅FP16/FP32，dilation仅1；F.max_pool2d/3d input列BF16/FP16/FP32，dilation分别仅1或全1的二维/三维元组。三者return_indices=True时文档均将argmax列为INT32，不自动套用其他后端的索引dtype约定。

F.max_pool1d/2d及nn.MaxPool2d另列use_compatible_impl(True)用于与社区内存一致性对齐。950DT的MaxPool2d indices按上游对齐，与A2/A3可能不同；不能只比较池化值相同便认定跨平台索引可互换，单纯转INT64也不能证明索引的值/编码语义已对齐。nn.MaxPool1d/3d条目未重复所有functional限制，不能由省略推断其参数无限制。

nn.MaxUnpool1d的950DT段提示重复索引时结果可能与GPU/A2/A3不同，不能据随机无重复样本推断全部散写语义一致。MaxUnpool1d/2d类input只列FP16/FP32；F.max_unpool1d/2d还列FP64、UINT8、INT8/INT32/INT64，不能把该集合扩展到类入口。F.max_unpool2d在jit_compile=False时还要求output_size乘积≥input H×W；按实际接口的output_size解释，不把batch或通道维随意并入这个条件。

## 平均、自适应与LP池化的精度路线

| 入口 | input条目 |
| --- | --- |
| AvgPool1d/2d及对应functional | BF16/FP16/FP32 |
| AdaptiveAvgPool1d及functional | FP16/FP32 |
| AdaptiveAvgPool2d类 | FP16/FP32 |
| F.adaptive_avg_pool2d、AdaptiveAvgPool3d及functional | BF16/FP16/FP32 |
| AdaptiveMaxPool3d及functional | FP32/FP64 |
| F.lp_pool1d/2d | FP16/FP32 |
| LPPool1d类 | FP16/FP32、UINT8、INT8/16/32/64、BOOL |
| LPPool2d类 | FP16/FP32、INT16/32/64、BOOL |

AdaptiveMaxPool1d/2d及functional、LPPool3d、MaxUnpool3d及functional等条目只列产品而未给额外dtype表；不以此补全未写出的全部形状、类型和反向组合。整数input被列出也不等于整数可求梯度。

F.fractional_max_pool2d明确可能CPU回退，类FractionalMaxPool2d与3d及functional 3d未重复这句话，不能把它扩展为全部Fractional池化必回退。应检查实际CPU/NPU路径和数据转移。

## Fold/Unfold接线

Unfold及F.unfold列BF16/FP16/FP32；Fold类仅列FP16，F.fold列FP16/FP32。名字互逆不表示所有dtype都双向支持，更不表示输出零分配或任意参数下Fold(Unfold(x))恒等。先核对实际patch/重叠及形状语义，再测整个卷积/视觉链路。

## 验证

核对值、indices的dtype/内容、下游Unpool或Gather、重复索引、dilation和反向；使用实际版本的公开范围及选中Kernel，支持表差异保留待确认。只读来源审阅不等于完成设备验证。

- [兼容实现与CPU门控](../../inference/guides/optimization/torch_npu/torch_npu_cpu_fallback_and_compatible_impl.md)
- [Padding边界](torch_npu_native_padding_constraints.md)

## 3D LP池化的functional条目

F.lp_pool3d在七版本页列A2/A3训练系列与950DT支持，但没有另列完整dtype表；不能把F.lp_pool1d/2d或LPPool类的整数/浮点集合直接并入。维度、距离阶数、输入和反向仍按真实接口核对，不据名称推定完整参数兼容。

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

## AdaptiveMaxPool3d的CPU往返与索引准备

两版固定OpPlugin的AdaptiveMaxPool3d前后向都在本地显式选择CPU慢路。它与前文文档FP32/FP64条目一起解释：文档中的类型范围不能单独证明该类型落到NPU内核，Double在下面的包装实现中直接转CPU。

| 实际条件或入口 | 行为 | 可见准备成本 |
| --- | --- | --- |
| 前向静态探测不到`aclnnAdaptiveMaxPool3d`或其GetWorkspaceSize符号，或self为Double | WARN_ONCE后走CPU；判断早于本地正常out检查/输出申请 | functional将self.cpu，CPU生成值和indices后分别to(self.device)；out将已有out、indices及self转CPU，执行CPU out后分别copy回两个原输出 |
| 反向独立探测不到`aclnnAdaptiveMaxPool3dBackward`或其GetWorkspaceSize，或**self**为Double | 同样先转CPU；门控读self.dtype，不是grad_output.dtype | functional将grad_output/self/indices转CPU，再将梯度to(grad_output.device)；out还先将grad_input.cpu，CPU out后copy回原grad_input |
| NPU前向functional | 申请self dtype的值输出和独立indices，然后调用aclnnAdaptiveMaxPool3d | SoC枚举≥Ascend950申请Long indices，较小枚举申请Int |
| NPU前向out | 值输出检查使用self dtype；≥950时传入indices为Long则保Long，否则要求Int；较小枚举要求Int | 已有out并不绕过shape/dtype检查；CPU分支则先于这些检查返回，交给CPU out路径处理 |
| NPU反向 | out检查grad_output dtype、自身self形状；functional按self形状、grad_output options申请，再执行aclnnAdaptiveMaxPool3dBackward | 这段本地代码没有显式把indices统一cast成另一dtype |

形状helper仅在self.dim()==4时拼`[C, OD, OH, OW]`，dim==5时拼`[N,C,OD,OH,OW]`，其余返回空shape，并直接读取output_size前三项；它自身没有完整rank/长度合法性检查。Schema声明output_size为int[3]，不能据此把helper说成任意Tensor入口的完备校验器。

上述逻辑在两版语义相同，950的indices分支也同时存在，不能写成仅主线新增。静态双符号探测复用已审的[TopK与排序入口证据](torch_npu_sort_topk_routing_and_legacy_output_costs.md)，只判断符号可见，不是执行支持认证；此处没有把普通DO_COMPATIBILITY的AclnnOnly门控套到显式CPU分支。实际往返传输、同步时间和格式转换由运行环境决定，本卡只审阅固定源码。

### AdaptiveMaxPool3d补充证据

- [AdaptiveMaxPool3dKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AdaptiveMaxPool3dKernelNpuOpApi.cpp)（implementation）：1–89。
- [AdaptiveMaxPool3dBackwardKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AdaptiveMaxPool3dBackwardKernelNpuOpApi.cpp)（implementation）：1–81。
- [KernelNpuOutputSize.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1960–1968。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：905–915。
- [op_api_common.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp)（implementation）：767–773。
- [AdaptiveMaxPool3dKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AdaptiveMaxPool3dKernelNpuOpApi.cpp)（implementation）：1–78。
- [AdaptiveMaxPool3dBackwardKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AdaptiveMaxPool3dBackwardKernelNpuOpApi.cpp)（implementation）：1–71。
- [KernelNpuOutputSize.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1770–1779。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：879–889。
- [op_api_common.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.cpp)（implementation）：785–792。

## AvgPool/MaxPool/AdaptivePool 的 Eager 包装层与 acl_op 回退

本节核对两版OpPlugin固定树内池化入口的Eager包装层：手写opapi文件、yaml生成层条目与acl_op回退内部；上文AdaptiveMaxPool3d前后向（CPU往返节）与文档支持表结论保持不变，max_unpool不重复。yaml登记逐条实读：`_adaptive_avg_pool2d`/`_adaptive_avg_pool3d`（前向带`_backward`）主线43–76、`adaptive_avg_pool2d(.out)`/`adaptive_avg_pool3d.out`/`adaptive_avg_pool3d_backward.grad_input`/`adaptive_max_pool2d`四条852–919、avg_pool2d/3d前后向八条1283–1315、max_pool2d/3d_with_indices八条3449–3481；发布826–893、1245–1277、3348–3380，与主线逐字相同（python逐行对比）。AdaptiveAvgPool2d/3d与MaxPool的opapi手写文件齐全，Adaptive系列反向走yaml生成层（gen_opapi exec `aclnnAdaptiveAvgPool2dBackward`/`aclnnAdaptiveAvgPool3d(Backward)`、`aclnnAdaptiveMaxPool2d(Backward)`，out尺寸=self或max_pool2d_out_size、indices dtype kLong）。

| 家族 | op_api 层实际门槛与动作 | acl_op 回退内部 | 关键边界 |
| --- | --- | --- | --- |
| adaptive_avg_pool2d/`.out`/`_adaptive_avg_pool2d` | 手写opapi：`DO_COMPATIBILITY(aclnnAdaptiveAvgPool2d, acl_op::…)`；functional在output_size=1×1且非量化时走`self.mean({-1,-2}, true)`组合（源码注释：与CPU实现不同、resnet50精度问题），其余委托`at::_adaptive_avg_pool2d`回入out层；`_adaptive`只查rank3/4，out层查result dtype==self后EXEC aclnnAdaptiveAvgPool2d | 全维非空+rank3/4检查；1×1输出走`at::mean_out`；否则ACE命令`AdaptiveAvgPool2d`（output_size attr）；CheckOut带NPU format，check_match不符时format_contiguous执行后format_fresh_view | 1×1快捷在两路各自独立实现；mean是设备归约命令，与池化命令不等价 |
| `_adaptive_avg_pool2d_backward`（+生成层grad_input） | 生成层exec aclnnAdaptiveAvgPool2dBackward，out尺寸=self、dtype=self | grad_output至少2D；其H/W均为1时`result.fill_(1.0/安全尺寸).mul_(grad_output)`组合，否则ACE命令`AdaptiveAvgPool2dGrad`（orig_input_shape attr）；安全尺寸=输入末两维乘积（空shape返回1） | fill_+mul_是两条设备命令组合，无单条反向池化命令 |
| `_adaptive_avg_pool3d(±backward)`/`adaptive_avg_pool3d.out`/`adaptive_avg_pool3d_backward.grad_input` | 前向生成层out尺寸经`adaptive_avg_pool3d_npu_output_size(self, output_size)`、dtype=self，exec aclnnAdaptiveAvgPool3d；反向exec aclnnAdaptiveAvgPool3dBackward | **acl_op回退仅支持D=H=W=1**：前向out_nocheck与functional各一次TORCH_CHECK硬拒其他output_size，随后`at::mean({-3,-2,-1}, true)`；反向同样硬拒grad 1×1×1，`fill_(1.0/安全尺寸).mul_`（安全尺寸含int64溢出TORCH_CHECK） | 文档表BF16/FP16/FP32不与该回退互推；acl_op路根本没有3D自适应池化命令 |
| `adaptive_max_pool2d`（.out/_backward/.grad_input） | 生成层exec aclnnAdaptiveMaxPool2d(Backward)，indices登记dtype kLong、尺寸max_pool2d_out_size | 全维非空+rank3/4；**H/W整除硬门**（input_size%output_size==0）；stride=H/O、kernel=H-(O-1)*stride推导后ACE命令`MaxPoolWithArgmaxV1`（argmax输出uint16）；indices申请为**Int16(kShort)+ACL_FORMAT_NC1HWC0的mask形状{n,c,kH·kW,ceil(OH·OW/16)+1}**；out变体CheckOut却要求indices **Long**；反向`MaxPoolGradWithArgmaxV1`，grad_input强制NC1HWC0 | functional(Int16)与out(Long)的indices dtype不对称按原文记录；mask形状不是[.,.,O_H,O_W]逻辑布局 |
| avg_pool2d四条 | 手写opapi：divisor_override存在时非零TORCH_CHECK；stride非零、pad非负且**pad≤kernel/2**；**无rank检查**；aclnnAvgPool2d额外携带`get_cube_math_type(false)`参数；backward functional有rank3/4、out变体无；grad_input dtype/格式跟grad_output、尺寸跟self（avg_pool2d_backward_npu_output_size） | functional查divisor∈**[1,255]**（out变体无此区间检查）、rank3输入unsqueeze(0)输出squeeze(0)；ACE命令`AvgPoolV2`：ksize/strides补1成4元、pads经get_paddings按ceil_mode补偿成非对称4元、data_format NCHW、**FP16/Int8输入exclusive强制true（忽略count_include_pad）**；反向`AvgPoolV2Grad`对称pads、exclusive=not count_include_pad、**命令不携带divisor_override**；反向functional的grad dtype跟self | 2D与3D的检查面互不移植；out变体跳过[1,255]区间；exclusive特殊化只作用于FP16/Int8 |
| avg_pool3d四条 | 手写opapi：**SoC<Ascend910B1整族先转acl_op**（先于DO_COMPATIBILITY）；kernel/stride/padding长度1或3、rank4/5、divisor非零、pool3d_shape_check；**没有pad≤kernel/2检查**（与2D不对称）；aclnnAvgPool3d**不携带cube_math_type**；backward无divisor检查、grad跟grad_output | `AvgPool3D`/`AvgPool3DGrad`：pads对称6元；functional以ACL_FORMAT_NCDHW申请（apply_tensor_with_format）；rank4双侧unsqueeze再squeeze；out变体CheckOut以result为参照；**反向先把输出buffer resize_as_(input)+zero_()再执行**；反向paddings向量按{pad_H, pad_W, pad_T}顺序构造再对称展开（与前向{p0,p0,p1,p1,p2,p2}顺序不同，字面按原文记录） | `AvgPool3dBackwardKernelNpu.cpp`以`__has_include(<ATen/native/PoolingChecks.h>)`双路shape check——2.15在研把avg_pool3d_backward_shape_check并入pool3d_backward_shape_check（PR#196230），源码注释注明正式发包后改回VERSION_BETWEEN |
| max_pool2d_with_indices四条 | 手写opapi：**双命令路由**——`!c10_npu::IsAclnnOnly() && !CheckCompatibleImpl()`走aclnnMaxPool2dWithMask（indices为Int8 mask：形状{n,c,kH·kW,(ceil(OH·OW/16)+1)×32}，注释"5HD format return the indices with mask, dtype int8"）；否则走aclnnMaxPool2dWithIndices（indices**aclnn-only设备(Ascend950及以后)为Long对齐PyTorch、其他产品Int32**，形状=输出）；functional全参数检查+at::native::pool2d_shape_check+命名张量传播（V2R13起按VERSION_BETWEEN不读names）；**out变体无本地参数检查直接EXEC**；DO_COMPATIBILITY按各自命令符号回退acl_op；backward同双路由，indices原样透传**无本地dtype/shape检查** | `MaxPoolWithArgmaxV1`：indices mask{n,c,kH·kW,ceil(OH·OW/16)+1}（**无×32**，与WithMask路不同）NC1HWC0格式，functional按apply_tensor_with_format申请、out变体CheckOut以indices自身scalar_type校验；反向`MaxPoolGradWithArgmaxV1`：**indices为Int8时按`view(kShort)`重解释并原地改写NPUBridge存储描述（末维/2/16并追加16维、format NC1HWC0、dtype Short、origin NCHW）**，衔接opapi WithMask前向mask进ACE命令（源码注释：避免FE插transdata破坏连续存储）；非Int8原样以uint16喂命令 | 两路命令的indices语义（mask vs argmax）不同；兼容实现（CheckCompatibleImpl）即use_compatible_impl环境会切到WithIndices命令——与[兼容实现卡](../../inference/guides/optimization/torch_npu/torch_npu_cpu_fallback_and_compatible_impl.md)的max_pool短名单衔接，环境页清单不穷举 |
| max_pool3d_with_indices四条 | 手写opapi：aclnnMaxPool3dWithArgmax(Backward)；indices**恒Int32**（文件注释"The indices tensor can only be of int32 type"，与2D的950 Long对齐不同）；**SoC门：Ascend910B1≤SoC<Ascend310B1 或 SoC>Ascend310B4才走opapi路**，区间外整族转acl_op；out变体无本地参数检查；backward grad跟grad_output、尺寸跟self | `MaxPool3D`命令**没有独立indices输出——两返回值tie(result, result)同一张量**（out变体的indice参数完全不检查）；反向`MaxPool3DGrad`消费orig_x/**orig_y**/grads三输入——orig_y即前向输出值张量而非argmax；functional反向**grad_output.clone()防御拷贝**、grad_input强制**Float dtype+NDC1HWC0**（out变体CheckOut反而按self dtype）；ceil_mode经complete_pad补非对称pads | 3D的acl_op"indices"是池化值，与2D的mask/argmax语义都不同，不跨族混用；functional Float强制与out self dtype不对称按原文记录 |

跨族三条：其一，**门有三层**——设备枚举门（avg_pool3d的910B1下限、max_pool3d的310B区间排除）、环境门（CheckCompatibleImpl/IsAclnnOnly只改变2D maxpool的命令选择）、DO_COMPATIBILITY符号门（缺aclnn符号回退acl_op），不能由一层生效推断其余。其二，**functional与out变体检查面普遍不对称**：max_pool2d/3d的out无参数检查、avg_pool2d的out无[1,255]、avg_pool2d_backward的out无rank检查——用out变体时不能假设functional的host检查仍在。其三，**梯度dtype参照分裂**：opapi的avg_pool2d/3d与max_pool3d反向跟grad_output，acl_op的avg_pool2d反向跟self，acl_op的max_pool3d反向functional强制Float（out按self）——任一路径都不构成通用规则。

### 池化包装层补充证据

- [AdaptiveAvgPool2dKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AdaptiveAvgPool2dKernelNpuOpApi.cpp)（primary）：20–92；手写opapi三入口完整函数体。
- [AvgPool2dKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AvgPool2dKernelNpuOpApi.cpp)（primary）：22–140；`AvgPool2dBackwardKernelNpuOpApi.cpp` 23–106；`AvgPool3dKernelNpuOpApi.cpp` 24–194；`AvgPool3dBackwardKernelNpuOpApi.cpp` 23–98；`MaxPool2dWithIndicesKernelNpuOpApi.cpp` 25–197；`MaxPool2dWithIndicesBackwardKernelNpuOpApi.cpp` 22–86；`MaxPool3dWithIndicesKernelNpuOpApi.cpp` 25–157；`MaxPool3dWithIndicesBackwardKernelNpuOpApi.cpp` 22–90；均为完整函数体。
- [aclops 池化八组 d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AvgPool2dKernelNpu.cpp)（primary）：AdaptiveAvgPool2d 21–108、AdaptiveAvgPool2dBackward 20–69、AdaptiveAvgPool3d 21–93、AdaptiveAvgPool3dBackward 20–81、AdaptiveMaxPool2d 21–190、AdaptiveMaxPool2dBackward 21–128、AvgPool2d 21–253、AvgPool2dBackward 21–140、AvgPool3d 20–231、AvgPool3dBackward 20–357、MaxPool2dWithIndices 20–257、MaxPool2dWithIndicesBackward 20–208、MaxPool3dWithIndices 20–217、MaxPool3dWithIndicesBackward 20–260；均为完整函数体（前部版权头不重复计行）。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（primary）：43–76、852–919、1283–1315、3449–3481；本节所述全部池化Schema条目（该文件已列于frontmatter来源）。
- 发布版本对应上述23个实现文件与yaml行段（AdaptiveAvgPool2d opapi 66行、aclops 107行等，行数见manifest source_meta）：逐文件与主线**去空白字符流相同**（`tr -d '[:space:]'`比对，仅版权头换行/排版差异；`AvgPool3dBackwardKernelNpu.cpp`发布217行对主线357行为缩进重排）；yaml发布43–76、826–893、1245–1277、3348–3380与主线逐字相同。
- 负向证据：`op_plugin/ops/`主线与发布两版本无`AdaptiveAvgPool3d`/`AdaptiveAvgPool2dBackward`/`MaxPool`（非WithIndices）等opapi手写文件（find零命中）——这些入口只存在生成层exec或aclops回退；aclops无`AdaptiveMaxPool3d`文件（上文AdaptiveMaxPool3d节已核对opapi层，acl_op无对应实现文件，DO_COMPATIBILITY语义见上文TopK证据卡口径）。

## im2col/col2im：SoC门、空输出短路的pin差与ND→NCHW桥

上文“Fold/Unfold接线”只锚定公开清单的dtype差异；本节补齐 `im2col(±.out)` 与 `col2im(±.out)` 在两版OpPlugin固定树的Eager实现层，核对 per_name 账本 g07 采样/网格区段的 col2im/im2col 两名。yaml登记主线与发布两版本逐字相同（python逐行对比）：`im2col`/`im2col.out` 为 `acl_op+op_api all_version`、无gen_opapi（主线2855–2857、2859–2861，发布2769–2771、2773–2775）——手写opapi文件承担op_api路；`col2im`/`col2im.out` 为 `[v2.1, newest]` 双登记外加gen_opapi（主线1893–1900、1902–1908，发布1834–1841、1843–1849）：out尺寸=`im2col_backward_npu_output_size(self, output_size, kernel_size)`、functional另有dtype=self，exec=`aclnnIm2colBackward`——**col2im的op_api路由是生成层直接调aclnnIm2colBackward**，主线与发布两版本均无手写Col2im opapi文件（find零命中），acl_op路由由aclops Col2imKernelNpu.cpp承担。生成层与结构化适配语义沿用上文池化节口径，不推导生成wrapper的额外检查。

| 入口 | 实际门槛→动作 | 失败/边界 |
| --- | --- | --- |
| im2col/im2col_out（opapi手写，主线24–56） | 每入口先`DO_COMPATIBILITY(aclnnIm2col, acl_op::im2col(_out)(...))`，随后**SoC门：`GetSocVersion() < Ascend910B1` 时直接整族转投acl_op实现**（与上文avg_pool3d同型的枚举门，先于尺寸推导）——即使aclnnIm2col符号可用，910B1以下也不走aclnn路；尺寸经`op_infer::image_to_col_npu_output_size(self, ...)`（self原样、3维不unsqueeze）；out变体`check_tensor({self}, out, out.scalar_type(), output_size)`后、functional按`apply_tensor_without_format(self, output_size)`申请后**主线独有的numel==0短路**（各一处，注释原文"Return the empty result directly when the output tensor is empty."，空输出不再下发命令）；单次`EXEC_NPU_CMD(aclnnIm2col, self, kernel_size, dilation, padding, stride, out/result)` | **发布版本无numel==0短路**（该两段为主线新增，pin差定案）；im2col opapi无本层shape检查（aclops路的im2col_shape_check不在此路），输入合法性依赖尺寸helper与SDK；3维self原样传SDK（helper内部need_squeeze产两维输出） |
| im2col/im2col_out（acl_op回退，主线24–145） | `im2col_shape_check`：self 3D（size(0)可0、size(1)/size(2)非0）或4D（size(1)/size(2)/size(3)非0，消息含sizes，PARAM），kernel_size长度1或2、stride/dilation/padding各空或1或2；nocheck内归一：单元素kernel补成{k,k}、空stride/dilation补{1}、空padding补{0}，padding 1元→{p,p,p,p}、2元→{p0,p0,p1,p1}；**self为ACL_FORMAT_ND时先`npu_format_cast(self, ACL_FORMAT_NCHW)`**（非ND输入原样）；ACE命令"Im2col"（x输入+ksizes/strides/dilations attrs+`padding_mode="CALCULATED"`+pads）；wrapper层3维输入`unsqueeze(0)`成4维、结果`squeeze(0)`回两维（与opapi路的原始3维直传不对称）；out变体CheckOut+check_match不匹配时format_contiguous执行后format_fresh_view | ND→NCHW是回退路私有的格式桥，不与opapi路without_format互推；`padding_mode="CALCULATED"`是命令字面，不据以断言padding语义与ATen一致；shape_check的“possibly 0 batch size”只覆盖3D的size(0) |
| image_to_col_npu_output_size（两路共用的尺寸helper，主线1736–1785） | ksize/stride/dilation/padding先各自归一（1元补两元、空补默认）；`out_h = div_rtn((H + 2*p0 - (d0*(k0-1) + 1)) / s0) + 1`（W同构，H/W取输入第index/index+1维）；`out_h<1或out_w<1`时`AT_ERROR`（原文"The shape (…, …) of the array calculated by other parameters must be at least one."）；3维输入输出`{C*kH*kW, out_h*out_w}`、4维输入输出`{N, C*kH*kW, out_h*out_w}` | helper同时被opapi路（self原样）与aclops路（unsqueeze后4维）调用——3维输入经两条路得到相同最终形状但中间合同不同；div_rtn的舍入方向沿用ATen同名语义（上游未核对，不展开） |
| col2im/col2im_out（op_api生成层，登记面） | gen_opapi exec `aclnnIm2colBackward`；out尺寸经`im2col_backward_npu_output_size(self, output_size, kernel_size)`（主线1322–1344：TORCH_CHECK grad 2D（两维非0）或3D（size(1)/size(2)非0，消息"Expected 2D or 3D (batch mode) tensor for gradOutput..."，PARAM）+`kernel_size[0]*kernel_size[1] != 0`（"kernel_size should not be zero"）；2D→`{size(0)/(kH*kW), H, W}`三维持、3D→`{N, size(1)/(kH*kW), H, W}`），functional dtype=self | **生成层直接支持2D grad输入合同**（输出3维），与aclops路的“2D先unsqueeze成4维执行再squeeze”是不同合同——两路输出形状一致（squeeze后），但2D输入的host检查文本与桥接层数不同；aclnnIm2colBackward设备侧语义未核对 |
| col2im/col2im_out（acl_op回退，主线23–156） | `check_func`：grad_output.dim()>=2、input_size/kernel_size/dilation/padding/stride各size()>=2、`kernel_size[0]*kernel_size[1] > 0`（均PARAM，消息"col2im expected ..."）；2维grad `unsqueeze(0)`成3维；nocheck先把grad view成`{N, C/(kH*kW), kH*kW, L}`（size(1)除以kernel积），`input_sizes`以at::kInt设备输入传命令；ACE命令"Col2im"（x输入+kernel_size/dilation/padding/stride attrs）；输出尺寸`{N, C/(kH*kW), input_size[0], input_size[1]}`；out变体CheckOut+check_match/format_contiguous/format_fresh_view，2维输入结果`squeeze(0)`回 | size()>=2的检查措辞是“大于等于2”（允许>2的参数数组，多余元素是否消费由命令侧决定，字面按原文记录）；grad的size(1)不整除kernel积时view直接抛ATen错误，本层无预检查 |

跨节三条：其一，**im2col的acl_op回退在910B1以下是默认路而非仅缺符号回退**——SoC门与DO_COMPATIBILITY是两层独立触发，与上文池化节的三层门（设备枚举/环境/符号）口径一致。其二，**两名的op_api/acl_op路对2D/3D输入的合同不同**：im2col的opapi路3维直传、aclops路4维桥接；col2im的生成层2D直出3维、aclops路2D桥接后squeeze——按入口与维度组合分别核对，不互推。其三，**发布版本的im2col opapi无空输出短路**：主线对numel==0提前返回不再下发命令，发布仍会向SDK下发空输出命令（其接受性未核对）。上文“Fold/Unfold接线”的dtype表（Unfold BF16/FP16/FP32、Fold FP16/FP32等）不因本节实现层结论改变。

### im2col/col2im 补充证据

- [Im2colKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/Im2colKernelNpuOpApi.cpp)（primary）：24–56；im2col_out与im2col完整函数体（含主线numel==0短路两段）。
- [Im2colKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/Im2colKernelNpu.cpp)（primary）：24–145；im2col_shape_check、im2col_out_nocheck与两个wrapper完整函数体。
- [Col2imKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/Col2imKernelNpu.cpp)（primary）：23–156；col2im_out_nocheck、check_func与两个wrapper完整函数体。
- [KernelNpuOutputSize.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1322–1342、1736–1785；im2col_backward_npu_output_size与image_to_col_npu_output_size两个完整函数体（该文件已列于frontmatter来源）。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：1893–1908、2855–2861；col2im两条目（含gen_opapi完整字段）与im2col两条目（该文件已列于frontmatter来源）。
- [Im2colKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/Im2colKernelNpuOpApi.cpp)（implementation）：24–50；发布侧完整函数体——**无numel==0短路两段**（主线58行/发布50行，diff -u核对：其余仅排版）。
- [Im2colKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/Im2colKernelNpu.cpp)（implementation）：完整本地文件（146行），与主线去空白字符流相同。
- [Col2imKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/Col2imKernelNpu.cpp)（implementation）：完整本地文件（133行），与主线去空白字符流相同（仅排版差异）。
- [KernelNpuOutputSize.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1171–1189、1548–1589；两个helper发布侧完整函数体（该文件已列于frontmatter来源）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：1834–1849、2769–2775；同四条目，与主线逐字相同。
- 负向证据：主线与发布两版本 `op_plugin/ops/opapi/`无Col2im手写文件（find零命中）；canonical与全部batch*/staged rg `Im2colKernelNpuOpApi|Col2imKernelNpu|image_to_col_npu_output_size` 零命中——本节为im2col/col2im首个实现级小节（上文“Fold/Unfold接线”仅docs面）。
