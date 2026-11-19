---
type: Guide
title: Tensor创建与类型转换：方法级支持和产品例外
description: 核对Tensor标量、元数据、创建及dtype/device转换入口，保留类与子方法的产品差异。
tags:
- task.lookup
- topic.memory
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-Tensor.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-Tensor.md
  role: constraint
created_at: '2026-11-09T13:59:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# Tensor创建与类型转换：方法级支持和产品例外

## 固定版本与表的读法

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的2.7.1、2.9至2.14中英文Tensor支持页，以下默认展示2.14，较早版本的不同表另列。所列三产品指A2/A3训练系列与950DT，不包含950PR，不回推26.0/PyTorch2.8发布基线。

类型表只描述该方法的self，既不是返回值类型，也不是整个模型应转换成的类型。原文未给独立类型表、语言缺项或版本未收录均不等于已证实不支持；明确的产品排除和方法特有限制另列，优先于概括。FP16/FP32/FP64分别对应fp16/fp32/fp64；保留原文DOUBLE名称，不代填转换规则。仅静态核对，未运行上游、编译或进行设备实验。

## 产品范围必须落到方法

Tensor类条目中文只列A2/A3，英文明确950DT不支持，但大量子方法另列三产品。不能把类条目的范围扩大成“950不能使用任何Tensor”，也不能用子方法支持替类条目补产品。record_stream中文只列A2/A3、英文明确950不支持；英文chalf明确三产品均不支持、中文未收录。其余本指南列出的方法在已收录语言的表中列三产品，但不提供任意参数组合的完整支持证明。

new_empty/new_ones/new_zeros的self为FP32，new_full为INT64，new_tensor没有独立self表；这些不是所有新Tensor的输出默认dtype。元数据和地址查询的FP32 self表不表示size/dim/data_ptr等返回浮点，也不是把所有Tensor统一转FP32的建议。
## 方法级self类型

| 方法/属性 | self类型范围 | 来源 |
| --- | --- | --- |
| `torch.Tensor.fill_`、`torch.Tensor.float`、`torch.Tensor.is_complex`、`torch.Tensor.is_conj`、`torch.Tensor.type_as`、`torch.Tensor.zero_` | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.byte` | BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.bool`、`torch.Tensor.double`、`torch.Tensor.half`、`torch.Tensor.int`、`torch.Tensor.long`、`torch.Tensor.short`、`torch.Tensor.to`、`torch.Tensor.type` | BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.bfloat16` | FP16/FP32 | 中英文 |
| `torch.Tensor.char`、`torch.Tensor.set_` | FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.data_ptr`、`torch.Tensor.dim`、`torch.Tensor.element_size`、`torch.Tensor.is_contiguous`、`torch.Tensor.is_floating_point`、`torch.Tensor.is_pinned`、`torch.Tensor.is_set_to`、`torch.Tensor.is_signed`、`torch.Tensor.item`、`torch.Tensor.ndim`、`torch.Tensor.ndimension`、`torch.Tensor.nelement`、`torch.Tensor.new_empty`、`torch.Tensor.new_ones`、`torch.Tensor.new_zeros`、`torch.Tensor.numel`、`torch.Tensor.numpy`、`torch.Tensor.record_stream`、`torch.Tensor.size`、`torch.Tensor.storage`、`torch.Tensor.storage_offset`、`torch.Tensor.storage_type`、`torch.Tensor.stride`、`torch.Tensor.tolist`、`torch.Tensor.untyped_storage` | FP32 | 中英文 |
| `torch.Tensor.new_full` | INT64 | 中英文 |
| `torch.Tensor.as_subclass`、`torch.Tensor.cdouble`、`torch.Tensor.cfloat`、`torch.Tensor`、`torch.Tensor.cpu`、`torch.Tensor.cuda`、`torch.Tensor.device`、`torch.Tensor.dim_order`、`torch.Tensor.get_device`、`torch.Tensor.imag`、`torch.Tensor.is_cuda`、`torch.Tensor.is_meta`、`torch.Tensor.is_shared`、`torch.Tensor.itemsize`、`torch.Tensor.nbytes`、`torch.Tensor.new_tensor`、`torch.Tensor.real`、`torch.Tensor.shape`、`torch.Tensor.share_memory_`、`torch.Tensor.to_mkldnn` | 未给独立self类型表 | 中英文 |
| `torch.Tensor.module_load`、`torch.Tensor.pin_memory` | 未给独立self类型表 | 仅中文 |
| `torch.Tensor.chalf` | 未给独立self类型表 | 仅英文 |

## 设备、格式与double兼容路径

Tensor.cuda的NPU形式为Tensor.npu，memory_format仅支持torch.contiguous_format；Tensor.to只支持torch.contiguous_format和torch.preserve_format，950DT不支持转换到double。英文to还排除“Atlas推理系列产品”跨NPU复制，来源没有将该措辞映射为A2/A3/950DT或950PR，保留独立产品口径。

Tensor.double说明部分NPU接口尚不支持double，为兼容默认返回FP32，可能回退CPU；不能据此断言所有FP64计算都不支持，也不能将返回类型与self表混合。cfloat/cdouble列三产品不等于所有复数算子组合均可用，chalf的英文显式排除独立适用。

## 元数据、Storage与流的边界

is_cuda/is_meta/is_shared/is_complex/is_conj等属性有支持表不等于其查询结果必为True。data_ptr、storage、untyped_storage、set_、share_memory_和record_stream也不自动建立共享所有权、IPC或流完成合同；未读取活跃地址或创建共享句柄。

- [Storage对象与类型边界](torch_npu_native_storage_scope.md)
- [布局和视图方法](torch_npu_native_tensor_layout.md)
- [设备与流的原生入口](torch_npu_native_device_stream_scope.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-Tensor.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-Tensor.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-Tensor.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-Tensor.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-Tensor.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-Tensor.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-Tensor.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-Tensor.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-Tensor.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-Tensor.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-Tensor.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-Tensor.md)（primary）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-Tensor.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-Tensor.md)（constraint）
