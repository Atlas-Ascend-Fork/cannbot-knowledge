---
type: Guide
title: 原生稀疏与嵌套Tensor：构造、子方法和反向边界
description: 保留稀疏压缩入口的950DT差异，以及嵌套张量“仅创建”文字与转换操作表的张力。并含 _coalesce 宿主组合链与 to_padded_tensor 原生委托的实现层；含 add.out/mul.out 的 sparse 标记实现层：index_add/cat 组合链与 mul 的 dense 往返。
tags:
- task.implementation
- topic.memory
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-sparse.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-sparse.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-sparse.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-sparse.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-sparse.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-sparse.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-sparse.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-sparse.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-sparse.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-sparse.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-sparse.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-sparse.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-sparse.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-sparse.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-nested.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nested.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nested.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nested.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nested.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-nested.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-nested.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nested.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nested.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nested.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nested.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nested.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nested.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nested.md
  role: constraint
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
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/sparse/SparseCoalesceKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/sparse/SparseCoalesceKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NestedTensorToPaddedTensorKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/sparse/SparseAddKernelOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/sparse/SparseTensorUtils.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/sparse/SparseTensorUtils.h
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/gen.py
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/gen_op_plugin_functions.py
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/sparse/SparseAddKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/sparse/SparseTensorUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/sparse/SparseTensorUtils.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/gen.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/gen_op_plugin_functions.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torchnpugen/gen_backend_stubs.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torchnpugen/gen_backend_stubs.py
  role: implementation

created_at: '2026-11-09T12:35:41Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
- '950'
---

# 原生稀疏与嵌套Tensor：构造、子方法和反向边界

## 版本与证据

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的PyTorch2.7.1、2.9至2.14支持页，中英文按实际条目分别审阅；不回推26.0/PyTorch2.8发布组合，不把950DT扩为950PR。未收录条目/产品仅代表清单未验证，支持表不替代完整社区参数手册。本卡仅静态审阅，未执行上游或设备实验。

## 稀疏表示按方法区分

sparse页对Tensor.coalesce/sparse_resize_/sparse_resize_and_clear_/is_coalesced与check_sparse_tensor_invariants及disable/enable/is_enabled列三类产品。Tensor.is_sparse_csr/to_sparse_coo/crow_indices/col_indices/row_indices/ccol_indices、torch.sparse_compressed_tensor的中文页只列A2/A3，英文明确950DT不支持；不将部分Tensor方法支持扩成全部稀疏布局和转换可用。

中文另列torch.sparse.mm、sum的三类产品，英文没有这些条目；英文对as_sparse_gradcheck列三类产品均不支持。spdiags只在英文2.7.1、2.11..2.13页收录，三类产品均不支持；2.13原文夹带的git fetch字样属于来源文本损坏，不作为安装或执行步骤。

表中未给完整COO/CSR/CSC/BSR/BSC、索引dtype、合并重复项、数值类型和梯度矩阵。构造/索引/不变量工具支持不证明稀疏计算或反向已支持；[autograd.backward明确排除稀疏Tensor](torch_npu_native_autograd_transforms.md)，不能由sparse.mm的产品表绕过。

## 嵌套张量的内部范围差异

nested_tensor和as_nested_tensor在两种语言七版本列三类产品，但同时写“目前嵌套张量只支持创建，不支持其他操作”。同页又对nested_tensor_from_jagged、to_padded_tensor、masked_select、narrow列支持。两种材料层次都保留：不能把泛化的“仅创建”当作已证明这些独立条目失效，也不能反向宣称任意嵌套运算、训练和图模式都已验证。

narrow另明确950DT不支持complex64/complex128；不将这个局部排除推广为其他嵌套入口的完整dtype表。jagged/offsets/lengths、拷贝与view、输出布局和反向仍需完整参数与实现证据，清单没有给出时保持未知。

## 验收

记录具体表示、索引/offset、shape、dtype、设备与是否求导，逐步检查构造、转换、消费者和反向，再比较真实存储与端到端性能。更多零值、压缩存储或创建成功不直接证明Kernel稀疏加速；本文没有执行稀疏或嵌套Tensor实验。

## Tensor稀疏查询与转换的独立范围

同提交Tensor页indices/values中文仅A2/A3、英文明确950不支持，values依赖稀疏Tensor；dense_dim/sparse_dim/to_dense及to_sparse_csr/csc/bsr/bsc列三产品。英文额外对smm/sspaddmm/sparse_mask/to_sparse明确三产品均不支持、中文未列，不用压缩格式转换支持替普通to_sparse补范围。

## 方法级self类型

| 方法/属性 | self类型范围 | 来源 |
| --- | --- | --- |
| `torch.Tensor.is_sparse` | FP32 | 中英文 |
| `torch.Tensor.dense_dim`、`torch.Tensor.indices`、`torch.Tensor.sparse_dim`、`torch.Tensor.to_dense`、`torch.Tensor.to_sparse_bsc`、`torch.Tensor.to_sparse_bsr`、`torch.Tensor.to_sparse_csc`、`torch.Tensor.to_sparse_csr`、`torch.Tensor.values` | 未给独立self类型表 | 中英文 |
| `torch.Tensor.smm`、`torch.Tensor.sparse_mask`、`torch.Tensor.sspaddmm`、`torch.Tensor.to_sparse` | 未给独立self类型表 | 仅英文 |

## 较早版本的不同类型表

| 方法 | 文档版本 | 当时self表 | 2.14 self表 | 来源 |
| --- | --- | --- | --- | --- |
| `torch.Tensor.is_sparse` | 2.11.0、2.12.0、2.13.0、2.7.1 | 未给独立self类型表 | FP32 | 中英文 |

is_sparse的变化不是单调随版本扩大：2.7.1/2.11/2.12/2.13中英文列三产品且没有独立self表；2.9/2.10/2.14中文只列A2/A3、英文明确950不支持，两侧self为FP32。按准确版本核对，不由此推断所有Tensor或所有稀疏计算不能用于950。支持查询和转换也不证明全部稀疏布局、算子及梯度组合可用。

## torch稀疏构造的局部类型

同提交torch页七版本两侧sparse_coo_tensor与sparse_csr/csc/bsr/bsc_tensor列三产品。COO的indices只列INT32/INT64、values只列FP16/FP32/INT32，dtype参数必须与values.dtype一致；其余四种构造只有产品表，不借COO表填入压缩格式的全部类型/形状规则。

Tensor.to_sparse的英文显式不支持与这些独立构造入口并存；构造支持也不证明任意稀疏算子、布局转换或反向组合可用。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-sparse.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-sparse.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-sparse.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-sparse.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-sparse.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-sparse.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-sparse.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-sparse.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-sparse.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-sparse.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-sparse.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-sparse.md)（primary）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-sparse.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-sparse.md)（constraint）
- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-nested.md)（constraint）
- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nested.md)（constraint）
- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nested.md)（constraint）
- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nested.md)（constraint）
- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nested.md)（constraint）
- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-nested.md)（constraint）
- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-nested.md)（constraint）
- [固定来源 22](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nested.md)（constraint）
- [固定来源 23](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nested.md)（constraint）
- [固定来源 24](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nested.md)（constraint）
- [固定来源 25](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nested.md)（constraint）
- [固定来源 26](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nested.md)（primary）
- [固定来源 27](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nested.md)（constraint）
- [固定来源 28](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nested.md)（constraint）

- [固定来源 29](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-Tensor.md)（constraint）

- [固定来源 30](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-Tensor.md)（constraint）

- [固定来源 31](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-Tensor.md)（constraint）

- [固定来源 32](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-Tensor.md)（constraint）

- [固定来源 33](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-Tensor.md)（constraint）

- [固定来源 34](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-Tensor.md)（constraint）

- [固定来源 35](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-Tensor.md)（constraint）

- [固定来源 36](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-Tensor.md)（constraint）

- [固定来源 37](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-Tensor.md)（constraint）

- [固定来源 38](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-Tensor.md)（constraint）

- [固定来源 39](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-Tensor.md)（constraint）

- [固定来源 40](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-Tensor.md)（primary）

- [固定来源 41](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-Tensor.md)（constraint）

- [固定来源 42](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-Tensor.md)（constraint）

- [固定来源 43](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch.md)（constraint）

- [固定来源 44](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch.md)（constraint）

- [固定来源 45](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch.md)（constraint）

- [固定来源 46](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch.md)（constraint）

- [固定来源 47](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch.md)（constraint）

- [固定来源 48](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch.md)（constraint）

- [固定来源 49](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch.md)（constraint）

- [固定来源 50](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch.md)（constraint）

- [固定来源 51](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch.md)（constraint）

- [固定来源 52](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch.md)（constraint）

- [固定来源 53](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch.md)（constraint）

- [固定来源 54](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch.md)（primary）

- [固定来源 55](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch.md)（constraint）

- [固定来源 56](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch.md)（constraint）

## _coalesce 与 to_padded_tensor 的实现层

本节把支持表行的两名（_coalesce、to_padded_tensor）核对到实现层，前文「Tensor稀疏查询与转换的独立范围」「嵌套张量的内部范围差异」的支持表结论保持不变。yaml 登记：`_coalesce` 仅 `sparse: [v2.1, newest]`（无 acl_op/op_api 段）；`to_padded_tensor` 仅 op_api [v2.1,newest] 且**只在主线注册、发布无该条目**（per_name 账本 main-only）。

`_coalesce` 不是单设备命令，而是 host 组合链（主线与发布两版本 语义等价，仅排版差异）：

1. 门槛：`TORCH_CHECK(!self.is_coalesced())`——**对已合并输入直接抛错**，不是幂等 no-op；nnz<2 时走 `self.clone()` + `_coalesced_(true)` 快捷返回，不下发命令。
2. 准备：`flatten_indices(indices, sizes, true)` 展平坐标后调 `at::_unique2(indices_1d, true, true)`（排序+return_inverse）；new_nnz 取唯一值长度；新坐标缓冲 `zeros({new_nnz, sparse_dim}, Int)`；原 indices 先 `transpose(0,1)`+`format_contiguous`+`to(Int)`。
3. 数值路径：**values 为 FP16/BF16 时先 `to(Float)` 执行 `aclnnCoalesceSparse` 再 `to` 回原 dtype**（FP32 往返，精度边界与 [损失/精度类卡](torch_npu_native_loss_constraints.md)的 FP16 转换提示同型）；其他 dtype 直接执行。
4. 返回：new_indices `transpose` 回并 `to(Long)`，`_sparse_coo_tensor_unsafe(...)._coalesced_(true)`。

该链路全程无 DO_COMPATIBILITY（直发 EXEC_NPU_CMD）；`at::_unique2` 会进入知识库已记录的 unique 调度（[unique 动态输出卡](torch_npu_unique_dynamic_output_and_sync.md)）。950DT deterministic 清单已列 Tensor.coalesce（见 [deterministic 卡](torch_npu_deterministic_algorithm_scope.md)），与本节静态阅读互补，不构成确定性结论。

`to_padded_tensor`（主线手写 opapi）直接 `return at::native::NestedTensor_to_padded_tensor_generic(self, padding, output_size)`——**纯 ATen 原生委托，无 aclnn 命令、无 DO_COMPATIBILITY**；其内部实现属 pytorch 仓，本卡未核对，不据此宣称嵌套张量其它操作或反向可用。发布版本 无该文件、无 yaml 条目：同一发布环境调用 to_padded_tensor 会落入框架默认分派，行为不在本节核对范围。

### _coalesce 与 to_padded_tensor 补充证据

- [SparseCoalesceKernelOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/sparse/SparseCoalesceKernelOpApi.cpp)（implementation）：1–78；完整本地小文件。
- [SparseCoalesceKernelOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/sparse/SparseCoalesceKernelOpApi.cpp)（implementation）：1–85；完整本地小文件，与主线仅排版差异。
- [NestedTensorToPaddedTensorKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NestedTensorToPaddedTensorKernelNpuOpApi.cpp)（implementation）：1–28；完整本地小文件，主线独有（发布无此文件）。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：1613–1614、5124–5126；仅 _coalesce 与 to_padded_tensor 两条 Schema（该文件已列于 frontmatter 来源）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：1554–1555；仅 _coalesce 一条 Schema，无 to_padded_tensor（该文件已列于 frontmatter 来源）。

## add.out/mul.out 的 sparse 标记实现层

本节核对g18账本中带`sparse:`登记标记的add.out/mul.out两名到实现层，上文_coalesce/to_padded_tensor补充小节保持不变。登记面（yaml原文）：主线`add.out`（927–931，`sparse: [v2.1, newest]`+acl_op/op_api all_version）、`mul.out`（3645–3648，同）；发布`add.out`（899–902）带sparse标记，**`mul.out`（3535–3538）无sparse标记**——这是pin差。生成链三段实读：`gen_op_plugin_functions.py`把`sparse`并入impl_ns（主线44–70/发布45–65，sparse→op_api）；op-plugin `torchnpugen/gen.py`为带标记Schema生成`<op>_sparse`包装（主线声明247–249、defn 404–408；发布247–249、388–393，包装体调用`sparse::<op>_sparse`）；pytorch fork `torchnpugen/gen_backend_stubs.py`以`gen_target_registration("sparse", DispatchKey.SparsePrivateUse1, ...)`注册到**SparsePrivateUse1分派键**（主线1799–1806、发布871–878）。sparse_csr注册组同样存在但主线与发布两版本 yaml无任何`sparse_csr`条目（全文rg零命中）。

`add_out_sparse`（SparseAddKernelOpApi.cpp，主线与发布两版本逻辑一致，发布仅少一行Intel版权头）分两条路：

- **dense+sparse**（`add_out_dense_sparse_npu`）：三个Tensor都必须是NPU；**尺寸相等硬门（不支持广播）**；`sparse._nnz()==0`时resize_as_+copy_快捷；`at::result_type`+`canCast`到out dtype；out dtype不符时先以common dtype建临时buffer；`is_same_tensor(r, dense_buffer)`时要求out连续（否则报"non-contiguous output tensor does not work"）；`flatten_indices`展平坐标后把r view成{rows, columns}（rows=前sparse_dim维乘积、columns=其余维乘积）、values reshape成{nnz, columns}，执行`r_view.index_add_(0, indices_1D, values, value)`再copy回——**全程无aclnn命令，host组合链**；index_add_的NPU消费面见[索引累加卡](torch_npu_indexed_add_buffer_preparation.md)。
- **sparse+sparse**（`add_out_sparse`）：self非稀疏时转投上条dense路；**add(sparse, dense)直接TORCH_CHECK硬拒**（报错提示改用add(dense, sparse)）；src._nnz()==0时`at::copy_sparse_to_sparse_`；**self._nnz()==0时直接委托`mul_out_sparse_scalar`**；`is_same_density`同密度硬门；indices按dim1、values按dim0**cat拼接——源码注释明示故意不合并（梯度累加场景换取免同步取nnz），结果非coalesced**；out dtype不符时构造promoted稀疏张量、coalesce后把values转回out dtype；末尾`r_._nnz() > r_.numel()`时再次coalesce并alias回。

`mul_out_sparse`（SparseTensorUtils.cpp 79–88）**主线独有**：TORCH_CHECK至少一个稀疏输入且out必须稀疏；sparse_dim取稀疏侧；**dense往返**——`at::mul(把稀疏侧to_dense化后与另一侧相乘)`得到稠密结果，再`copy_sparse_to_sparse_(out, dense_result.to_sparse(sparse_dim))`。**发布版本无此函数且yaml无标记**：发布环境稀疏mul.out落入框架默认分派，行为不在本卡核对范围。

`mul_out_sparse_scalar/zerodim`（主线与发布两版本）：value允许0维稀疏Tensor（其nnz==0时r.zero_()，否则取values）；r与t为同一Tensor时原地`_values().mul_(value_)`；否则resize_as_+indices copy_+`at::mul_out`写values+`set_nnz_and_narrow`+`_coalesced_(t.is_coalesced())`。

`flatten_indices_npu_kernel`（SparseTensorUtils.cpp 22–33，主线与发布两版本）：经`REGISTER_PRIVATEUSE1_DISPATCH(flatten_indices_stub, ...)`**覆盖ATen的flatten_indices分派**——先`zeros({indices.size(1)})`再逐稀疏维`tensor_temp += indices[i]*flatten_size[i]`的host触发设备加乘循环，无单条aclnn命令；影响所有经`at::sparse::flatten_indices`的NPU调用方（含上文_coalesce链，该节当时未记录此stub覆盖，以本节为准补充）。

边界与未确认：add.Tensor/mul.Tensor functional无sparse标记，其经ATen组合到out变体的路径未核对；`copy_sparse_to_sparse_`/`to_dense`/`to_sparse`/`alias_into_sparse`（set_indices_and_values_unsafe）属上游ATen/torch_npu实现，未核对不据以断言稀疏布局语义；`max_sparse/max_out_sparse`（主线与发布两版本，self.to_dense()后at::max/max_out委托）与max.out的sparse标记消费归[legacy min/max卡](../apis/torch_npu/legacy_min_max_and_sort.md)owner，本节不核对。

### add.out/mul.out sparse 标记补充证据

- [SparseAddKernelOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/sparse/SparseAddKernelOpApi.cpp)（primary）：27–177；add_out_dense_sparse_npu与add_out_sparse完整函数体。
- [SparseAddKernelOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/sparse/SparseAddKernelOpApi.cpp)（implementation）：27–176；与主线去空白字符流相同（仅Intel版权行差异）。
- [SparseTensorUtils.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/sparse/SparseTensorUtils.cpp)（primary）：21–98；flatten_indices_npu_kernel、mul_out_sparse_zerodim/scalar、mul_out_sparse（79–88主线独有）与PrivateUse1分派注册。
- [SparseTensorUtils.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/sparse/SparseTensorUtils.cpp)（implementation）：21–78；**无mul_out_sparse**（与主线79–88的pin差，`tr -d '[:space:]'`比对确认）。
- [SparseTensorUtils.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/sparse/SparseTensorUtils.h)（primary）：22–37；mul_out_sparse声明（发布对应40行无该声明）。
- [gen.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/gen.py)（primary）：247–249、404–408；`_sparse`包装声明与defn（发布dedc316对应247–249、388–393）。
- [gen_op_plugin_functions.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/gen_op_plugin_functions.py)（primary）：44–70；sparse→impl_ns归并（发布45–65）。
- [gen_backend_stubs.py ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torchnpugen/gen_backend_stubs.py)（primary）：1799–1806；`gen_target_registration("sparse", DispatchKey.SparsePrivateUse1, ...)`（发布f3ecfe4a对应871–878）。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（primary）：927–931、3645–3648；add.out/mul.out两条Schema（该文件已列于frontmatter来源）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：899–902、3535–3538；add.out带sparse标记、mul.out**无**sparse标记（发布侧pin差）。
- 负向证据：主线与发布两版本 yaml全文rg `sparse_csr` 零命中（注册组存在但无条目消费）；add.Tensor（主线922–925）、mul.Tensor（3641–3644）两条无sparse标记（逐字核对，仅out变体带标记）。
