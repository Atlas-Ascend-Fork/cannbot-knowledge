---
type: Guide
title: torch创建与默认类型：参数、设备和产品范围
description: 区分函数创建入口与Tensor方法，记录asarray完整设备名、dtype版本变化和英文产品排除。
tags:
- task.lookup
- topic.memory
- topic.precision
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
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）NPU-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）NPU-Tensor.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)NPU-Tensor.md
  role: constraint
created_at: '2026-11-09T14:10:41Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# torch创建与默认类型：参数、设备和产品范围

## 固定来源与参数表的范围

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的2.7.1、2.9至2.14中英文torch页；下表默认2.14，较早版本与实际收录语言另列。产品为A2/A3训练系列和950DT，不扩到950PR，不回推26.0/PyTorch2.8发布基线。

每行的input、dtype、tensors等是该条目的局部字段，不与Tensor方法的self表互换，不表示返回值或整个模型的数据类型。没有独立类型表、未收录语言/版本不等于已证实不支持；显式产品排除和额外条件另列。不借同名别名、父对象或相邻函数补齐参数、默认值与实现。这里仅静态核对，没有运行上游、编译、加载文件或进行设备实验。

## 创建和默认设置的产品例外

torch.tensor和set_default_tensor_type中文只列A2/A3，英文明确950DT不支持；不能用Tensor.new_*、其他创建函数或示例中的torch.tensor代替这些条目的范围。set_default_tensor_type还不支持torch.npu.DtypeTensor，英文2.9/2.10/2.14提示弃用并建议分别设置set_default_dtype/set_default_device，其他版本未重复该提示。

其余下表已收录条目列三产品，类型及参数条件独立适用。is_tensor/is_storage/is_complex/is_conj等可查询不表示结果必为True；ones条目名为input的类型说明也不能改写成实际调用必有一个同名Tensor参数。
## 函数级参数类型

| 函数/对象 | 局部参数类型表 | 来源 |
| --- | --- | --- |
| `torch.polar` | abs=FP32 | 中英文 |
| `torch.as_tensor` | data=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.linspace` | dtype=BF16/FP16/FP32/FP64/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.arange` | dtype=BF16/FP16/FP32/FP64/INT32/INT64 | 中英文 |
| `torch.empty`、`torch.frombuffer` | dtype=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.full` | dtype=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.eye` | dtype=BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.ones` | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.empty_like`、`torch.full_like`、`torch.ones_like` | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.zeros_like` | input=BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.is_complex` | input=COMPLEX64/COMPLEX128 | 中英文 |
| `torch.from_numpy` | input=FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.asarray` | obj=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.complex`、`torch.empty_strided`、`torch.get_default_dtype`、`torch.is_conj`、`torch.is_floating_point`、`torch.is_nonzero`、`torch.is_storage`、`torch.is_tensor`、`torch.numel`、`torch.range`、`torch.set_default_device`、`torch.set_default_dtype`、`torch.set_default_tensor_type`、`torch.set_flush_denormal`、`torch.set_printoptions`、`torch.tensor`、`torch.zeros` | 未给独立参数类型表 | 中英文 |
| `torch.fill`、`torch.get_default_device`、`torch.logspace`、`torch.scalar_tensor` | 未给独立参数类型表 | 仅中文 |

## 较早版本的不同参数表

| 函数/对象 | 文档版本 | 当时参数表 | 2.14参数表 | 来源 |
| --- | --- | --- | --- | --- |
| `torch.arange` | 2.10.0、2.7.1、2.9.0 | dtype=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64 | dtype=BF16/FP16/FP32/FP64/INT32/INT64 | 中英文 |
| `torch.zeros` | 2.10.0、2.7.1、2.9.0 | dtype=BF16/FP16/FP32/UINT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 未给独立参数类型表 | 中英文 |

## 文档收录版本与语言

| 函数/对象 | 中文收录版本 | 英文收录版本 |
| --- | --- | --- |
| `torch.get_default_device`、`torch.logspace` | 2.10.0、2.11.0、2.12.0、2.13.0、2.14.0、2.7.1、2.9.0 | 未收录 |
| `torch.fill`、`torch.scalar_tensor` | 2.13.0、2.14.0 | 未收录 |

## 设备与序列语义

中文asarray在obj为NPU Tensor且copy=False时要求省略device或指定与输入一致的完整设备名，例如npu:0；只写不带编号的npu会报设备不匹配。英文只有obj类型表，没有这条补充，保留语言范围。这里不据该条件推导跨进程、跨设备零拷贝和所有权协议。

linspace创建steps大小的一维向量；polar要求abs和angle维度相等，abs仅FP32。英文2.9/2.10/2.14提示range弃用、改用arange时注意后者不包含区间右端点；不能只改函数名而忽略端点行为。zeros较早三版本有dtype表、其余四版没有，不从删去一句话推断所有类型均已验证。

- [Tensor方法的创建和转换](torch_npu_native_tensor_conversion_scope.md)
- [布局和DLPack边界](torch_npu_native_tensor_layout.md)
- [稀疏构造入口](../../../../training/guides/torch_npu_native_sparse_nested_scope.md)

## NPU Tensor别名表的额外范围

OpPlugin发布中文和主线中英文NPU Tensor列表仅列Double/Short/Char/Byte/Float/Half/Int/Bool/LongTensor九种旧式NPU别名，并声明与相应CUDA构造形式对应；没有独立逐硬件/参数合同。这份名称表不改变前文set_default_tensor_type禁止torch.npu.DtypeTensor的条件，也不证明全部dtype运算、FP64 Kernel或950DT默认类型选择可用。

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

- [固定来源 15](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）NPU-Tensor.md)（constraint）

- [固定来源 16](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）NPU-Tensor.md)（primary）

- [固定来源 17](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)NPU-Tensor.md)（constraint）
