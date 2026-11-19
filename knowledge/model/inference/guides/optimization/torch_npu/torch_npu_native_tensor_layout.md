---
type: Guide
title: 原生Tensor元数据：memory_format与NPU布局边界
description: 区分contiguous/preserve与不支持的channels_last，保留dtype/device/layout及finfo/iinfo/Size支持清单的粒度；并给出 tril/triu、fill_/zero_/fill_diagonal_、repeat 的实现层派发与宿主准备差异，以及工厂/创建 28 名（arange/eye/linspace/logspace.out/range/ones/zeros/stack/roll/flip/view_as_*）的手写 opapi、生成直发与 acl_op 回退差异。
tags:
- task.implementation
- topic.memory
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/Tensor-Attributes.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/Tensor-Attributes.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/Tensor-Attributes.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/Tensor-Attributes.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/Tensor-Attributes.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/Tensor-Attributes.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/Tensor-Attributes.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/Tensor-Attributes.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/Tensor-Attributes.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/Tensor-Attributes.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/Tensor-Attributes.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/Tensor-Attributes.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/Tensor-Attributes.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/Tensor-Attributes.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/Type-Info.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/Type-Info.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/Type-Info.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/Type-Info.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/Type-Info.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/Type-Info.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/Type-Info.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/Type-Info.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/Type-Info.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/Type-Info.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/Type-Info.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/Type-Info.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/Type-Info.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/Type-Info.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-Size.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-Size.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-Size.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-Size.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-Size.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-Size.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-Size.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/Named-Tensors.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/Named-Tensors.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/Named-Tensors.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/Named-Tensors.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/Named-Tensors.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/Named-Tensors.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/Named-Tensors.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/Named-Tensors.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/Named-Tensors.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/Named-Tensors.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-utils-dlpack.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-utils-dlpack.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-utils-dlpack.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-utils-dlpack.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-utils-dlpack.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-utils-dlpack.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-utils-dlpack.md
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
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/private_apis.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/private_apis.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/troubleshooting_cases/nz_format_precision_issue.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_broadcast.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_format_cast.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_format_cast.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_format_cast.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_format_cast_.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_format_cast_.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_format_cast_.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_reshape.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_transpose.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_transpose.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_transpose.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/FormatCastKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/FormatCastKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/FormatCastHelper.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/FormatCastHelper.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ReshapeKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ReshapeKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UnfoldBackwardLernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UnfoldBackwardLernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/TrilKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/TrilKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/TriuKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/TriuKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/FillKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/FillKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/FillDiagonalKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/FillDiagonalKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RepeatKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/RepeatKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ZerosLikeKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ZerosLikeKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FillKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FillKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ZerosLikeKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ZerosLikeKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ArangeKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ArangeKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/EyeKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/EyeKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LinspaceKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LinspaceKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LogSpaceKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LogSpaceKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/OnesKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/OnesKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RangeKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RangeKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ZerosKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ZerosKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/OnesLikeKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/OnesLikeKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ViesAsRealKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ViesAsRealKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ArangeKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ArangeKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/EyeKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/EyeKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LinspaceKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LinspaceKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogSpaceKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LogSpaceKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/OnesKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/OnesKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RangeKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/RangeKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ZerosKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ZerosKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/OnesLikeKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/OnesLikeKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/FlipKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/FlipKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RollKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/RollKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/StackKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/StackKernelNpu.cpp
  role: implementation
created_at: '2026-11-09T12:28:09Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 原生Tensor元数据：memory_format与NPU布局边界

## 固定来源与范围

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的PyTorch2.7.1、2.9至2.14支持页；七版本及实际存在的中英文页分别审阅，不回推26.0/PyTorch2.8发布组合，也不将950DT扩为950PR。文档未收录的接口/产品只表示此清单未验证；支持条目不是完整社区参数手册。仅静态审阅，未执行上游、设备或性能实验。

## memory_format的实际限制

Tensor Attributes的中英文七版本页均列torch.memory_format支持A2/A3训练系列及950DT，但正文明确NPU仅支持torch.contiguous_format与torch.preserve_format；channels_last和channels_last_3d不支持。preserve_format用于clone/empty_like等保留输入布局，不用于torch.empty()。

类/枚举本身的支持不等于所有枚举值可用；不能因为卷积融合或convert_conv2d/3d_weight_memory_format工具出现在支持表，就认定NPU已经支持channels_last。转换工具的清单没有另给完整格式矩阵，按[卷积指南](../../../../training/guides/torch_npu_native_convolution_constraints.md)与本条限制分别消费。

## 元数据与具体运算分开

torch.dtype、torch.device、torch.layout，以及Type Info的torch.finfo/iinfo，均在实际存在的中英文页列三类产品支持，但没有说明每一种dtype/layout都能用于每个算子。torch.Size在七份中文页列三类产品；该路径未提供对应英文Size页，不制造不存在的语言来源。

类型对象、类型信息或shape可查询，不证明FP64/复数、稀疏格式、任意stride与所有算子/图后端组合均受支持，也不证明更改布局一定零拷贝或更快。实际格式编号、私有存储与memory_format枚举不能只凭名字互换。

## 核对方法

保存实际shape、dtype、device、stride、内存格式与存储，分别核对分配、clone/empty_like、消费者和反向。检查布局及数值后，再比较转换成本、峰值内存和端到端耗时；不能仅凭格式转换工具调用成功判断性能收益。

## 旧版具名Tensor与DLPack的独立清单

Named-Tensors页仅在同提交2.7.1、2.9..2.12中英文存在；该页的torch.Tensor条目及names/rename/rename_/align_to/refine_names/align_as都限定self FP32，中文只列A2/A3、英文明确950DT不支持。flatten却单独列三类产品且self FP32。这里的Tensor类是具名张量页面局部范围，不是所有普通torch.Tensor都只支持FP32或不支持950；新页缺项也不直接证明运行时删除具名功能。

七份英文utils.dlpack页对from_dlpack/to_dlpack明确三类均不支持，没有对应中文页；不要由Storage、底层指针或普通Tensor转换支持，推导这两个公开入口的零拷贝交换已可用。来源没有给跨库胶囊、所有权、流同步与销毁协议，不据“DLPack”名称生成已验证共享方案；本文未创建胶囊或访问活跃地址。

## 七版本Tensor方法的几何和类型表

以下表按同提交2.14 Tensor页面列self范围；除T/t中文仅A2/A3、英文明确950不支持外，已列几何方法的产品表列三产品，具体限制仍单独适用。H/mT/mH/adjoint不能由T/t的较窄范围一并排除；也不从转置支持推导布局、别名和零拷贝协议。

## 方法级self类型

| 方法/属性 | self类型范围 | 来源 |
| --- | --- | --- |
| `torch.Tensor.broadcast_to` | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.t_` | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64 | 中英文 |
| `torch.Tensor.T`、`torch.Tensor.as_strided`、`torch.Tensor.chunk`、`torch.Tensor.clone`、`torch.Tensor.conj`、`torch.Tensor.copy_`、`torch.Tensor.diagonal`、`torch.Tensor.expand`、`torch.Tensor.expand_as`、`torch.Tensor.flatten`、`torch.Tensor.narrow`、`torch.Tensor.permute`、`torch.Tensor.ravel`、`torch.Tensor.reshape`、`torch.Tensor.reshape_as`、`torch.Tensor.select`、`torch.Tensor.split`、`torch.Tensor.squeeze`、`torch.Tensor.swapaxes`、`torch.Tensor.tile`、`torch.Tensor.transpose`、`torch.Tensor.transpose_`、`torch.Tensor.unbind`、`torch.Tensor.unflatten`、`torch.Tensor.unsqueeze`、`torch.Tensor.view`、`torch.Tensor.view_as`、`torch.Tensor.where` | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.t` | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.diagonal_scatter` | BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.contiguous`、`torch.Tensor.resize_` | BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.fill_diagonal_` | FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.repeat_interleave` | FP16/FP32/INT16/INT32/BOOL | 中英文 |
| `torch.Tensor.roll` | FP16/FP32/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.diag_embed`、`torch.Tensor.select_scatter`、`torch.Tensor.slice_scatter`、`torch.Tensor.unfold` | FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.diag`、`torch.Tensor.diagflat` | FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64 | 中英文 |
| `torch.Tensor.flip`、`torch.Tensor.fliplr`、`torch.Tensor.flipud`、`torch.Tensor.hsplit`、`torch.Tensor.moveaxis`、`torch.Tensor.movedim`、`torch.Tensor.narrow_copy`、`torch.Tensor.repeat`、`torch.Tensor.resize_as_`、`torch.Tensor.resolve_conj`、`torch.Tensor.resolve_neg`、`torch.Tensor.rot90`、`torch.Tensor.swapdims`、`torch.Tensor.vsplit` | FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.squeeze_`、`torch.Tensor.unsqueeze_` | FP32 | 中英文 |
| `torch.Tensor.H`、`torch.Tensor.adjoint`、`torch.Tensor.mH`、`torch.Tensor.mT`、`torch.Tensor.tensor_split` | 未给独立self类型表 | 中英文 |
| `torch.Tensor.dsplit` | 未给独立self类型表 | 中英文；英文self为FP32 |

## 较早版本的不同类型表

| 方法 | 文档版本 | 当时self表 | 2.14 self表 | 来源 |
| --- | --- | --- | --- | --- |
| `torch.Tensor.where` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.repeat` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.repeat_interleave` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | FP16/FP32/INT16/INT32/BOOL | 中英文 |
| `torch.Tensor.roll` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/UINT8/INT8/INT32/INT64/BOOL | FP16/FP32/INT32/INT64/BOOL | 中英文 |

dsplit中文只有产品表、英文另写self FP32，保留语言差异。copy_的INT16维度限制中文写“不支持5维以上”，英文写“5 or more dimensions”（大于等于5维）；保留两侧原文，不自行放宽成5维可用。contiguous/resize_的self不列FP64，resize_as_还不列BF16，不能相互代填；resize_/resize_as_的memory_format只允许torch.contiguous_format或torch.preserve_format。

tensor_split明确仅CPU支持；select_scatter可能CPU回退。tile会在dims前补1：若第一个维度参与重复，则dims中大于1的元素数不得超过4，否则不得超过3；反向时Tensor维度数与dims中大于1的元素数之和不得超过8。repeat_interleave输出元素数必须小于2^22。

Tensor.cumsum/matmul支持具名Tensor的局部说明，不扩大上节旧Named-Tensors页面的A2/A3和FP32范围。更多创建、转换、地址与流属性见[Tensor转换指南](torch_npu_native_tensor_conversion_scope.md)。

## torch函数的布局表与Tensor方法分开

同提交torch页下列函数产品表列三产品，from_dlpack除外：英文七版本明确三产品均不支持、中文未收录。它与前节utils.dlpack入口分别记录，不能据from_numpy/frombuffer支持推导DLPack可用。

## 函数级参数类型

| 函数/对象 | 局部参数类型表 | 来源 |
| --- | --- | --- |
| `torch.broadcast_to`、`torch.narrow_copy`、`torch.slice_scatter`、`torch.swapaxes`、`torch.swapdims`、`torch.t`、`torch.where` | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.chunk`、`torch.clone`、`torch.diag_embed`、`torch.flatten`、`torch.movedim`、`torch.narrow`、`torch.permute`、`torch.reshape`、`torch.split`、`torch.squeeze`、`torch.tensor_split`、`torch.tile`、`torch.transpose`、`torch.unsqueeze` | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.diagonal_scatter` | input=BF16/FP16/FP32/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.conj`、`torch.select_scatter`、`torch.tril`、`torch.triu` | input=BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.diagonal`、`torch.dsplit`、`torch.hsplit`、`torch.ravel`、`torch.resolve_neg`、`torch.vsplit` | input=BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.view_as_real` | input=COMPLEX64/COMPLEX128 | 中英文 |
| `torch.resolve_conj` | input=FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.repeat_interleave` | input=FP16/FP32/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.roll` | input=FP16/FP32/INT32/INT64/BOOL | 中英文 |
| `torch.diag` | input=FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64 | 中英文 |
| `torch.flip`、`torch.fliplr`、`torch.flipud` | input=FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.view_as_complex` | input=FP32/FP64 | 中英文 |
| `torch.moveaxis` | input=FP32/INT64/COMPLEX128 | 中英文 |
| `torch.as_strided` | input=FP32 | 中英文 |
| `torch.cat`、`torch.stack` | tensors=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.concat`、`torch.hstack`、`torch.vstack` | tensors=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64 | 中英文 |
| `torch.atleast_1d`、`torch.broadcast_tensors`、`torch.cartesian_prod`、`torch.meshgrid` | tensors=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.concatenate` | tensors=BF16/FP16/FP32/INT64/BOOL/COMPLEX64 | 中英文 |
| `torch.dstack`、`torch.row_stack` | tensors=BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64 | 中英文 |
| `torch.block_diag` | tensors=BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.atleast_2d`、`torch.atleast_3d` | tensors=FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.broadcast_shapes`、`torch.tril_indices`、`torch.triu_indices`、`torch.unflatten` | 未给独立参数类型表 | 中英文 |
| `torch.adjoint`、`torch.column_stack`、`torch.diagflat`、`torch.rot90`、`torch.select`、`torch.unbind` | 未给独立参数类型表 | 仅中文 |
| `torch.from_dlpack` | 未给独立参数类型表 | 仅英文 |

## 较早版本的不同参数表

| 函数/对象 | 文档版本 | 当时参数表 | 2.14参数表 | 来源 |
| --- | --- | --- | --- | --- |
| `torch.tril`、`torch.triu` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | input=BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.repeat_interleave` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | input=FP16/FP32/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.roll` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/UINT8/INT8/INT32/INT64/BOOL | input=FP16/FP32/INT32/INT64/BOOL | 中英文 |

## 文档收录版本与语言

| 函数/对象 | 中文收录版本 | 英文收录版本 |
| --- | --- | --- |
| `torch.adjoint`、`torch.column_stack`、`torch.diagflat`、`torch.rot90`、`torch.select`、`torch.unbind` | 2.10.0、2.11.0、2.12.0、2.13.0、2.14.0、2.7.1、2.9.0 | 未收录 |
| `torch.from_dlpack` | 未收录 | 2.10.0、2.11.0、2.12.0、2.13.0、2.14.0、2.7.1、2.9.0 |

concat的950DT说明排除COMPLEX64，concatenate排除complex，不用其通用类型表覆盖产品局部例外。where不支持8维shape。narrow_copy可能CPU回退；torch.tensor_split只有产品及input表，没有Tensor.tensor_split的“仅CPU”说明，不自动继承方法限制。

torch.tile先向dims前补1；首轴重复时dims中大于1的元素数最多4，不重复时最多3；反向时输入Tensor维度数加dims中大于1的元素数不得超过8。torch.repeat_interleave输出元素数必须小于2^22，局部input含INT64，与Tensor方法表不同。

## 私有复制与分块入口

private_apis对torch._chunk_cat列BF16/FP16/FP32，对torch.split_with_sizes_copy列FP16/FP32、UINT8、INT8/16/32/64、BOOL，两侧均列三产品。torch.ops.aten._to_copy.default和torch._foreach_copy_列BF16/FP16/FP32/FP64、UINT8、INT8/16/32/64、BOOL、COMPLEX64/128；前者列三产品，后者两侧明确950暂不支持。

原文说“支持”而未分参数，不改成完整参数/输出表。_to_copy.default不与Tensor.copy_、Tensor.to或foreach复制视为同一存储协议；私有复制的产品表也不由入图清单的收录覆盖。该页未特别注明的接口按自身版本口径处理，不证明任意安装版本可互换。

## NZ精度案例同时改变dtype与格式

同提交中文故障页介绍allow_internal_format默认False时的隐式NZ→ND路径及开启后可能走不同数值路径，建议显式转ND或保持关闭。它是故障场景描述，没有整套产品矩阵，不能据此推定每个算子、输入或950组合都具备同样转换行为；NZ白名单路由还按[框架适配草稿](torch_npu_opplugin_adaptation.md)分别核对。

示例input_tensor.float().npu_format_cast(2)同时转FP32和ND，不能把输出改善全部归因于布局，或机械要求所有低精度业务先升FP32。格式编号、dtype与逻辑permute继续分开；按同dtype对照才能独立分析布局影响。固定发布版[npu_format_cast接口](../../../apis/torch_npu/npu_format_cast.md)的产品和新Tensor语义仍按其自身来源，本主线案例不扩大该API卡的发布范围。

## 旧自定义接口的分配与物理布局

[格式转换](../../../apis/torch_npu/npu_format_cast.md)同格式可能返回self、base格式之间可能只修改存储描述，原地Tensor-src重载还含数据写回，不能按名字推断新对象或纯模板转换。[旧形状变换](../../../apis/torch_npu/legacy_shape_transforms.md)的broadcast/transpose实际分配输出，reshape的can_refresh=True也不能当普通view别名保证。逻辑shape、物理格式、对象/存储别名及消费者限制需要分别核对。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/Tensor-Attributes.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/Tensor-Attributes.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/Tensor-Attributes.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/Tensor-Attributes.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/Tensor-Attributes.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/Tensor-Attributes.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/Tensor-Attributes.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/Tensor-Attributes.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/Tensor-Attributes.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/Tensor-Attributes.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/Tensor-Attributes.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/Tensor-Attributes.md)（primary）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/Tensor-Attributes.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/Tensor-Attributes.md)（constraint）
- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/Type-Info.md)（constraint）
- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/Type-Info.md)（constraint）
- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/Type-Info.md)（constraint）
- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/Type-Info.md)（constraint）
- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/Type-Info.md)（constraint）
- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/Type-Info.md)（constraint）
- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/Type-Info.md)（constraint）
- [固定来源 22](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/Type-Info.md)（constraint）
- [固定来源 23](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/Type-Info.md)（constraint）
- [固定来源 24](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/Type-Info.md)（constraint）
- [固定来源 25](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/Type-Info.md)（constraint）
- [固定来源 26](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/Type-Info.md)（primary）
- [固定来源 27](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/Type-Info.md)（constraint）
- [固定来源 28](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/Type-Info.md)（constraint）
- [固定来源 29](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-Size.md)（constraint）
- [固定来源 30](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-Size.md)（constraint）
- [固定来源 31](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-Size.md)（constraint）
- [固定来源 32](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-Size.md)（constraint）
- [固定来源 33](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-Size.md)（primary）
- [固定来源 34](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-Size.md)（constraint）
- [固定来源 35](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-Size.md)（constraint）

- [固定来源 36](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/Named-Tensors.md)（constraint）

- [固定来源 37](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/Named-Tensors.md)（constraint）

- [固定来源 38](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/Named-Tensors.md)（constraint）

- [固定来源 39](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/Named-Tensors.md)（constraint）

- [固定来源 40](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/Named-Tensors.md)（constraint）

- [固定来源 41](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/Named-Tensors.md)（constraint）

- [固定来源 42](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/Named-Tensors.md)（constraint）

- [固定来源 43](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/Named-Tensors.md)（constraint）

- [固定来源 44](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/Named-Tensors.md)（constraint）

- [固定来源 45](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/Named-Tensors.md)（constraint）

- [固定来源 46](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-utils-dlpack.md)（constraint）

- [固定来源 47](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-utils-dlpack.md)（constraint）

- [固定来源 48](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-utils-dlpack.md)（constraint）

- [固定来源 49](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-utils-dlpack.md)（constraint）

- [固定来源 50](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-utils-dlpack.md)（constraint）

- [固定来源 51](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-utils-dlpack.md)（constraint）

- [固定来源 52](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-utils-dlpack.md)（constraint）

- [固定来源 53](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-Tensor.md)（constraint）

- [固定来源 54](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-Tensor.md)（constraint）

- [固定来源 55](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-Tensor.md)（constraint）

- [固定来源 56](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-Tensor.md)（constraint）

- [固定来源 57](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-Tensor.md)（constraint）

- [固定来源 58](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-Tensor.md)（constraint）

- [固定来源 59](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-Tensor.md)（constraint）

- [固定来源 60](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-Tensor.md)（constraint）

- [固定来源 61](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-Tensor.md)（constraint）

- [固定来源 62](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-Tensor.md)（constraint）

- [固定来源 63](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-Tensor.md)（constraint）

- [固定来源 64](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-Tensor.md)（primary）

- [固定来源 65](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-Tensor.md)（constraint）

- [固定来源 66](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-Tensor.md)（constraint）

- [固定来源 67](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch.md)（constraint）

- [固定来源 68](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch.md)（constraint）

- [固定来源 69](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch.md)（constraint）

- [固定来源 70](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch.md)（constraint）

- [固定来源 71](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch.md)（constraint）

- [固定来源 72](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch.md)（constraint）

- [固定来源 73](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch.md)（constraint）

- [固定来源 74](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch.md)（constraint）

- [固定来源 75](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch.md)（constraint）

- [固定来源 76](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch.md)（constraint）

- [固定来源 77](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch.md)（constraint）

- [固定来源 78](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch.md)（primary）

- [固定来源 79](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch.md)（constraint）

- [固定来源 80](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch.md)（constraint）

- [固定来源 81](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/private_apis.md)（primary）

- [固定来源 82](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/private_apis.md)（constraint）

- [固定来源 83](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/troubleshooting_cases/nz_format_precision_issue.md)（primary）

- [固定来源 84](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_broadcast.md)（primary）

- [固定来源 85](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_format_cast.md)（constraint）

- [固定来源 86](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_format_cast.md)（primary）

- [固定来源 87](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_format_cast.md)（constraint）

- [固定来源 88](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_format_cast_.md)（constraint）

- [固定来源 89](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_format_cast_.md)（primary）

- [固定来源 90](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_format_cast_.md)（constraint）

- [固定来源 91](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_reshape.md)（primary）

- [固定来源 92](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_transpose.md)（constraint）

- [固定来源 93](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_transpose.md)（primary）

- [固定来源 94](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_transpose.md)（constraint）

- [固定来源 95](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/FormatCastKernelNpu.cpp)（implementation）

- [固定来源 96](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/FormatCastKernelNpu.cpp)（implementation）

- [固定来源 97](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/FormatCastHelper.cpp)（implementation）

- [固定来源 98](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/FormatCastHelper.cpp)（implementation）

- [固定来源 99](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ReshapeKernelNpuOpApi.cpp)（implementation）

- [固定来源 100](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ReshapeKernelNpuOpApi.cpp)（implementation）

## Tensor.unfold反向的CPU门控与空结果差异

这里是aten::unfold_backward的本地包装，使用Tensor窗口的input_sizes/dim/size/step；不把nn.Unfold的patch/im2col合同或产品表直接套到该内部入口。

两版静态缓存三项条件：aclnnUnfoldGrad及其GetWorkspaceSize双符号可见；SoC枚举满足`[Ascend910B1, Ascend310B1)`或`>=Ascend910_9391`；调用CANN `"8.3.RC1"`版本比较helper得到真。任意条件失败就WARN_ONCE，将grad_in.cpu后调用CPU unfold_backward，再把结果to(grad_in.device)。这里没有统一Float转换，也没有用普通兼容宏的AclnnOnly分支阻止CPU路线。

NPU路线将input_sizes拷成输出shape，按grad_in dtype/options申请结果再调用aclnnUnfoldGrad。主线在申请后检查out.numel()==0并直接返回；发布没有这个早退。**CPU选择在该空判之前**，不能据主线空结果早退断言任何环境中的空输入都不做CPU准备。

本地没有再验证窗口size/step、input_sizes和grad布局的全部关系，不能把输出申请等同完整支持校验。固定主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`与发布`dedc316708372c9a8bfde4527abd2a94b74840f5`只读审阅，未执行复制、梯度或设备实验；其余原布局知识保持原范围。

### unfold_backward补充证据

- [UnfoldBackwardLernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UnfoldBackwardLernelNpuOpApi.cpp)（implementation）：1–50；完整本地小文件。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：5567–5568；仅unfold_backward Schema。
- [OpUtils.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）：474–478；仅CANN版本helper。
- [op_api_common.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp)（implementation）：767–773；仅双符号探测helper。
- [UnfoldBackwardLernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UnfoldBackwardLernelNpuOpApi.cpp)（implementation）：1–42；完整本地小文件。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：5395–5396；仅unfold_backward Schema。
- [OpUtils.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp)（implementation）：430–434；仅CANN版本helper。
- [op_api_common.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.cpp)（implementation）：785–792；仅双符号探测helper。

## 三角屏蔽、填充初始化与 repeat 的实现层派发

本节闭合视图/创建/形状主题级中此前只有支持表行的 11 名：tril/tril.out/tril_、triu/triu.out/triu_、fill_.Scalar/fill_.Tensor、zero_、fill_diagonal_、repeat。所有结论为两 pin 静态阅读；上层支持表的 dtype 行保持原范围。yaml 登记：tril/triu 族 acl_op+op_api all_version、gen_opapi out size/dtype=self、exec aclnnTril/aclnnTriu（原地 aclnnInplaceTril/aclnnInplaceTriu）；fill_diagonal_ exec aclnnInplaceFillDiagonal；repeat acl_op+op_api [v2.1,newest]、out size=`repeat_npu_output_size(self,repeats)`、dtype=self、exec aclnnRepeat；fill_.Scalar/fill_.Tensor 与 zero_ **无 gen_opapi 段**——opapi 侧为手写包装（见下）。

| 入口 | 门槛与动作 | 边界 |
| --- | --- | --- |
| tril（functional） | 先经 NPUBridge 读 storage_sizes 做「last two dims」检查（storage 维数≤1 抛错），再 `apply_tensor(self)`+OpCommand "Tril" | **秩检查只在 functional**；tril_/tril_out（CheckOut({self},result,self)+格式分支）无此检查，同一张量 1 维时 functional 报错而原地/ out 路不拦 |
| triu 全族 | 无秩检查；functional `apply_tensor(self)`，out/原地 CheckOut+格式分支，OpCommand "Triu" | tril/triu 的 gen 直发路径均为 size/dtype=self 的 aclnnTri*，包装内的秩/格式检查不在生成路径中 |
| fill_.Scalar（手写 opapi） | DO_COMPATIBILITY(aclnnInplaceFillScalar)→EXEC aclnnInplaceFillScalar | 无本地格式分支 |
| fill_.Tensor（手写 opapi） | 双 DO_COMPATIBILITY(aclnnInplaceFillScalar/aclnnInplaceFillTensor)；`IsCPUScalar(other)` 为真时先 `other.item()` 走 aclnnInplaceFillScalar，否则 aclnnInplaceFillTensor | 第 4 个已核的手写 IsCPUScalar 实例（前 3 例与机制见 [动态选择与 Where 卡](../../../../training/guides/torch_npu_dynamic_selection_sync_and_where_scalar_execution.md) 增补小节；masked_fill_ Tensor 重载见 index_put 卡） |
| fill_（aclops 回退） | Tensor 重载先 TORCH_CHECK value.dim()≤1、`CheckMemory({self,value},{self})`；「Fill」OpCommand 把 self.sizes() 作为 Long 输入（0 维 self 用 {1}），Scalar 值以 MEMORY_HOST_COMPILE_INDEPENDENT 传入；内部同文件复用 IsCPUScalar→item() 分支 | 与手写 opapi 的差异：回退路有 CheckMemory 与格式分支（check_match/format_contiguous/format_fresh_view） |
| zero_（手写 opapi 位于 ZerosLikeKernelNpuOpApi.cpp） | DO_COMPATIBILITY(aclnnInplaceZero)→EXEC aclnnInplaceZero | 回退 acl_op::zero_ 用 OpCommand "ZerosLike"（self 同时作输入与输出）；zeros 工厂经 `out.zero_()` 复用该入口（ZerosKernelNpu.cpp），工厂语义不在本节单独闭合 |
| fill_diagonal_ | aclops 先 `CastBackToOriFormat(self)`（其他入口未见该调用），fill_value 经 get_scalar_float_value 收窄 float，OpCommand "FillDiagonal" attrs fill_value/wrap | gen 直发 aclnnInplaceFillDiagonal；「wrap 模式下对角填充的完整行为」未在本节展开 |
| repeat | aclops：TORCH_CHECK repeats.size()≥self.ndimension()；repeats 更长时 host 逐维 unsqueeze 到前部；output_size=`repeat_npu_output_size(self_cp,repeats)`（前补 1 后逐维相乘）；OpCommand "Tile" 以 repeats 为 Input | gen 直发路径 yaml 引用 `repeat_npu_output_size(self, repeats)`：helper 自身对 repeats 短于 self 维数的情形先按负数差值构造（上游 host 检查在 aclops 包装内），两路径对 repeats 短于维数的输入都未在源内证明可用 |

两 pin 差异如实：本节 aclops/opapi 文件全部语义等价（Tril/Triu/Repeat/ZerosLike 系列仅排版差异，Fill/FillDiagonal/FillOpapi/ZerosLikeOpapi 去空白 token 流相同）；yaml 条目同语义（release 缺主线 repeat 条目的行号偏移）。设备侧 aclnnTril/Triu/Fill/FillDiagonal/Zero/Repeat/Tile 内核与 _npu 布局后端细节不在本节来源范围；`CastBackToOriFormat` 的格式恢复语义在 torch_npu OpPreparation，本节只记录调用位置。

### 三角屏蔽与填充初始化证据

- [TrilKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/TrilKernelNpu.cpp)（implementation）：1–66；完整本地小文件。
- [TrilKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/TrilKernelNpu.cpp)（implementation）：1–77；仅排版差异。
- [TriuKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/TriuKernelNpu.cpp)（implementation）：1–52；完整本地小文件。
- [TriuKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/TriuKernelNpu.cpp)（implementation）：1–63；仅排版差异。
- [FillKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/FillKernelNpu.cpp)（implementation）：1–94；完整本地小文件。
- [FillKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/FillKernelNpu.cpp)（implementation）：1–94；与主线去空白 token 流相同。
- [FillDiagonalKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/FillDiagonalKernelNpu.cpp)（implementation）：1–56；完整本地小文件。
- [FillDiagonalKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/FillDiagonalKernelNpu.cpp)（implementation）：1–56；与主线去空白 token 流相同。
- [RepeatKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RepeatKernelNpu.cpp)（implementation）：1–51；完整本地小文件。
- [RepeatKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/RepeatKernelNpu.cpp)（implementation）：1–59；仅排版差异。
- [ZerosLikeKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ZerosLikeKernelNpu.cpp)（implementation）：17–46；zero_ 实现段（文件其余为 zeros_like，未展开）。
- [ZerosLikeKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ZerosLikeKernelNpu.cpp)（implementation）：17–47；zero_ 实现段，仅排版差异。
- [FillKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FillKernelNpuOpApi.cpp)（implementation）：1–42；完整本地小文件。
- [FillKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FillKernelNpuOpApi.cpp)（implementation）：1–40；仅排版差异。
- [ZerosLikeKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ZerosLikeKernelNpuOpApi.cpp)（implementation）：17–30；zero_ 手写包装段（文件其余为 zeros_like，未展开）。
- [ZerosLikeKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ZerosLikeKernelNpuOpApi.cpp)（implementation）：17–30；同段，仅排版差异。
- [KernelNpuOutputSize.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1344–1358；仅 repeat_npu_output_size helper。
- [KernelNpuOutputSize.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1191–1204；同 helper，语义相同。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：2264–2275、4266–4272、5158–5200、5524–5527；仅本节 11 名 Schema 条目（该文件已列于 frontmatter 来源）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：2197–2210、4151–4157、4992–5036、5355–5358；同 11 名条目（该文件已列于 frontmatter 来源）。

## 工厂/创建 28 名的实现层：手写 opapi、生成直发与 acl_op 回退

本节闭合视图/创建/形状主题支持表 28 名（arange×5、eye×4、linspace×2、logspace.out、range×3、ones×4、zeros×3、stack×2、roll、flip、view_as_real、view_as_complex）到实现层；前文支持表的 dtype/产品行保持原范围。除 flip/stack/roll 外均无 gen_opapi 段——手写 opapi 文件承接 op_api 分派；flip/stack/roll 为 gen 直发规格。所有结论为两 pin 静态阅读。

| 家族 | op_api 路径（手写或 gen） | acl_op 回退（aclops） |
| --- | --- | --- |
| arange 5 名 | 手写：AT_DISPATCH_ALL_TYPES_AND2(Half,BFloat16) host 校验（step 非零、start/end isfinite、方向与 step 符号一致）；**缺省 dtype 且三个标量全整型→Long**；长度 `infersize_arange`；`arange_out` numel 不匹配时 **TORCH_WARN+resize_（非空 out 也被重设尺寸，不抛错）**；start/start_step 以 step=1/start=0 委托 | "Range" 命令：start/end/step 以 `MEMORY_HOST_COMPILE_DEPENDENT` 标量输入；**start==end 提前返回 {0} 空 tensor**（opapi 路无该特例）；**Half/BFloat16 先按 Float 申请执行再 `.to(dtype)`**（opapi 路直接按 option dtype 申请）；arange_out 同样 WARN+resize_+格式分支 |
| eye 4 名 | 手写：TORCH_CHECK n/m≥0（四个入口都有）；out `resize_({n,n})`/`({n,m})` 后 EXEC aclnnEye；functional `apply_tensor_without_format` | **"Eye" 命令无 Tensor 输入**（num_rows/num_columns/dtype 全为 attr）；**Bool 结果先 `_npu_dtype_cast` 到 Int 执行再转回（out 变体额外 `copy_`）**；**n≥0 检查只在 eye_out**（functional 无）；`eye_out(n)` 委托 `(n,-1)`，m<0 时取 m=n |
| linspace 2 名 | 手写：TORCH_CHECK steps≥0；out numel!=steps **静默 resize_（无警告）**；EXEC aclnnLinspace | **steps==1 走 `acl_op::fill_(result,start)`（换命令）**；steps==0 不下发任何命令；**非 Float dtype 先 cast Float 执行再转回（out 变体 copy_）**；"LinSpace" 命令 start/end 以 Float 标量输入、steps 以 Int 输入 |
| logspace.out（仅 out 变体注册） | **yaml 两 pin 都只登记 out 变体（无 functional 条目）**；手写：steps≥0 检查+resize_+check_match/format 分支+非 1d 先 `view({steps})`；base≤0 且 start/end 非整型时 TORCH_NPU_WARN（警告非错误）；aclnnLogSpace | **dtype 白名单 TORCH_CHECK（仅 Float/Half，其他抛错）**；先用 `at::arange(0,steps)`（递归进入 acl_op arange）构造 assistant 输入（Half 再 cast）；"LogSpaceD" 命令 + start/end/steps/base/dtype attr |
| range 3 名 | 手写：isfinite 检查；长度 `(end-start)/step+1` 按 acc_type 计算后静态截断；`range_out` 对 result dtype 做 TORCH_CHECK——**主线 `isIntegralType(res_type,false)`（排除 Bool）、发布 `isIntegralType(res_type)`（默认含 Bool）**，Bool out 两 pin 接受度不同；`check_tensor({},result,res_type,result.sizes())`；numel 不匹配 TORCH_NPU_WARN+resize_ | **host 构造 0..size-1 的 tmp_vector 作输入**；"RangeD" 命令（start/limit/delta attr）；结果按 **ACL_FORMAT_NCHW** 申请；range functional 委托 `at::range(start,end,1,option)`；range_out CheckOut({},out,NCHW,…)+WARN+resize_+格式分支 |
| ones 4 名（ones/ones.names/ones.out/ones_like） | 手写 ones/ones_out：DO_COMPATIBILITY(aclnnInplaceOne)+`apply_tensor_without_format`+EXEC aclnnInplaceOne；ones_like：**非 NPU device → `at::empty_like`+`fill_(1)`**；NPU → `self.options()` 与显式选项 merge（缺省 dtype 取 self）后申请+aclnnInplaceOne+propagate_names。**ones.names 的 `#if !VERSION_BETWEEN(V2R13,VERSION_NEWEST)` 守卫与 yaml [v2.1,v2.12] 配套；发布 pin 无该 #if 且 yaml 登记为 all_version** | ones 系全部委托 `acl_op::one_`（"OnesLike" 命令+格式分支）；ones_like 非 NPU 分支与 opapi 相同，NPU 分支 `apply_tensor(self,option)` 后走 one_ |
| zeros 3 名 | 手写：DO_COMPATIBILITY(aclnnInplaceZero)+`apply_tensor_without_format` 后 **`result.zero_()`**（复用前文 zero_ 链）；zeros.names 的 #if 守卫/两 pin 差异与 ones.names 同型；symint 段另登记 zeros(SymInt[]) **仅 acl_op [v2.1,newest]** | `zeros_out`=resize_+`out.zero_()`；zeros 系委托 `zeros_common_nocheck`（inner_compute） |
| stack 2 名 | **gen 直发**：out size=`stack_output_size(tensors,dim)`、exec aclnnStack；gen dtype 两 pin 仅 **stack.out** 有差——`at::native::result_type(tensors)`（**主线**）/`tensors[0]`（**发布**），functional stack 两 pin 同为 `at::native::result_type(tensors)`——混合 dtype 堆叠的 out dtype 判定仅 stack.out 两 pin 不同 | "Pack" 命令：逐 tensor 以 x0..xN 命名输入+N/axis attr；CheckOut dtype 模板同为 result_type（主线）/tensors[0]（发布）；functional `apply_tensor_with_format(…,ACL_FORMAT_ND)` 按 tensors[0].options() |
| roll | **gen 直发**：yaml 以 `grad_input:` 键（非 out）注 size/dtype=self，exec aclnnRoll | "Roll" 命令（dims 为空时整卷）；**dims 非空时逐轴 `npu_transpose`→单轴 Roll→transpose 回**的组合（首轴==0 时直接 Roll）；shifts/dims 长度一致 TORCH_CHECK |
| flip | **gen 直发**：out size/dtype=self，exec aclnnFlip | **dims 为空时 `self.clone()` 直返（不下发命令）**；否则 "ReverseV2" 命令、dims 以 Long 输入 |
| view_as_real / view_as_complex | **op_api only（yaml 无 acl_op 行，另有 internal_format_opapi: all_version 标记）；手写文件纯委托 `at::native::view_as_real/view_as_complex`——无 aclnn 命令、无 DO_COMPATIBILITY**，视图逻辑完全在 ATen 侧 | 无 acl_op 回退可走（yaml 未登记） |

两条需要单独记录的边界：

1. **out 张量的 resize 语义**：arange_out（opapi/aclops 两路都是 TORCH_WARN+resize_）、linspace_out（静默 resize_）、logspace_out/range_out（TORCH_NPU_WARN+resize_）、eye_out（直接 resize_）——这 6 个工厂 out 入口 numel 不匹配时**一律重设尺寸而非报错**，与元素级算子 CheckOut 的「不匹配即抛错」族不同；文档表未单独提示该行为。
2. **logspace 只有 out 变体**：`logspace` functional 在两 pin yaml 均无条目，调用 functional 形态时的框架分派路径不在本卡范围；acl_op 回退侧的 dtype 白名单（仅 Float/Half）比 opapi 路更显式。

两 pin 差异如实：OnesKernelNpuOpApi.cpp/ZerosKernelNpuOpApi.cpp 的 names 守卫（主线有 #if、发布无，与 yaml 版本区间配套）、RangeKernelNpuOpApi.cpp 的 range_out Bool 接受度、StackKernelNpu.cpp 的 CheckOut dtype 模板与 stack.out 的 gen dtype——共 4 处真实 token 级差异；其余本节文件两 pin 语义等价（Eye/Flip aclops 与 PutKernelNpuOpApi 字节相同，其余仅排版差异）。zeros 工厂与前文 zero_ 增补小节的复用链衔接：opapi 手写 zeros 即「申请+zero_()」，不重复展开。

### 工厂/创建 28 名证据

- [ArangeKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ArangeKernelNpuOpApi.cpp)（implementation）：1–201；完整本地小文件。
- [ArangeKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ArangeKernelNpuOpApi.cpp)（implementation）：1–138；仅排版差异。

- [EyeKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/EyeKernelNpuOpApi.cpp)（implementation）：1–81；完整本地小文件。
- [EyeKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/EyeKernelNpuOpApi.cpp)（implementation）：1–91；仅排版差异。

- [LinspaceKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LinspaceKernelNpuOpApi.cpp)（implementation）：1–55；完整本地小文件。
- [LinspaceKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LinspaceKernelNpuOpApi.cpp)（implementation）：1–51；仅排版差异。

- [LogSpaceKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LogSpaceKernelNpuOpApi.cpp)（implementation）：1–51；完整本地小文件（仅 logspace_out）。
- [LogSpaceKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LogSpaceKernelNpuOpApi.cpp)（implementation）：1–61；仅排版差异。

- [OnesKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/OnesKernelNpuOpApi.cpp)（implementation）：1–65；完整本地小文件，names 重载带 V2R13 #if 守卫。
- [OnesKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/OnesKernelNpuOpApi.cpp)（implementation）：1–70；完整本地小文件，**无 #if 守卫**（两 pin 真实差异）。

- [RangeKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RangeKernelNpuOpApi.cpp)（implementation）：1–114；完整本地小文件，isIntegralType(res_type,false)。
- [RangeKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RangeKernelNpuOpApi.cpp)（implementation）：1–97；完整本地小文件，isIntegralType(res_type)（含 Bool，两 pin 真实差异）。

- [ZerosKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ZerosKernelNpuOpApi.cpp)（implementation）：1–57；完整本地小文件，names 重载带 V2R13 #if 守卫。
- [ZerosKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ZerosKernelNpuOpApi.cpp)（implementation）：1–65；完整本地小文件，**无 #if 守卫**（两 pin 真实差异）。

- [OnesLikeKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/OnesLikeKernelNpuOpApi.cpp)（implementation）：1–53；完整本地小文件（含 one_ helper）。
- [OnesLikeKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/OnesLikeKernelNpuOpApi.cpp)（implementation）：1–55；仅排版差异。

- [ViesAsRealKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ViesAsRealKernelNpuOpApi.cpp)（implementation）：1–14；完整本地小文件（纯 ATen 委托）。
- [ViesAsRealKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ViesAsRealKernelNpuOpApi.cpp)（implementation）：1–16；仅排版差异。

- [ArangeKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ArangeKernelNpu.cpp)（implementation）：1–196；完整本地小文件（start==end 特例、Half→Float）。
- [ArangeKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ArangeKernelNpu.cpp)（implementation）：1–149；仅排版差异。

- [EyeKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/EyeKernelNpu.cpp)（implementation）：1–121；完整本地小文件（attr-only Eye 命令、Bool→Int）。
- [EyeKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/EyeKernelNpu.cpp)（implementation）：1–121；与主线字节相同。

- [LinspaceKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LinspaceKernelNpu.cpp)（implementation）：1–109；完整本地小文件（steps==1 走 fill_）。
- [LinspaceKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LinspaceKernelNpu.cpp)（implementation）：1–114；仅排版差异。

- [LogSpaceKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogSpaceKernelNpu.cpp)（implementation）：1–79；完整本地小文件（dtype 白名单、arange assistant）。
- [LogSpaceKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LogSpaceKernelNpu.cpp)（implementation）：1–90；仅排版差异。

- [OnesKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/OnesKernelNpu.cpp)（implementation）：1–56；完整本地小文件。
- [OnesKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/OnesKernelNpu.cpp)（implementation）：1–63；仅排版差异。

- [RangeKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RangeKernelNpu.cpp)（implementation）：1–121；完整本地小文件（RangeD、NCHW）。
- [RangeKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/RangeKernelNpu.cpp)（implementation）：1–126；仅排版差异。

- [ZerosKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ZerosKernelNpu.cpp)（implementation）：1–44；完整本地小文件。
- [ZerosKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ZerosKernelNpu.cpp)（implementation）：1–48；仅排版差异。

- [OnesLikeKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/OnesLikeKernelNpu.cpp)（implementation）：1–62；完整本地小文件（OnesLike 命令）。
- [OnesLikeKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/OnesLikeKernelNpu.cpp)（implementation）：1–67；仅排版差异。

- [FlipKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/FlipKernelNpu.cpp)（implementation）：1–38；完整本地小文件（空 dims clone 直返）。
- [FlipKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/FlipKernelNpu.cpp)（implementation）：1–38；与主线字节相同。

- [RollKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RollKernelNpu.cpp)（implementation）：1–94；完整本地小文件（transpose 组合）。
- [RollKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/RollKernelNpu.cpp)（implementation）：1–110；仅排版差异。

- [StackKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/StackKernelNpu.cpp)（implementation）：1–84；完整本地小文件，CheckOut dtype=result_type(tensors)。
- [StackKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/StackKernelNpu.cpp)（implementation）：1–87；CheckOut dtype=tensors[0]（两 pin 真实差异）。

- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：1132–1151、2237–2252、2278–2286、3049–3056、3295–3298、3939–3954、4084–4095、4380–4388、4951–4968、5436–5443、5532–5539；仅本节 28 名 Schema 条目（该文件已列于 frontmatter 来源）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：1094–1113、2170–2185、2211–2219、2950–2957、3193–3196、3831–3846、3972–3983、4262–4270、4796–4813、5269–5276、5363–5370；同 28 名条目，ones.names/zeros.names 发布登记 all_version、stack.out gen dtype=tensors[0]（该文件已列于 frontmatter 来源）。
