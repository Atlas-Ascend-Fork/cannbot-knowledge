---
type: Guide
title: NPU重采样与像素重排：尺寸、dtype和CPU回退
description: 区分interpolate/旧upsample入口的参数与950DT double边界，以及PixelShuffle类函数差异和可能的Host计算。并含 Nearest-exact 1D 前后向：尺寸推导借用linear1d helper、同构DO_COMPATIBILITY往返与SymInt声明差异。并含普通 upsample 七族：双层回退结构、尺寸helper不对称与scale缺省值分裂；含普通七族 acl_op 回退内部：ACE 命令、dtype cast 与 scale 处理分裂。并含 网格采样与affine网格：grid_sampler 生成层登记、Half 往返分裂与 affine 反向的 BatchMatMul 组合。
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
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleBicubic2dAAKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleBilinear2dAAKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleBilinear2dAABackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleBicubic2dAABackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/opapi/UpsampleConstants.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleBicubic2dAAKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleBilinear2dAAKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleBilinear2dAABackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleBicubic2dAABackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/opapi/UpsampleConstants.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleNearestExact2dKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleNearestExact2dBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleNearestExact3dKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleNearestExact3dBackwardKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleNearestExact2dKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleNearestExact2dBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleNearestExact3dKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleNearestExact3dBackwardKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleNearestExact1dKernelOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleNearestExact1dBackwardKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleNearestExact1dKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleNearestExact1dBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleBicubic2dKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleBicubic2dBackwardKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleBilinear2dKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleBilinear2dBackwardKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleLinear1dKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleLinear1dBackwardKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleNearest1dKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleNearest1dBackwardKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleNearest2dKernelOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleNearest2dBackwardKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleNearest3dKernelOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleNearest3dBackwardKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleTrilinear3dKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleTrilinear3dBackwardKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleBicubic2dKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleBicubic2dBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleBilinear2dKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleBilinear2dBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleLinear1dKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleLinear1dBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleNearest1dKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleNearest1dBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleNearest2dKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleNearest2dBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleNearest3dKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleNearest3dBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleTrilinear3dKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleTrilinear3dBackwardKernelNpuOpApi.cpp
  role: implementation

- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/UpsampleNearest1dKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/UpsampleNearest1dBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/UpsampleNearest2dKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/UpsampleNearest2dBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/UpSampleNearest3dKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/UpsampleNearest3dBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/UpsampleLinear1dKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/UpsampleLinear1dBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/UpsampleBilinear2dKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/UpsampleBilinear2dBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/UpsampleBicubic2dKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/UpSampleBicubic2dBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/UpsampleTrilinear3dKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/UpsampleTrilinear3dBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/UpsampleNearest1dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/UpsampleNearest1dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/UpsampleNearest2dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/UpsampleNearest2dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/UpSampleNearest3dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/UpsampleNearest3dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/UpsampleLinear1dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/UpsampleLinear1dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/UpsampleBilinear2dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/UpsampleBilinear2dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/UpsampleBicubic2dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/UpSampleBicubic2dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/UpsampleTrilinear3dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/UpsampleTrilinear3dBackwardKernelNpu.cpp
  role: implementation

- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AffineGridGeneratorKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AffineGridGeneratorBackwardKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/Im2colKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AffineGridGeneratorKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AffineGridGeneratorBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/GridSampler2dKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/GridSampler2dBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/GridSampler3dKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/GridSampler3dBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/GridSampler3dBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/inner_compute.h
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AffineGridGeneratorKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AffineGridGeneratorBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/Im2colKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AffineGridGeneratorKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AffineGridGeneratorBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/GridSampler2dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/GridSampler2dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/GridSampler3dKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/GridSampler3dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/GridSampler3dBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/inner_compute.h
  role: implementation

created_at: '2026-11-09T10:01:21Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# NPU重采样与像素重排：尺寸、dtype和CPU回退

## 固定版本与范围

依据TorchNPU固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的原生API支持页，范围为其明列的A2/A3训练系列与950DT，不扩展950PR或发布组合。同提交PyTorch2.7.1、2.9至2.14的相关完整条目已逐版本对照；页面链接中的版本号、HTML标识及排版差异不当成能力增减。文档中的“已验证”是上游清单口径，本卡只读审阅，未运行设备或性能实验。

本卡聚焦空间重采样、网格和像素重排的迁移选择；不以相似名称推断dtype、参数或实现等价。

## 插值入口的尺寸与类型

| 入口 | input清单/特殊限制 |
| --- | --- |
| F.interpolate | BF16/FP16/FP32/FP64；950DT不支持double；模式nearest、linear、bilinear、bicubic、trilinear、area；不支持scale_factor |
| nn.Upsample | BF16/FP16/FP32/FP64，950DT不支持double；该条目没有重复F.interpolate的所有参数限制 |
| F.upsample | FP16/FP32/FP64，仅nearest；不能因名字是通用upsample就沿用bilinear等模式 |
| F.upsample_nearest | BF16/FP16/FP32，input仅3..5维 |
| F.upsample_bilinear | FP16/FP32 |
| nn.UpsamplingNearest2d | FP16/FP32/UINT8，可能回退CPU执行 |

部署F.interpolate时应提供与模型定义一致的显式输出size；由scale_factor换算size需要核对舍入、坐标与模式，不能直接删掉该参数或按任意取整宣称等价。旧入口与类条目的dtype范围差异也不能取并集；F.upsample虽然列FP64，不足以推翻interpolate/Upsample针对950DT的double限制，具体路线需独立验证。

UpsamplingNearest2d的“可能回退”不表示每次必然CPU，也不表示同名functional全部走同一路径。设备Tensor及接口清单支持不证明没有Host数值或往返拷贝，应对照实际CPU/NPU时间线和已纳管fallback门控。

## 网格输入

F.affine_grid对theta只列FP16/FP32，F.grid_sample对input列FP16/FP32/FP64；两个参数名与类型表不可互换，input有FP64不代表affine_grid也能用FP64 theta。清单未在这些条目写出的grid类型、维度、padding或反向能力不能自动补全。

## PixelShuffle与PixelUnshuffle

共同的基础集合为FP16/FP32/FP64、UINT8、INT8/16/32/64、BOOL；在此基础上：

- nn.PixelShuffle另列BF16，但未列complex；F.pixel_shuffle另列BF16、complex64/128。
- nn.PixelUnshuffle未列BF16/complex；F.pixel_unshuffle另列BF16，但未列complex。

这些是类/函数条目差异，不能据数学重排可逆就扩展类型或宣称纯view、无分配、零拷贝。它们也不改变前后卷积对通道、shape和dtype的要求。

## 验证边界

分别验证尺寸、像素/通道顺序、数值、梯度和实际执行位置，再比较端到端数据转移、内存及耗时。未在清单找到的入口不按名称推定支持或绝对不支持；来源支持表不替代各条目全部实现、组合参数或设备验证。

- [CPU回退与兼容实现](../../inference/guides/optimization/torch_npu/torch_npu_cpu_fallback_and_compatible_impl.md)
- [卷积路线](torch_npu_native_convolution_constraints.md)

## ChannelShuffle的独立类型表

固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的七份torch.nn页还将ChannelShuffle列为A2/A3训练系列与950DT支持，input为BF16/FP16/FP32、UINT8、INT8/16/32/64、BOOL、complex64/128，未列FP64。不能把PixelShuffle或PixelUnshuffle的dtype并集移植到ChannelShuffle，也不因它是重排就推定只改view、无拷贝或所有分组/布局都可用。本文未执行重排或设备实验。

## Flatten/Unflatten的入口名字和类型

同提交2.7.1、2.9、2.10页按torch.nn.Flatten/Unflatten列条目，2.11..2.14页按torch.nn.modules.flatten.Flatten/Unflatten列条目；这是文档命名差异，不直接断言运行时别名的新增/删除。

Flatten input列BF16/FP16/FP32、UINT8、INT8/16/32/64、BOOL、complex64/128；Unflatten列FP16/32/64、UINT8、INT8/16/32/64、BOOL，没有同一BF16/complex表。2.11/2.12的Unflatten.NamedShape另列A2/A3支持、950DT不支持，2.13/2.14未列这个子条目；不能用父类范围替代子方法，或把未收录直接解释成行为改变。条目不证明任意stride下只改view、零拷贝或可互逆，仍需检查实际shape和存储。

## 英文旧插值迁移与NamedShape版本

英文2.9/2.10/2.14对UpsamplingNearest2d、F.upsample、F.upsample_nearest、F.upsample_bilinear均有弃用提示，转向F.interpolate；nearest迁移指定mode="nearest"，bilinear提示mode="bilinear", align_corners=True。其余英文版本和中文未重复全部Version Notes，迁移仍需保持原尺寸、坐标和数值语义，不能只据提示宣称任意参数等价。

上文NamedShape在2.11/2.12收录指中文；英文2.7.1、2.9、2.10也在旧torch.nn.Unflatten下列NamedShape，连同2.11/2.12均标A2/A3支持、950DT不支持，2.13/2.14未列。文档名称和缺项不直接证明运行时别名增删或限制解除。

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

## AA二维插值：fast门控与FP32 CPU往返

以下补充OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`、发布`dedc316708372c9a8bfde4527abd2a94b74840f5`中_upsample_bilinear2d_aa、_upsample_bicubic2d_aa及各自backward的functional/out包装。它们属于antialias分支，不把同名普通插值、nearest或全部F.interpolate行为合并进来；八个Schema均仅列op_api [v2.1,newest]。这两仓的固定快照不认证某个安装组合，原平台支持页范围保持不变。

两版这些本地路线相同，命中slow会明确请求CPU FP32计算，再转回输入dtype并copy_至结果；最终返回设备Tensor不能用来判定没有Host计算。

| gate/位置 | 实际行为 | 可见准备成本 |
|---|---|---|
| DO_COMPATIBILITY对应算子不可用 | 调用本文件slow表达式 | 输入/grad转CPU并转Float、CPU插值、结果转原dtype和copy_ |
| 兼容通过但check*UseFast返回false | 同样调用slow | functional此时已经申请本地结果，slow中另有结果申请位置 |
| 所有本地fast检查通过 | 调用对应ACLNN算子 | 正向按输出shape、反向按input_size准备结果；无本地CPU路线 |
| out入口兼容检查 | 发生在check_tensor之前 | 符号兼容slow与经过out检查后gate失败的slow顺序不同 |

这里没有统一catch SDK执行错误再改CPU的机制。CPU调用自身失败、具体拷贝次数与等待、分配器复用均需结合实际运行定位。

### fast检查的真实条件

四个文件各自以函数局部static缓存同一个SoC表达式：`(GetSocVersion()>=Ascend910B1 && GetSocVersion()<Ascend310B1) || GetSocVersion()>Ascend310B4`。该枚举比较没有在本节展开成额外硬件支持白名单。

compute_scale对正的显式scale取倒数1/scale；否则output_size非零时取input_size/output_size，为零时取0。未指定scale在外层先value_or(0)，并不是一律按scale=1。前向以self H/W和结果H/W计算，反向以grad_input H/W与grad_output H/W计算；H_INDEX=2、W_INDEX=3。

| 入口 | 除SoC表达式之外的fast检查 |
|---|---|
| bilinear/bicubic前向 | 两轴均不能满足realScale>50 |
| bilinear反向 | 任一轴满足0<realScale<0.02则slow |
| bicubic反向 | 任一轴满足0<realScale<0.03则slow；还要求checkBicubicBackwardShapes接收的H/W都<=8192 |

scale检查函数的参数类型是float，compute_scale返回double后会经过该传参转换；上表是实际比较表达式，不保证任意十进制边界在转换后精确相等。bicubic反向shape检查形参是int，调用处传grad_output的H/W，不能将其说成对任意int64超大shape的完整范围认证。

align_corners虽出现在部分check函数形参中，没有用于上述gate计算，仍原样传入fast/CPU算子。bilinear check函数的output_size形参也没有另加gate；“入参存在”不等于决定fast选择。为避开CPU改尺寸、scale或align_corners时，应保留目标坐标与采样语义。

### slow的dtype与申请顺序

正向slow执行self.cpu().to(Float)，调用CPU同名AA算子，再将CPU结果to(self原dtype)并copy_到result；反向对grad_output做同样的CPU Float准备，调用CPU AA backward，把梯度转回grad_output原dtype再copy_。因此最终dtype恢复不证明Float计算保留所有FP64或整数原精度。

slow functional内部自行申请结果，正向由self选项和输出shape申请，反向由grad_output和input_size申请。兼容通过的functional外层已经为fast申请结果，gate失败时没有把该对象传给slow复用，而是调用slow functional再申请；这是两处独立申请请求，不能直接报固定两份物理storage或峰值。out slow直接copy_到传入结果，不在该slow函数内重新申请设备输出。

前向bicubic shape helper明确检查self.rank==4、output_size长度==2；bilinear helper只明确self.rank>1、output_size长度>1，再构造[N,C,outH,outW]，不能把后者检查擅自收紧成已经验证rank恰好4。fast gate随后读取H/W，完整参数合法性仍要结合实际入口。反向申请/检查以input_size为目标shape。

fast正向分别调用aclnnUpsampleBilinear2dAA/aclnnUpsampleBicubic2dAA，反向分别是aclnnUpsampleBilinear2dAABackward/aclnnUpsampleBicubic2dAAGrad，保留准确符号名。定位训练慢路径应同时记录前后向、实际SoC、scale来源、输入/输出H/W、原dtype及out是否提供，再核Host时间线、数值和梯度。本节仅静态审阅，没有执行CPU/NPU、数值或性能实验，不新增运行verified或平台承诺。

### AA实现证据

- [UpsampleBicubic2dAAKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleBicubic2dAAKernelNpuOpApi.cpp)（implementation）：1–113。
- [UpsampleBilinear2dAAKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleBilinear2dAAKernelNpuOpApi.cpp)（implementation）：1–106。
- [UpsampleBilinear2dAABackwardKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleBilinear2dAABackwardKernelNpuOpApi.cpp)（implementation）：1–148。
- [UpsampleBicubic2dAABackwardKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleBicubic2dAABackwardKernelNpuOpApi.cpp)（implementation）：1–152。
- [UpsampleConstants.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/opapi/UpsampleConstants.h)（implementation）：19–19、21–25。
- [OpUtils.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）：291–298。
- [KernelNpuOutputSize.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1479–1497、1503–1527。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：5246–5256、5282–5292。
- [UpsampleBicubic2dAAKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleBicubic2dAAKernelNpuOpApi.cpp)（implementation）：1–103。
- [UpsampleBilinear2dAAKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleBilinear2dAAKernelNpuOpApi.cpp)（implementation）：1–106。
- [UpsampleBilinear2dAABackwardKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleBilinear2dAABackwardKernelNpuOpApi.cpp)（implementation）：1–128。
- [UpsampleBicubic2dAABackwardKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleBicubic2dAABackwardKernelNpuOpApi.cpp)（implementation）：1–134。
- [UpsampleConstants.h dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/opapi/UpsampleConstants.h)（implementation）：19–19、21–25。
- [OpUtils.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp)（implementation）：287–294。
- [KernelNpuOutputSize.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1328–1343、1350–1366。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：5079–5089、5115–5125。

## Nearest-exact 2D/3D：兼容选择与CPU往返

本节对照OpPlugin固定主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`与发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的四类nearest-exact前/反向包装及functional/out变体。它们是独立低层入口，不扩大前文公开interpolate模式、dtype和产品支持清单；这里只读源码，没有执行设备或CPU算子。

| 条件或阶段 | 两版所读行为 | 准备成本与定位点 |
| --- | --- | --- |
| 每个入口最先执行DO_COMPATIBILITY | 各宏展开处静态保存算子/GetWorkspaceSize地址与IsAclnnOnly结果 | 不是每次调用重新探测，也不是执行失败后才选择CPU |
| 任一所需地址缺失，且保存的AclnnOnly为真 | 抛不支持错误 | 提供了CPU slow函数也不表示一定会进入它 |
| 任一地址缺失，AclnnOnly为假 | 直接返回对应slow函数结果 | 此return在正常out的check_tensor及正常functional申请之前 |
| slow前向 | self.cpu()后调用同维度at::_upsample_nearest_exact算子，再copy_到结果 | functional先申请self.options对应输出；out直接使用传入对象 |
| slow反向 | grad_output.cpu()后调用对应CPU backward，再copy_到grad_input | functional按grad_output和给定input_size申请；out直接回写原对象 |
| 地址可用的正常分支 | 2D/3D及前/反向分别调用对应aclnnUpsampleNearestExact* | 没有此处额外的比例阈值分支，也没有总catch把SDK错误重跑CPU |

本页前述AA表的“兼容分派选择slow”同样以缺少所需地址且保存的AclnnOnly为假为前提；API地址可用后，显式fast gate失败而调用slow是另一条分支，不由该缺符号检查统一否决。

这些slow函数没有显式先转FP32；它们把原输入或梯度dtype交给CPU算子，而不是据最终结果设备判断计算始终在NPU。CPU算子内部支持、实际复制等待及数值仍需按具体输入核对。

正常SDK路线将缺省scales_h/scales_w及3D的scales_d以value_or(0)准备；slow路线向CPU算子传原optional参数。不要自行把SDK中的0解释为某个已验证的坐标算法，或把nearest-exact与前文近邻类名当作等价入口。

前向shape helper只作局部最小结构检查：2D要求input.dim()>=2且output_size.size()>=2，取前两输入维和前两输出尺寸组成[N,C,H,W]；3D要求input.dim()>1、output_size.size()>2，取前两输入维和前三输出尺寸组成[N,C,D,H,W]。原output_size仍完整传给SDK，helper不截断它，也不是完整输入rank、尺度或存储布局校验。反向则直接使用给定input_size申请或检查输出。

两版Schema对八个入口列op_api=[v2.1,newest]，这里没有对应acl_op声明。2D前向元数据字面写SymInt[3]，反向output_size写SymInt[2]；记录这项声明差异，不从注解或helper的最小检查推导任意多余尺寸均可用。兼容性、框架参数约束与最终CPU/SDK接受应分别核对。

定位时记录确切维度与前/反向重载、首次符号/模式状态、是否进入slow、输入/输出shape及dtype，再分别观察CPU计算和copy_；不能按“接口可调用”省略这些往返准备。

### Nearest-exact固定实现证据

- [固定源码](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleNearestExact2dKernelOpApi.cpp)：1–80行。
- [固定源码](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleNearestExact2dBackwardKernelNpuOpApi.cpp)：1–100行。
- [固定源码](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleNearestExact3dKernelOpApi.cpp)：1–86行。
- [固定源码](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleNearestExact3dBackwardKernelOpApi.cpp)：1–107行。
- [固定源码](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)：1579–1605,2012–2023行。
- [固定源码](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)：5360–5371,5378–5383,5400–5405行。
- [固定源码](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)：94–119行。
- [固定源码](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleNearestExact2dKernelOpApi.cpp)：1–69行。
- [固定源码](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleNearestExact2dBackwardKernelNpuOpApi.cpp)：1–71行。
- [固定源码](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleNearestExact3dKernelOpApi.cpp)：1–71行。
- [固定源码](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleNearestExact3dBackwardKernelOpApi.cpp)：1–75行。
- [固定源码](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)：1402–1419,1821–1833行。
- [固定源码](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)：5193–5204,5211–5216,5233–5238行。
- [固定源码](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)：96–110行。

## Nearest-exact 1D：借用linear1d尺寸推导的兼容往返

本节补齐OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`、发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的`_upsample_nearest_exact1d`与`_upsample_nearest_exact1d_backward`及其out/grad_input变体（四个Schema，主线yaml 5354–5357、5372–5375，发布5187–5190、5205–5208，均只列`op_api: [v2.1, newest]`、无acl_op条目）。主线与发布两版本两个手写OpAPI文件去空白字符流逐字相等（仅排版，main 73/80行、release 66/71行，diff -u核对）；上文2D/3D节已读的DO_COMPATIBILITY/op_api_common.h语义沿用不重复展开。这里只读源码，没有执行设备或CPU算子。

| 条件或阶段 | 实际门槛→动作 | 失败/边界 |
| --- | --- | --- |
| 前向尺寸推导 | 借用`op_infer::upsample_linear1d_npu_output_size`（主线KernelNpuOutputSize.cpp 1529–1550、发布1368–1381，非nearest-exact专属helper）：先TORCH_CHECK `self.dim() > 1`（原文"tensor self's dimension must be greater than 1, but got Tensor of dimension N"）与`output_size.size() > 0`（原文"output_size length should be greater than 0..."，均ErrCode::PARAM），随后只取`output_size[0]`组成{N, C, W} | 1D nearest-exact没有自己的尺寸helper：输入按N,C,W三维合同解释，纯一维[W]输入直接PARAM抛错；output_size只消费首元素，其余元素是否可用由SDK侧决定，不从Schema的SymInt[3]推导三个尺寸都有效 |
| 每个入口的DO_COMPATIBILITY | `aclnnUpsampleNearestExact1d`（前向）/`...Exact1dBackward`（反向）符号或其GetWorkspaceSize缺失时走slow函数，与上文2D/3D节同一宏语义 | 同上文：AclnnOnly模式下缺符号抛"Current device only support aclnn operators, but ..."，非AclnnOnly才进slow |
| slow前向 | functional先按linear1d helper的输出尺寸`apply_tensor_without_format(self.options())`申请，再`at::_upsample_nearest_exact1d(self.cpu(), output_size, scales)`后`copy_`回结果；out变体直接把CPU结果`copy_`进传入对象，不申请 | 无显式FP32转换，与上文2D/3D slow口径一致；CPU算子内部支持与数值未运行验证 |
| slow反向 | functional按`apply_tensor_without_format(grad_output, input_size)`申请后`grad_output.cpu()`调CPU backward再`copy_`；out变体直接回写原对象 | 同上 |
| 正常前向分支 | scales经`value_or(0)`成double；out变体`check_tensor({self}, out, self, outputSize)`后单次`EXEC_NPU_CMD(aclnnUpsampleNearestExact1d, self, output_size, scalesValue, out)`；functional按同一helper尺寸申请后同一命令 | 单host命令不等于单device kernel；SDK对0比例值的解释沿用上文nearest-exact节边界（不作已验证坐标算法断言） |
| 正常反向分支 | `check_tensor({grad_output}, grad_input, grad_output, input_size)`后单次`EXEC_NPU_CMD(aclnnUpsampleNearestExact1dBackward, grad_output, output_size, input_size, scales_attr, grad_input)`；functional按input_size申请 | 两个反向变体里各有一行未消费的`at::Tensor self = grad_output;`本地别名（按原文记录，无行为影响）；反向输出尺寸直接用给定input_size，与本卡2D/3D节一致 |
| Schema声明差异 | 前向元数据字面写`SymInt[3] output_size`；反向写`SymInt[1] output_size`与`SymInt[3] input_size` | 反向output_size的一维声明与前向三维声明不对称，按原文记录；不从注解推导多余尺寸或可省参数的通用规则 |

### Nearest-exact 1D 补充证据

- [UpsampleNearestExact1dKernelOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleNearestExact1dKernelOpApi.cpp)（primary）：1–73；完整本地小文件。
- [UpsampleNearestExact1dBackwardKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleNearestExact1dBackwardKernelNpuOpApi.cpp)（primary）：1–80；完整本地小文件。
- [UpsampleNearestExact1dKernelOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleNearestExact1dKernelOpApi.cpp)（implementation）：1–66；完整本地小文件；与主线去空白字符流相同（仅排版）。
- [UpsampleNearestExact1dBackwardKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/UpsampleNearestExact1dBackwardKernelNpuOpApi.cpp)（implementation）：1–71；完整本地小文件；与主线去空白字符流相同（仅排版）。
- [KernelNpuOutputSize.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1529–1550；upsample_linear1d_npu_output_size完整helper（该文件已列于frontmatter来源）。
- [KernelNpuOutputSize.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1368–1381；同helper发布侧完整函数体。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：5354–5357、5372–5375；1D四个Schema条目（该文件已列于frontmatter来源）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：5187–5190、5205–5208；同口径，与主线逐字相同。

## 普通 upsample 七族：双层回退结构、尺寸helper不对称与scale缺省值分裂

上文 AA 与 nearest-exact 两节核对了带后缀的子族；本节补齐 039/030 账本"_upsample_*_aa / _upsample_nearest_exact* 族"在同一 yaml 区段内的其余 27 个 Schema——普通 `upsample_*` 七族（bicubic2d/bilinear2d/linear1d/nearest1d/nearest2d/nearest3d/trilinear3d 各前向+out+backward+grad_input，linear1d 无 grad_input 条目）。主线与发布两版本 这 27 条逐字相同、均`acl_op: [v2.1, newest]`+`op_api: [v2.1, newest]`（与 AA/exact 不同——那些只列 op_api；这里 acl_op 回退是登记路径）。14 个手写 opapi 文件主线与发布两版本 逻辑结构一致（排版与尾注释差异，逐文件去空白字符流核对）；KernelNpuOutputSize 尺寸 helper 与 yaml 已在 frontmatter 来源。DO_COMPATIBILITY 双符号探测语义沿用上文 op_api_common.h 结论，不重复。

| 族/入口 | 回退结构与关键门 | 尺寸合同 | scale 缺省 |
| --- | --- | --- | --- |
| bicubic2d 前向/.out | 直接`DO_COMPATIBILITY(aclnnUpsampleBicubic2d, acl_op::...)`；check_tensor 后调共享内层`upsample_bicubic2d_opapi`（无宏单 EXEC，主线 23–34） | `upsample_bicubic2d_npu_output_size`：TORCH_CHECK **`self.dim() == 4`**、`output_size.size() == 2`（严格等式，主线 1479–1497） | 0 |
| bicubic2d backward/.grad_input | `DO_COMPATIBILITY(aclnnUpsampleBicubic2dBackward, acl_op::...)`；out 变体 check_tensor({grad_output}, grad_input, grad_output, input_size) | backward 尺寸 helper 是 identity：直接返回 input_size（主线 1499–1501） | 0 |
| bilinear2d 前向/.out | 直接`DO_COMPATIBILITY(aclnnUpsampleBilinear2d, acl_op::...)`；**TORCH_CHECK 硬拒 Double**（原文"upsample_binlinear_2d not support torch.fp64 dtypes"——binlinear 拼写按原文记录，ErrCode::TYPE） | `upsample_bilinear2d_npu_output_size`：`self.dim() > 1`、`output_size.size() > 1`（与 bicubic 的 ==4 不对称，主线 1503–1527） | 0 |
| bilinear2d backward/.grad_input | **BackwardV2 双层**：当前入口`DO_COMPATIBILITY(aclnnUpsampleBilinear2dBackwardV2, op_api::upsample_bilinear2d_backward_old(_out))`，old 再`DO_COMPATIBILITY(aclnnUpsampleBilinear2dBackward, acl_op::...)`——两层都在同一文件 | grad_input 按 input_size 申请（apply_tensor，非 without_format） | 0；**反向无 Double 检查**（与前向不对称按原文记录） |
| linear1d 前向/.out | 直接`DO_COMPATIBILITY(aclnnUpsampleLinear1d, acl_op::...)` | 复用`upsample_linear1d_npu_output_size`（dim>1、size>0，{N,C,W}——上文 nearest-exact 1D 节已核对该 helper） | 前向 **-1**（DEFAULT_SCALES=-1） |
| linear1d backward（无 grad_input 条目） | 直接`DO_COMPATIBILITY(aclnnUpsampleLinear1dBackward, acl_op::...)`；apply_tensor 申请 | input_size | **0**——同族前向 -1/反向 0 分裂按原文记录 |
| nearest1d 前向/.out | **V2 双层**：`DO_COMPATIBILITY(aclnnUpsampleNearest1dV2, op_api::upsample_nearest1d_old(_out))`，old 再`DO_COMPATIBILITY(aclnnUpsampleNearest1d, acl_op::...)`且**old 命令不带 scale 实参**（aclnnUpsampleNearest1d 只收 self/output_size/result） | 复用 linear1d helper | V2 路 `static_cast<float>(scales.value_or(-1.0))`——**double→float 收窄**（与上文 AA 节 compute_scale 传参转换同型问题） |
| nearest1d backward/.grad_input | 无 V2 层：直接`DO_COMPATIBILITY(aclnnUpsampleNearest1dBackward, acl_op::...)` | input_size | -1（DEFAULT_SCALES） |
| nearest2d 前向/.out | **V2 双层**同 nearest1d（aclnnUpsampleNearest2dV2→old→acl_op；old 不带 scale） | 文件**本地** helper `upsample_nearest2d_output_size_npu`（主线 23–34：TORCH_CHECK dim>=2、output_size.size()>=2，取 {N,C,H,W}——不在 KernelNpuOutputSize.cpp） | V2 路 float 收窄 value_or(-1.0) |
| nearest2d backward/.grad_input | 无 V2 层：直接`DO_COMPATIBILITY(aclnnUpsampleNearest2dBackward, acl_op::...)` | check_tensor({grad_output}, grad_input, grad_output, input_size) | -1 |
| nearest3d 前向/.out + backward/.grad_input | 无 V2 层：`DO_COMPATIBILITY(aclnnUpsampleNearest3d(Backward), acl_op::...)`直接 | `upsample_nearest3d_npu_output_size`（dim>1、output_size.size()>2，{N,C,D,H,W}，主线 1579–1605） | **0**——与 nearest1d/2d 的 -1 分裂按原文记录 |
| trilinear3d 前向/.out + backward/.grad_input | 直接`DO_COMPATIBILITY(aclnnUpsampleTrilinear3d(Backward), acl_op::...)`；共享内层`*_opapi` helper（无宏单 EXEC，与 bicubic 同型） | `upsample_trilinear3d_npu_output_size`（dim>1、output_size.size()==3，{N,C,D,H,W}，主线 1553–1577） | 0 |

三个跨族结论：其一，**尺寸 helper 只取 input 前 2 维与 output_size 前 k 个元素**（k=1/2/3），输入更高维或 output_size 多余元素不在本层校验、原样传 SDK——bicubic 的 ==4 严格等式是唯一硬 rank 门，其余族 rank>1 宽松合同按原文记录不互推。其二，**scale 缺省哨兵分裂**：nearest1d/2d 全族 -1、linear1d 仅前向 -1（反向 0）、nearest3d/bilinear2d/bicubic2d/trilinear3d 全 0——与上文 nearest-exact 的 value_or(0) 又是另一口径；-1 与 0 哨兵在 SDK 侧的解释未核对，不把缺省值当作已验证坐标算法，V2 命令的 float 收窄同型。其三，**双层回退仅存在于三处**（nearest1d/nearest2d 前向、bilinear2d 反向的 V2 变体）：缺 aclnnXV2 符号回退到同文件 old 入口、再缺 aclnnX 才回退 acl_op——与 AA 节"兼容选择slow"是不同机制（AA 是 fast gate 失败走 CPU slow，这里全链是 NPU 命令选择，无 CPU 路径）。

迁移 F.interpolate 到这些低层入口时按族核对：双层回退的实际落点（V2/old/acl_op 三段）、scale 缺省哨兵与本族的前反向一致性、bicubic 的 4 维硬门（其余族接受 >1 维）、bilinear2d 前向的 FP64 硬拒与反向无检查的不对称。所有 acl_op 回退目标（主线与发布两版本 `op_plugin/ops/aclops/` 各 14 个 Upsample* 文件存在）本节未核对。

### 普通 upsample 七族补充证据

- [UpsampleBicubic2dKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleBicubic2dKernelNpuOpApi.cpp)（primary）：1–65；完整本地小文件（含共享内层 upsample_bicubic2d_opapi）。
- [UpsampleBicubic2dBackwardKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleBicubic2dBackwardKernelNpuOpApi.cpp)（primary）：1–75；完整本地小文件。
- [UpsampleBilinear2dKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleBilinear2dKernelNpuOpApi.cpp)（primary）：1–68；完整本地小文件（Double 硬拒）。
- [UpsampleBilinear2dBackwardKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleBilinear2dBackwardKernelNpuOpApi.cpp)（primary）：1–131；完整本地小文件（old/old_out/V2 四函数）。
- [UpsampleLinear1dKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleLinear1dKernelNpuOpApi.cpp)（primary）：1–55；完整本地小文件。
- [UpsampleLinear1dBackwardKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleLinear1dBackwardKernelNpuOpApi.cpp)（primary）：1–40；完整本地小文件（无 grad_input 变体）。
- [UpsampleNearest1dKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleNearest1dKernelNpuOpApi.cpp)（primary）：1–63；完整本地小文件（V2 双层）。
- [UpsampleNearest1dBackwardKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleNearest1dBackwardKernelNpuOpApi.cpp)（primary）：1–52；完整本地小文件。
- [UpsampleNearest2dKernelOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleNearest2dKernelOpApi.cpp)（primary）：1–90；完整本地小文件（本地尺寸 helper + V2 双层）。
- [UpsampleNearest2dBackwardKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleNearest2dBackwardKernelNpuOpApi.cpp)（primary）：1–57；完整本地小文件。
- [UpsampleNearest3dKernelOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleNearest3dKernelOpApi.cpp)（primary）：1–56；完整本地小文件。
- [UpsampleNearest3dBackwardKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleNearest3dBackwardKernelNpuOpApi.cpp)（primary）：1–70；完整本地小文件。
- [UpsampleTrilinear3dKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleTrilinear3dKernelNpuOpApi.cpp)（primary）：1–78；完整本地小文件。
- [UpsampleTrilinear3dBackwardKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/UpsampleTrilinear3dBackwardKernelNpuOpApi.cpp)（primary）：1–82；完整本地小文件。
- [KernelNpuOutputSize.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1479–1527、1553–1605；bicubic（含 backward identity helper 1499–1501）、bilinear、trilinear、nearest3d 四个尺寸 helper 完整函数体（linear1d helper 1529–1550 已在上文已读清单；该文件已列于 frontmatter 来源）。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：5238–5244、5258–5281、5294–5304、5306–5320、5322–5336、5338–5352、5384–5398；七族 27 条目（AA/exact 条目已在上文已读清单，不重复计；该文件已列于 frontmatter 来源）。
- 发布版本 对应 14 个 opapi 文件（UpsampleBicubic2d/Bicubic2dBackward/Bilinear2d/Bilinear2dBackward/Linear1d/Linear1dBackward/Nearest1d/Nearest1dBackward/Nearest2d/Nearest2dBackward/Nearest3d/Nearest3dBackward/Trilinear3d/Trilinear3dBackward，1–53/63/58/104/51/40/69/52/96/53/59/70/71/74 行）：逐文件与主线逻辑结构一致（排版+尾注释差异，去空白字符流核对）。
- [KernelNpuOutputSize.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1328–1347（含 backward identity 1345–1347）、1350–1374、1383–1419；四 helper 发布侧完整函数体。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：5071–5077、5091–5113、5127–5137、5139–5153、5155–5169、5171–5185、5217–5231；同 27 条目，与主线逐字相同。
- 负向证据：本卡正文（含上文 AA/nearest-exact 节）此前未覆盖普通 upsample 七族——canonical 与全部 batch*/staged rg `UpsampleBilinear2dKernelNpuOpApi` 等七族文件名零命中；aclops 侧 14 个 Upsample* 文件主线与发布两版本 存在但未核对（未核对）。

## 普通七族的 acl_op 回退内部

上文普通七族节把`DO_COMPATIBILITY(…, acl_op::…)`的回退目标记为未核对；本节读完主线与发布两版本各14个aclops Upsample文件，核对该目标。14文件主线与发布两版本**去空白字符流逐一相同**（`tr -d '[:space:]'`比对；UpsampleBilinear2d仅版权头换行差异）。登记口径沿用上文：这些族`acl_op: [v2.1, newest]`是登记路径，acl_op路使用ACE命令而非aclnn，与opapi路不互推。

| 家族（acl_op 回退） | 实际门槛与动作 | 关键边界 |
| --- | --- | --- |
| nearest1d 前向/.out | rank==3且后两维非空、output_size长度1；unsqueeze(2)后**dtype分命令**：FP32/FP16走`ResizeNearestNeighborV2`（{1,W} Int设备输入、align_corners/half_pixel_centers均false）；**其他dtype走ACE命令`Resize`**（output_size两度作为Float设备输入、out.sizes()作为Long设备输入、nearest/floor/pytorch_half_pixel attrs）；结果squeeze(2) | 非浮点dtype的尺寸走Float输入是ACE合同字面，不据以断言精度；functional与out共用nocheck，out变体CheckOut按self |
| nearest1d backward/.grad_input | 同型dtype分命令：FP32/FP16走`ResizeNearestNeighborV2Grad`；其他走`ResizeGrad`（scales以标量设备输入传入`value_or(-1)`两份、origin_size Long输入、cubic_coeff_a -0.75/extrapolation_value 0.0等默认attrs；output_size[0]!=0仅在该分支检查） | input_size必须3元；scales缺省-1哨兵与opapi口径不同不互推 |
| nearest2d 前向/.out | rank==4硬门、output_size长度2；`ResizeNearestNeighborV2`（尺寸Int设备输入、两attr false）；out变体CheckOut显式带`get_tensor_npu_format(result)` | 无dtype分命令（与1d不对称）；scales参数完全不使用 |
| nearest2d backward/.grad_input | `ResizeNearestNeighborV2Grad`（input_size 4元检查）；out变体CheckOut按grads.scalar_type()原dtype；**functional对非Float的grad先`_npu_dtype_cast(grad_output, kFloat)`且不转回**——grad_input以cast后options申请 | functional产生FP32梯度、out变体要求原dtype，两侧dtype合同不同；_npu_dtype_cast内部属torch_npu仓未核对 |
| nearest3d 前向/.out + backward/.grad_input | rank==5/output_size长度3；`UpsampleNearest3d(Grad)`——output_size（前向）与input_size/output_size（反向）都走**attr**；反向grad尺寸按input_size前两维+三维复原 | **scales_d/h/w三参数被整族完全忽略**；无dtype分命令 |
| linear1d 前向/.out | output_size长度1、rank3非空且输入/输出W>0；unsqueeze(2)后ACE命令`ResizeD`（mode linear、coordinate_transformation_mode按align_corners二选一、sizes attr）；**scale=显式scales或缺省时`output_size[0]/输入W`的float计算比值** | 与opapi路的-1/0哨兵根本不同——acl_op自行计算scale；无backward grad_input变体（yaml无条目，与上文一致） |
| linear1d backward | input_size 3元、grad_output≥3维；`ResizeGradD`（original_size attr、scales attr、mode linear）；functional对非Float的grad先cast到Float，结尾**把结果`to(grad_output.dtype())`转回** | 与nearest2d的"不转回"不对称按原文记录；scale按grad_output.W/input_W计算 |
| bilinear2d 前向/.out | **非Float（含Half）输入先`_npu_dtype_cast(self, kFloat)`**；输出尺寸按cast后tensor推导；ACE命令`ResizeBilinearV2`（{H,W} Int设备输入、align_corners与half_pixel_centers=!align_corners）；functional结尾把结果cast回self dtype，**out变体不转回**（CheckOut以cast后tensor为参照） | out变体的dtype合同=FP32；round-trip只发生在functional |
| bilinear2d backward/.grad_input | `ResizeBilinearV2Grad`——**需要`original_image`占位输入**：`apply_tensor(grad_output, input_size)`分配的未初始化张量纯作命令输入；无scales传递 | 占位输入是额外分配；functional grad dtype跟grad_output |
| bicubic2d 前向/.out | **rank>=2宽松门**：输出取self.size(0)/size(1)为N/C再拼output_size成4元——2D输入也产出4D输出；ACE命令`ResizeD`（mode cubic、cubic_coeff_a -0.75、nearest_mode round_prefer_floor、roi空）；**scales缺省{0.0,0.0}不计算** | 与opapi路bicubic==4严格rank门不对称；与linear1d的scale计算比不同 |
| bicubic2d backward/.grad_input | `ResizeGradD`（data_format **HWNC**）：grad_output先permute{2,3,0,1}喂命令，grad_input再`reshape({H,W,N,C}).permute({2,3,0,1})`恢复——**out变体把grad_input引用重绑到该permuted view**；scales缺省{0,0} | 输出是重排后的视图；input_size必须4元 |
| trilinear3d 前向/.out | rank==5/output_size长度3；`UpsampleTrilinear3d`（output_size与align_corners走attr） | scales三参数忽略（与nearest3d同型） |
| trilinear3d backward/.grad_input | `UpsampleTrilinear3dGrad`（input_size/output_size/align_corners attrs）；**out变体的check_match不符分支把grad_input（而非contiguous_out）作为命令输出**——contiguous_out已format_contiguous计算但未用于命令，format_fresh_view仍按其执行 | 该分支字面按原文记录，不判定上游意图；functional按grad_output申请结果 |

跨族三条：其一，**scale处理三分裂**——nearest3d/trilinear3d整族忽略、bicubic2d缺省0不计算、linear1d按比值计算；缺省值都不与opapi路的-1/0哨兵互推。其二，**dtype cast三分裂**——nearest3d/trilinear3d不转换、nearest2d backward转换不回转、linear1d backward转换回转、bilinear2d前向转换且仅functional回转；bilinear2d的FP32 round-trip与上文AA节的CPU slow路径、opapi路的Double硬拒是三种不同机制。其三，**1D族统一unsqueeze(2)/squeeze(2)的4D桥接**（除nearest3d/trilinear3d的5D合同），bicubic2d的rank>=2门是唯一无严格rank要求的入口。

### acl_op 回退补充证据

- [UpsampleNearest1dKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/UpsampleNearest1dKernelNpu.cpp)（primary）：21–105；`UpsampleNearest1dBackwardKernelNpu.cpp` 21–113；`UpsampleNearest2dKernelNpu.cpp` 21–95；`UpsampleNearest2dBackwardKernelNpu.cpp` 21–86；`UpSampleNearest3dKernelNpu.cpp` 21–81；`UpsampleNearest3dBackwardKernelNpu.cpp` 21–115；`UpsampleLinear1dKernelNpu.cpp` 21–119；`UpsampleLinear1dBackwardKernelNpu.cpp` 21–121；`UpsampleBilinear2dKernelNpu.cpp` 21–93；`UpsampleBilinear2dBackwardKernelNpu.cpp` 21–82；`UpsampleBicubic2dKernelNpu.cpp` 21–129；`UpSampleBicubic2dBackwardKernelNpu.cpp` 21–130；`UpsampleTrilinear3dKernelNpu.cpp` 21–101；`UpsampleTrilinear3dBackwardKernelNpu.cpp` 21–115；均为完整函数体（前部版权头不重复计行）。
- 发布版本对应14文件（98/121/85/75/81/115/129/102/105/86/132/134/87/122行，行数见manifest source_meta）：逐文件与主线**去空白字符流相同**（`tr -d '[:space:]'`比对，缩进重排/版权头换行差异）。
- 负向证据：aclops目录主线与发布两版本无其他Upsample文件（find零命中）；上文普通七族opapi节所列`DO_COMPATIBILITY`回退目标`acl_op::upsample_*`与本节文件一一对应（AclOpsInterface声明由gen_op_backend生成，不另记来源）。

## 网格采样与affine网格：生成层登记、Half往返分裂与反向组合

上文“网格输入”只锚定公开清单的dtype差异；本节补齐同族底层入口在两版OpPlugin固定树的Eager实现层：`affine_grid_generator(±backward)`与`grid_sampler_2d/3d(±backward)`。yaml登记主线与发布两版本逐字相同（python逐行对比）：affine两名主线1038–1044、发布1000–1006（acl_op+op_api均`[v2.1, newest]`、无gen_opapi）；`grid_sampler_2d`/`grid_sampler_2d_backward`/`grid_sampler_3d`三名`all_version`（主线2492–2499、2501–2511、2513–2520，发布2413–2420、2422–2432、2434–2441），**`grid_sampler_3d_backward`为`[v2.1, newest]`**（主线2522–2532、发布2443–2453）——注册版本范围与其余三名不对称按原文记录，不外推为v2.1前不可用（框架侧路由未核对）。grid_sampler四名在主线与发布两版本均无手写opapi文件（find零命中），op_api路由全部来自gen_opapi生成层（op-plugin config README：结构化适配“适配层除申请output tensor，无其他适配逻辑”）：前向out0尺寸字面`{input.size(0), input.size(1), grid.size(1), grid.size(2)}`（3D另加`grid.size(3)`）、dtype=input；反向out0/dinput尺寸与dtype=input、out1/dgrid=grid；exec分别为aclnnGridSampler2D/2DBackward/3D/3DBackward。生成体不随仓提交，本节按登记面记录，不推导生成wrapper的额外检查；下表acl_op列为主线与发布两版本手写aclops文件的实读行为。

| 入口 | 实际门槛→动作 | 失败/边界 |
| --- | --- | --- |
| affine_grid_generator（opapi手写，主线21–44） | `DO_COMPATIBILITY(aclnnAffineGrid, acl_op::affine_grid_generator(...))`后TORCH_CHECK `size.size()==4或==5`（原文"AffineGridGenerator needs 4d or 5d size(input)."，PARAM）；输出按`{size[0],size[2],size[3],2}`或`{size[0],size[2],size[3],size[4],3}`推导，`apply_tensor_without_format(theta, outputSize)`申请后单次`EXEC_NPU_CMD(aclnnAffineGrid, theta, size, align_corners, result)` | theta的dtype/维度检查不在本层（公开清单的FP16/FP32见上文“网格输入”，不互推）；单host命令≠单device kernel |
| affine_grid_generator（acl_op回退，主线40–58） | 同TORCH_CHECK；输出尺寸走`op_infer::infersize_affine_grid_generator`（KernelNpuOutputSize.cpp 1679–1693：4元size→`{N,H*W,2}`三维中间形；否则TORCH_CHECK `size.size()>4`（原文"It is expected size greater than 4..."）→`{N,D*H*W,3}`）；`apply_tensor`（带格式申请，与opapi路without_format不对称）后ACE命令"AffineGrid"（size以at::kInt设备输入、align_corners attr），结尾`result.view(...)`回四/五维 | 中间三维形是回退路私有合同；两路最终形状一致但申请格式路径不同，不互推 |
| affine_grid_generator_backward（opapi手写，主线43–74） | **无DO_COMPATIBILITY、无专用aclnn反向命令**：TORCH_CHECK仅`size.size()==4`（原文"AffineGridGeneratorBackward needs 4d (spatial) input."，PARAM）；result按`{N,3,2}`+ACL_FORMAT_ND申请、assist按`{N,H,W,3}`without_format申请；assist三通道由`select(-1,k).copy_(_linspace_from_neg_one(...))`（k=0取size[3]、k=1取size[2]再unsqueeze_(-1)）与`select(-1,2).fill_(1)`填充；`AT_ASSERT(grad.sizes()=={N,H,W,2})`（VALUE）；view/transpose后`EXEC_NPU_CMD(aclnnBatchMatMul, reassist, grad_view, result, cube_math_type)`（cube_math_type来自get_cube_math_type_with_passthrough）；返回`result.transpose(1,2)` | **前向4/5维、反向仅4维**——5维affine_grid的反向在主线与发布两版本源集内无实现（torch函数层组合回退未核对，不外推）；linspace/mul/div/copy_/fill_均为ATen host分发再落各自NPU实现，是多命令组合而非单命令；_linspace_from_neg_one对num_steps<=1返回`at::tensor(0)`、!align_corners时`range*(n-1)/n` |
| affine_grid_generator_backward（acl_op回退，主线70–86） | 同上同构组合：同样仅4维TORCH_CHECK、同_linspace_from_neg_one与assist填充、同AT_ASSERT；BatchMatMul走ACE命令（attrs bias=0、adj_x1=false、adj_x2=false，无cube_math_type参数）；assist用`apply_tensor`申请（opapi路为without_format） | 两路反向逻辑等价（去空白字符流相同），仅命令通道（aclnn+cube_math_type vs ACE+bias/adj attrs）与申请格式差异 |
| grid_sampler_2d（acl_op，主线23–68） | 仅TORCH_CHECK模式范围`0<=interpolation_mode<=2`、`0<=padding_mode<=2`（VALUE，原文"interpolation_mode must be in range [0~2]."）——**无任何输入形状检查**；self/grid为Half时各自`_npu_dtype_cast`到Float；输出按cast后`{N,C,gH,gW}`（grid.size(1)/size(2)）`apply_tensor_with_format(..., ACL_FORMAT_ND)`申请；ACE命令"GridSampler2D"（interpolation_mode/padding_mode以字符串attr映射bilinear/nearest/bicubic与zeros/border/reflection、align_corners attr）；结果与self dtype不同时cast回 | 形状合法性完全交SDK/ACE（与3d的全套host检查不对称）；_npu_dtype_cast实现在torch_npu仓未核对；FP16输入全程以FP32参与命令再转回 |
| grid_sampler_2d_backward（acl_op，主线23–76） | 同两TORCH_CHECK；grad_output/input/grid三者Half均cast Float；dx按cast后input、dgrid按cast后grid形状`apply_tensor`申请；ACE命令"GridSampler2DGrad"（同字符串attr）；**output_mask参数完全不消费——dx与dgrid恒都计算并返回**；结尾若`dx.dtype != input.dtype`，**dx与dgrid一起cast回input dtype** | dgrid最终dtype跟随input而非grid：input Float/grid Half时dgrid以Float返回、input Half/grid Float时dgrid被降回Half——混合精度用例按此核对；output_mask为false也不省计算 |
| grid_sampler_3d（acl_op，主线40–94） | 模式TORCH_CHECK之外另有完整形状门（均PARAM、消息含实际sizes）：`input.dim()==5且==grid.dim()`、input/grid defined、`input.size(0)==grid.size(0)`、`grid.size(-1)==input.dim()-2`；Half cast同2d；输出按cast后`{N,C,gD,gH,gW}`（grid.size(1)/size(2)/size(3)）申请；ACE命令"GridSampler3D"；结果cast回input dtype | 2d/3d检查面不对称按原文记录：2d把形状交给SDK、3d在host先行拒绝；不从2d可用推断3d宽松或相反 |
| grid_sampler_3d_backward（acl_op，主线23–33） | 入口仅转调`grid_sampler3d_backward_common_nocheck`（声明于utils/custom_functions/aclops/inner_compute.h:26，实现在同目录GridSampler3dBackwardKernelNpu.cpp 22–65）——**output_mask未传入该公共函数**（2d的忽略在函数体内、3d在转发处丢弃）；公共体：三处Half cast→dx/dgrid按cast后形状申请→ACE命令"GridSampler3DGrad"（同字符串attr）→返回 | **无任何cast回**：Half输入返回Float的dx/dgrid，与2d backward的“cast回input dtype”不对称按原文记录——3d反向FP16输入的梯度dtype是Float，迁移脚本显式核对 |

跨族三条：其一，**反向没有统一的专用命令**——affine反向是linspace/填充/BatchMatMul的host组合（aclnn与ACE两通道同构），grid_sampler反向才有专用Grad命令；组合链的命令数与等待需按实际时间线核对。其二，**Half合同三分裂**：2d前/反向“cast进+cast回input dtype”、3d前向“cast进+cast回”、3d反向“cast进不cast回”——dgrid的最终dtype按入口核对，不从forward推backward，也不把任一路当作族规则。其三，**检查面不对称**：2d无形状检查、3d全查；affine前向查size长度、反向仅4维；grid_sampler与affine均无out变体schema（两名族只有functional登记），故本族无CheckOut路径。

迁移F.affine_grid/F.grid_sample时按dim核对：生成层登记的输出尺寸公式与aclops本地推导一致；affine反向仅4维合同——5维affine_grid的反向在主线与发布两版本源集内无实现，不能据前向可用推反向可用。本节静态阅读，未构造网格/稀疏输入、未运行任何命令或数值验证，不新增verified或平台承诺。

### 网格采样补充证据

- [AffineGridGeneratorKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AffineGridGeneratorKernelNpuOpApi.cpp)（primary）：21–44；完整函数体（版权头不重复计行）。
- [AffineGridGeneratorBackwardKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AffineGridGeneratorBackwardKernelNpuOpApi.cpp)（primary）：22–74；完整函数体（含匿名namespace内_linspace_from_neg_one）。
- [AffineGridGeneratorKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AffineGridGeneratorKernelNpu.cpp)（primary）：24–58；完整函数体。
- [AffineGridGeneratorBackwardKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AffineGridGeneratorBackwardKernelNpu.cpp)（primary）：23–86；完整函数体。
- [GridSampler2dKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/GridSampler2dKernelNpu.cpp)（primary）：23–68；完整函数体。
- [GridSampler2dBackwardKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/GridSampler2dBackwardKernelNpu.cpp)（primary）：23–76；完整函数体。
- [GridSampler3dKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/GridSampler3dKernelNpu.cpp)（primary）：24–94；完整函数体（含nocheck helper）。
- [GridSampler3dBackwardKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/GridSampler3dBackwardKernelNpu.cpp)（primary）：23–33；转发入口完整函数体。
- [GridSampler3dBackwardKernelNpu.cpp（utils）d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/GridSampler3dBackwardKernelNpu.cpp)（primary）：22–65；grid_sampler3d_backward_common_nocheck完整函数体；[inner_compute.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/inner_compute.h)（implementation）：26–32；声明。
- [KernelNpuOutputSize.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1679–1693；infersize_affine_grid_generator完整函数体（该文件已列于frontmatter来源）。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：1038–1044、2492–2532；affine两名与grid_sampler四名条目完整字段（该文件已列于frontmatter来源）。
- 发布版本对应9个实现文件（AffineGridGenerator opapi 37行、Backward opapi 64行、AffineGridGenerator aclops 64行、Backward aclops 84行、GridSampler2d 69行、2dBackward 77行、3d 95行、3dBackward 35行、utils 3dBackward 67行，行数见manifest source_meta）：AffineGridGenerator opapi与主线仅排版+尾注释差异（去空白字符流去除尾`// namespace op_api`注释后相同）；其余8文件与主线**去空白字符流相同**；inner_compute.h发布侧同声明（:26）。
- [KernelNpuOutputSize.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1496–1510；发布侧infersize_affine_grid_generator完整函数体（该文件已列于frontmatter来源）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：1000–1006、2413–2453；同条目，与主线逐字相同。
- 负向证据：主线与发布两版本 `op_plugin/ops/opapi/`无GridSampler*/Col2im手写文件（find零命中）；canonical与全部batch*/staged rg `GridSampler2dKernelNpu|AffineGridGeneratorKernelNpuOpApi|grid_sampler3d_backward_common_nocheck` 零命中——本节为该家族首个实现级小节（上文“网格输入”仅docs面）。
