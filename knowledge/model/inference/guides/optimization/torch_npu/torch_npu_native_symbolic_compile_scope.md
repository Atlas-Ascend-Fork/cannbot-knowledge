---
type: Guide
title: 原生符号与编译入口：支持表和后端边界
description: 核对SymInt/SymFloat子项与sym_ite产品范围，区分compile后端名称和完整动态图执行合同。
tags:
- task.implementation
- topic.compilation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch.md
  role: constraint
created_at: '2026-11-09T14:10:41Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 原生符号与编译入口：支持表和后端边界

## 固定来源与参数表的范围

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的2.7.1、2.9至2.14中英文torch页；下表默认2.14，较早版本与实际收录语言另列。产品为A2/A3训练系列和950DT，不扩到950PR，不回推26.0/PyTorch2.8发布基线。

每行的input、dtype、tensors等是该条目的局部字段，不与Tensor方法的self表互换，不表示返回值或整个模型的数据类型。没有独立类型表、未收录语言/版本不等于已证实不支持；显式产品排除和额外条件另列。不借同名别名、父对象或相邻函数补齐参数、默认值与实现。这里仅静态核对，没有运行上游、编译、加载文件或进行设备实验。

## 符号对象与方法

SymInt/SymFloat/SymBool及sym_float/sym_int/sym_max/sym_min/sym_not/sym_sum的已收录表列三产品；SymInt中文只有产品表、英文另写input FP32。SymBool、sym_float/sym_int/sym_max两侧写input FP32，不能把这些局部字段推导为所有符号表达式实际只表示FP32值。SymFloat.as_integer_ratio列三产品；is_integer仅2.7.1/2.9/2.10收录，也列三产品。

sym_ite中文仅A2/A3、英文明确950不支持，不由相邻sym_*的表扩大它。
## 函数级参数类型

| 函数/对象 | 局部参数类型表 | 来源 |
| --- | --- | --- |
| `torch.SymBool`、`torch.sym_float`、`torch.sym_int`、`torch.sym_max` | input=FP32 | 中英文 |
| `torch.SymFloat`、`torch._assert`、`torch.compile`、`torch.sym_ite`、`torch.sym_min`、`torch.sym_not`、`torch.sym_sum` | 未给独立参数类型表 | 中英文 |
| `torch.SymInt` | 未给独立参数类型表 | 中英文；英文：input=FP32 |
| `torch.cond` | 未给独立参数类型表 | 仅中文 |

## 文档收录版本与语言

| 函数/对象 | 中文收录版本 | 英文收录版本 |
| --- | --- | --- |
| `torch.cond` | 2.10.0、2.11.0、2.12.0、2.13.0、2.14.0、2.7.1、2.9.0 | 未收录 |

## compile和控制流

compile两侧列三产品，明确backend可为npugraphs、整体功能与cudagraphs相同；它没有给任意模型、动态形状、训练、所有算子或所有配置的完整合同，不能用这句概括覆盖[原生NPUGraph的推理限定](torch_npu_native_graph_support_scope.md)，也不把TorchAir其他编译后端视作同一个实现。

cond仅中文列三产品，_assert两侧列三产品；条目不提供分支输入、返回结构、别名、反向和重编译的完整约束。符号对象、条件入口或断言可调用，不等于任意数据依赖控制流已完全捕获或没有图中断。实际图行为需按准确后端、版本和模型检查，本次没有执行编译。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch.md)（primary）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch.md)（constraint）
