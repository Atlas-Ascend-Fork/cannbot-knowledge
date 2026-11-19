---
type: Guide
title: 原生激活函数的NPU边界：近似算法、dtype与反向
description: 对照GELU近似和兼容路径、SELU FP16梯度、Threshold大整数，以及SiLU等类函数和文档版本差异。并含 _add_relu 生成直发 aclnn 与两命令 acl_op 回退。并含 ELU/CELU、GLU、LeakyReLU 三子族的生成直发、acl_op 回退与 dtype/门槛不对称。并含 Hard* 五子族、Mish/Softplus/LogSigmoid 的手写 opapi 与回退差异，以及原地变体与 PReLU 的申请依据、RNG 来源和回退形态。
tags:
- task.optimization
- topic.precision
- topic.compilation
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
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GeluOutKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuNewParams.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ThresholdKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ThresholdKernelNpu.cpp
  role: implementation
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
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SiluBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SiluBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SiluKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_silu_backward.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_silu.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SiluBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SiluBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SiluKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_silu_backward.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_silu.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LogitKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LogitBackwardKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LogitKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LogitBackwardKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AddReluKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AddReluKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/struct_codegen.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/struct/struct_codegen.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/model.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/struct/model.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/gencode.sh
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/gencode.sh
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_add_relu.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_add_relu.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/GluKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/GluKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/GluBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/GluBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/EluKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/EluKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/EluBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/EluBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/CeluKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/CeluKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LeakyReluKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LeakyReluKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LeakyReluBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LeakyReluBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/HardShrinkKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/HardShrinkKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/HardShrinkBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/HardShrinkBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SoftShrinkKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SoftShrinkKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SoftShrinkBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SoftShrinkBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/HardsigmoidKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/HardsigmoidKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/HardsigmoidBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/HardsigmoidBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/HardSwishKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/HardSwishKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/HardSwishBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/HardSwishBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/HardtanhKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/HardtanhKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/HardtanhBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/HardtanhBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MishKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MishKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MishV2KernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MishV2KernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MishBackwardV2KernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MishBackwardV2KernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SoftplusKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SoftplusKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SoftplusBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SoftplusBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogSigmoidKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LogSigmoidKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogSigmoidBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LogSigmoidBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/HardSwishBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/HardSwishBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MishKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MishKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LogSigmoidNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LogSigmoidNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/SoftplusBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/SoftplusBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/PreluKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/PreluKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/PreluBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/PreluBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ReluKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ReluKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SigmoidKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SigmoidKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/TanhKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/TanhKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RreluWithNoiseKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/RreluWithNoiseKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ErfKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ErfKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ErfcKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ErfcKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ErfinvKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ErfinvKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/TanhKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/TanhKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RReluWithNoiseKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RReluWithNoiseKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/PreluBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/PreluBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/PreluKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/PreluKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/PreluBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/PreluBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/inner_compute.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/inner_compute.h
  role: implementation
created_at: '2026-11-09T10:19:09Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 原生激活函数的NPU边界：近似算法、dtype与反向

## 固定版本与选择顺序

依据TorchNPU固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 中PyTorch2.7.1、2.9至2.14的完整条目，产品为A2/A3训练系列与950DT，具体例外另列，不扩展950PR或发布组合。它们是同一提交中的分版本文档，不将差异直接当作已验证的发行历史。本卡只读审阅，没有执行上游、设备或性能实验。

先保持模型的激活定义、近似方式、dtype及反向需求，再选择对应入口。类与functional的清单差异不能取并集；整数input被列出也不意味着整数能求梯度或任意inplace变换都保持别名语义。

## GELU的公开规格与实际分派

GELU类与F.gelu在七版本列BF16/FP16/FP32、approximate仅tanh；950DT段说明其默认近似算法与上游一致，与A2/A3可能不同，不能用相同函数名保证跨产品结果逐位一致。

静态对照OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的gelu_out：非ACLNN-only且兼容标志关闭时使用aclnnGelu，不将approximate传给它；另一分支使用aclnnGeluV2，由公共helper将none/tanh分别转换为0/1。公开页面“仅tanh”和实现能接收none之间存在范围差异，本卡不据helper扩展公开产品支持，更不能为提速把模型需要的精确GELU随意换成近似。

该out重载以static变量在首次调用保存CheckCompatibleImpl结果；运行中修改开关不证明它会重新读取。这里只说明该重载，不推断所有GELU重载、后端和CANN有相同缓存时机；两主线不是已配套运行的组合。

## SELU梯度与Threshold整数精度

F.selu列FP16/FP32；来源提示FP16反向相对GPU有累加误差，给出的规避思路是在正向使用aten.elu并保留SELU的alpha≈1.6732632423543773、scale≈1.0507009873554805。它不是默认alpha=1的普通ELU替换，也不是本卡已验证的数值修复；必须同时比较前向与梯度，并保留模型原定义。SELU类另列FP64、整数和BOOL，不能用类的宽表解除functional的FP16反向条件。

F.threshold/threshold_列INT32值超过2^24（16777216）可能损失精度；dtype仍为INT32不保证值精确。所读opapi包装直接调用aclnnThreshold/aclnnInplaceThreshold，兼容路径使用ThresholdV2D；框架这几段未展示导致损失的Kernel内部转换，不把2^24警告自行归因成已确认的某次FP32 cast。

## BF16与类/函数差异

| 入口 | 清单中的差异 |
| --- | --- |
| SiLU类 | BF16/FP16/FP32 |
| F.silu | 2.7.1、2.9、2.10页列BF16/FP16/FP32；2.11..2.14页仅FP16/FP32 |
| Mish类 / F.mish | 类仅FP16/FP32，函数另列BF16 |
| Softshrink类 / F.softshrink | 类列BF16/FP16/FP32，函数仅FP16/FP32 |
| PReLU类 / F.prelu | 类仅FP32，函数列FP16/FP32且input仅1..8维 |
| GLU类 / F.glu | 类仅FP16/FP32，函数列BF16/FP16/FP32/FP64 |
| Softmax及F.softmax | BF16/FP16/FP32/FP64 |
| LogSoftmax及F.log_softmax、Softmax2d、Softmin类 | BF16/FP16/FP32；不向F.softmin补写未列的细表 |

以上是条目差异而非按相似实现推导出的新能力。没有BF16条目的路线保留独立确认，不能仅凭模型已经autocast就将所有激活统一转换。

## 其他类型与回退边界

ELU/LeakyReLU及对应functional列BF16、FP16/32/64；Hardtanh/ReLU6及functional还列UINT8、INT8/16/32/64。ReLU、F.relu/relu_列BF16/FP16/FP32、UINT8、INT8/INT32/INT64，没有同一INT16条目。

Sigmoid类列BF16、FP16/FP32、UINT8、INT8/16/32/64、BOOL、complex64/128，F.sigmoid没有其中的BF16；Tanh类列BF16、FP16/FP32、同一整数/BOOL集合，F.tanh也未列BF16。Softsign及functional列BF16、FP16/FP32、UINT8、INT8/16/32/64，不把复数或BOOL从其他激活并入。

CELU、LogSigmoid、Hardshrink、Hardswish及对应functional的input基本列FP16/FP32；Hardsigmoid类额外列INT32，F.hardsigmoid仅FP16/FP32。Hardshrink类、Hardsigmoid类、Tanhshrink类与F.hardswish标注可能CPU回退，其他相似入口未重复该句不能证明完全无Host活动。Tanhshrink类的input另列UINT8、INT8/16/32/64；F.tanhshrink只列产品，未给另一份完整类型表。

## RReLU产品差异

RReLU类位于A2/A3条件段，950DT行写不支持；F.rrelu_也将950DT标为不支持。F.rrelu非原地入口却列950DT支持、input为BF16/FP16/FP32。不能因为数学函数相似就把原地/类的950限制删除，或把未支持的重载等同于所有RReLU入口都不可用。

F.gumbel_softmax等仅列产品或无额外类型细表，支持标记不替代随机性、参数与梯度验证。本文未以缩减dtype、启用兼容路径或少量节点替换宣称收益。

- [Dropout类型与产品限制](torch_npu_native_dropout_scope.md)
- [CPU回退与兼容实现](../../inference/guides/optimization/torch_npu/torch_npu_cpu_fallback_and_compatible_impl.md)

## 另列的原地激活入口

七版本页对F.hardtanh_列input为FP16/FP32、INT8/16/32/64，F.elu_仅FP16/FP32，F.leaky_relu_列FP16/32/64，产品为A2/A3训练系列和950DT。它们没有与非原地入口相同的BF16/UINT8等并集，不能仅改变函数后缀就假定dtype、别名、反向或入图行为都相同。需要保持原模型写回/消费者语义后独立验证，本卡未执行原地修改。

## SiLU的真实前后向与原地路径

以下小节只依据 OpPlugin 主线d84e9b1d6a558e5f27973cd4329f62968e46fdda和发布dedc316708372c9a8bfde4527abd2a94b74840f5的本地包装、Schema与测试，未执行生成器、OpCommand、ACLNN、自动梯度或设备。原文公开文档的status/platforms与dtype清单保持原范围；新的分配、命令和枚举分支不构成另一份产品支持认证，也不能用源码枚举解除上表F.silu的BF16文档限制。

### 前向Schema和ACL原地实现并不相同

两版的silu/silu.out/silu_都列ACL与OpAPI。Schema中functional和inplace通过structured_inherit指向silu.out，out配置的size/dtype按self、exec为aclnnSilu；这说明所选配置的生成意图，本卡没有读取或执行全部生成器来认证最终C++与运行分派。主线另对silu和silu_backward列dvm，发布这些条目不含该标签；不能由局部标签缺失推导发布完全没有DVM能力。

读取的ACL实现以Swish命令、scale=float(1.0)执行前向。functional silu与custom npu_silu共用按self申请结果的helper。out路径先CheckOut；result不匹配本地格式时申请format_contiguous临时对象、执行后format_fresh_view，否则直接输出result。这些外部格式helper的完整复制/别名协议另计，不能只看返回引用就假定没有额外工作。

普通ACL silu_先调用functional helper生成临时result，再self.copy_(result)并返回self；custom npu_silu_则把self作为输入和输出交给out helper。前者明确有本地结果申请与copy_，后者仍可能触发上述格式整理；“原地”不能自动等同于没有临时存储。这是该ACL分支的差异，不把它套到尚未实际生成检查的OpAPI inplace实现。custom npu_silu/npu_silu_/npu_silu_backward的所选Schema仅列acl_op。

### 两输入ATen后向与三输入custom后向

ATen silu_backward及grad_input重载的OpAPI先做aclnnSiluBackward兼容分派。SoC枚举小于Ascend950时，functional按grad_output申请无格式结果，out重载执行check_tensor({grad_output,self},result,grad_output)。大于等于该枚举时，functional把grad_output与self交给broadcast_ops_npu_output_size推shape；两者dtype相同保留grad_output dtype，不同则显式申请FP32，设备选项取self。这个out重载在该枚举区间不走上述本地check_tensor，直接把传入result交ACLNN。

这些是本地shape/dtype申请和校验分支；广播helper、SDK完整输入限制及任意混合dtype的执行支持没有在这里核对，跳过一处check不等于任意out对象都安全。两种重载都返回自己的结果句柄；本卡没有运行广播、混合dtype或out用例。

ACL兼容的ATen后向使用SiluGrad，输入只有grad_output与self。functional按grad_output调用apply_tensor；out走CheckOut后直接交命令，没有把OpAPI的>=Ascend950广播/FP32申请规则复制进来。另一个custom npu_silu_backward接收grad_output/x0/x1，申请依据同为grad_output，却调用**三输入SwishGrad**。应核对实际Schema和参数，不能因名字相似就把这两个后向入口当作同一调用合同或互换两/三个输入。

### 小型测试的覆盖边界与双版本差异

前向测试比较F.silu的FP16和FP32，FP16使用FP32 CPU参考后转回FP16；FP32列格式0/3/4/29，FP16仅格式0。测试里的显式原地入口是custom npu_silu_，不是普通ATen silu_。因此不能借前向原地测试证明普通ACL silu_一定不分配临时结果。

反向测试通过F.silu(...).sum().backward()及全局hook比较FP32输入梯度，还包括as_strided([2,2],[1,2],1)视图。inplace训练用例调用nn.SiLU(inplace=True)，先构造x+0.1再mean().backward()，比较输出和原x梯度；并没有对叶子x直接做原地SiLU。所列测试没有BF16、混合输入dtype、不同shape广播、显式grad_input重载或直接调用三输入custom backward，源码用例存在也不是本卡设备通过证据。

两版OpAPI后向和ACL后向的完整phase2 token相同，主线多匿名/命名namespace尾注。ACL前向两版完整函数体同token，唯一额外token顺序差异是两个未使用autograd using声明的对调，全部注释相同；其余是排版。两个测试逐字节相同。版本局部一致不外推为底层CANN相同或产品均支持。

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
- [固定来源 15](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GeluOutKernelNpuOpApi.cpp)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuNewParams.cpp)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ThresholdKernelNpuOpApi.cpp)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ThresholdKernelNpu.cpp)（implementation）

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

## SiLU包装与测试的新增固定来源

- [SiluBackwardKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SiluBackwardKernelNpuOpApi.cpp)（implementation）：1–50；完整本地小文件。
- [SiluBackwardKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SiluBackwardKernelNpu.cpp)（implementation）：1–43；完整本地小文件。
- [SiluKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SiluKernelNpu.cpp)（implementation）：1–101；完整本地小文件。
- [test_silu_backward.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_silu_backward.py)（example）：1–97；完整本地小文件。
- [test_silu.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_silu.py)（example）：1–83；完整本地小文件。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：4652–4681、6936–6943；仅所选完整Schema条目。
- [SiluBackwardKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SiluBackwardKernelNpuOpApi.cpp)（implementation）：1–51；完整本地小文件。
- [SiluBackwardKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SiluBackwardKernelNpu.cpp)（implementation）：1–55；完整本地小文件。
- [SiluKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SiluKernelNpu.cpp)（implementation）：1–123；完整本地小文件。
- [test_silu_backward.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_silu_backward.py)（example）：1–97；完整本地小文件。
- [test_silu.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_silu.py)（example）：1–83；完整本地小文件。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：4500–4527、6736–6743；仅所选完整Schema条目。

## Logit前后向：显式CPU路线与原位委托

两版Logit包装的CPU选择取决于静态双符号探测和SoC枚举门控，**没有额外的Double类型门控**。前后向分别探测aclnnLogit/aclnnLogitGrad，SoC条件均为`[Ascend910B1, Ascend310B1)`或`>Ascend310B4`；不能把枚举大小直接替换为未经核实的产品支持集合。

| 入口 | CPU分支 | SDK分支 |
| --- | --- | --- |
| functional前向 | self.cpu后调用at::native::logit，结果to(self.device) | 按self shape/dtype申请，执行aclnnLogit |
| out前向 | self和已有out都cpu，CPU out之后copy回原out | 按self shape/dtype检查out后执行SDK |
| functional反向 | grad_output与self都cpu，CPU反向后to(grad_output.device) | shape取self，options取grad_output并将dtype设为self.dtype，再执行aclnnLogitGrad |
| out反向 | grad_output/self/grad_input都cpu，CPU out后copy回原grad_input | 输出检查使用self shape/dtype；传SDK的顺序为self、grad_output、eps、grad_input |

CPU分支发生在上述正常申请/输出检查之前，并保留optional eps交CPU接口；SDK把缺省eps变为-1。显式代码没有为了CPU慢路统一转Float。`logit_`本地仅委托`at::native::logit_(self, eps)`，没有调用同一个fallback helper或显式.cpu；不能因warning提到了原位名字就说原位必走表中CPU链。

两版活动代码的phase2 token与有序include指令逐项核对相同；除主线多出的namespace尾注释外其余注释相同，其余差异只是排版（大括号、缩进、引用写法空格），两版行尾同为CRLF，这些差异不改变上述分支。双符号的静态可见性不证明任意dtype/shape能够执行；这也是显式CPU门控，不套普通DO_COMPATIBILITY的AclnnOnly抛错规则。原激活支持页和SiLU测试/实现保持独立，此处没有运行Logit或量化传输耗时。

### Logit补充证据

- [LogitKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LogitKernelNpuOpApi.cpp)（implementation）：1–60；完整本地小文件。
- [LogitBackwardKernelOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LogitBackwardKernelOpApi.cpp)（implementation）：1–63；完整本地小文件。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：5546–5560；仅logit五条Schema。
- [op_api_common.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp)（implementation）：767–773；仅双符号探测helper。
- [LogitKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LogitKernelNpuOpApi.cpp)（implementation）：1–63；完整本地小文件。
- [LogitBackwardKernelOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LogitBackwardKernelOpApi.cpp)（implementation）：1–61；完整本地小文件。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：5377–5391；仅logit五条Schema。
- [op_api_common.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.cpp)（implementation）：785–792；仅双符号探测helper。

## _add_relu：生成直发 aclnn 与两命令 acl_op 回退

aten::_add_relu 是 ATen 内部的「加法后接 ReLU」入口（Schema 默认 `alpha=1`，functional/out/inplace 三个重载）。主线与发布两版本 yaml（主线 74–93、发布 74–93）登记同一语义：三个重载均同时列 acl_op all_version 与 op_api all_version；`_add_relu.Tensor`/`_add_relu.out` 的 gen_opapi exec 为 aclnnAddRelu（仅 `.Tensor` 另注 out size/dtype=self），`_add_relu_.Tensor` 为 aclnnInplaceAddRelu。op_api 侧没有手写包装文件：gencode.sh 第 68–71 行以 `torchnpugen.struct.gen_struct_opapi` 把生成分片写到 `op_plugin/ops/opapi/`，生成代码不随仓提交。本卡按主线与发布两版本 生成器模板静态推导下表行为，未运行 gencode 认证最终产物。

| 重载 | 生成的 op_api 路径（主线模板 33–46 推导） | acl_op 回退（AddReluKernelNpu.cpp 24–66） |
| --- | --- | --- |
| `_add_relu.Tensor` | DO_COMPATIBILITY 后按 `self.sizes()`/`self.scalar_type()` 用 `apply_tensor_without_format` 申请输出，单次 `EXEC_NPU_CMD(aclnnAddRelu, self, other, alpha, out)` | `apply_tensor(self)`（57）→ `acl_op::add(self, other, alpha)`（29，其自身 NPU 分派未核对）+ 单独 OpCommand "Relu"（30–31）：host 侧两段执行，不等于 device 侧恰好两个 kernel |
| `_add_relu.out` | yaml 未注 out 规格：`check_tensor({self, other}, out, out.scalar_type(), out.sizes())` 自洽校验后 `EXEC_NPU_CMD(aclnnAddRelu, self, other, alpha, out)` | `CheckOut({self, other}, out, self)`（41）；`check_match(&out)` 不匹配时先 `format_contiguous` 临时对象执行、再 `format_fresh_view` 刷新（43–46），匹配则直接执行 |
| `_add_relu_.Tensor` | `EXEC_NPU_CMD(aclnnInplaceAddRelu, self, other, alpha)` 后返回 self | 直接委托 `acl_op::_add_relu_out(self, …, self)`（66），继承上一行的校验与格式整理分支 |

DO_COMPATIBILITY（主线 op_api_common.h 94–117，发布 96–116 同语义）以函数级 static 探测 aclnnAddRelu（inplace 为 aclnnInplaceAddRelu）与其 GetWorkspaceSize 两个符号：缺失且 Aclnn-only 模式下 TORCH_CHECK 抛 "Current device only support aclnn operators, but ..."；非 Aclnn-only 则 ASCEND_LOGW 警告并整函数 `return acl_op::` 同名实现。EXEC_NPU_CMD（主线 343–492）再 TORCH_CHECK 符号存在，按 task-queue 选项选 V1/V2，workspace 非零时 `unsafe_empty_workspace` 分配，`RunOpApiV2` 异步下发；host 侧无逐元素逻辑，「融合」语义由 aclnn 符号名承载，其内核内部实现未核对。「单次 aclnn 调用」只说明 host 侧执行形态，不构成 device kernel 数量或性能承诺；生成路与回退路申请输出的 helper 名称也不同（apply_tensor_without_format vs apply_tensor，内部格式语义未逐一读取）。

源内测试 test_add_relu.py（主线与发布两版本 字节相同，218 行）静态覆盖 functional/out/inplace 与 alpha=1/3，FP16/FP32、格式 0/3/29，FP16 用 FP32 CPU 参考后比对；测试存在不构成本卡运行证据，未执行任何用例。

主线与发布两版本 差异如实：yaml 三条目语义等价（发布仅第 93 行 exec 缩进多两格）；aclops 文件仅排版差异（主线 68 行/发布 72 行，去空白字符流相同）；生成器主线 503 行/发布 296 行差异较大（主线新增 integral_identity/cpu_scalar 等特性），但 _add_relu 条目不含相关键，主线与发布两版本 对这三个入口生成同形代码；gencode.sh 的 gen_struct_opapi 调用段主线与发布两版本 相同。以下未核对：生成的 C++ 最终产物未运行认证；aclnnAddRelu/aclnnInplaceAddRelu 的内核语义与 dtype 支持范围在 CANN 侧未核对；`check_tensor`/`CheckOut` 的内部校验语义在 torch_npu OpPreparation，本卡未核对；aclnn 符号在哪些 CANN/SoC 组合缺失不在源内；未做设备验证。

### _add_relu 补充证据

- [AddReluKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AddReluKernelNpu.cpp)（implementation）：1–68；完整本地小文件。
- [AddReluKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AddReluKernelNpu.cpp)（implementation）：1–72；完整本地小文件，与主线去空白字符流相同（仅排版）。
- [struct_codegen.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/struct_codegen.py)（implementation）：30–480；生成模板/过滤/compute_op_api_definition 定向逐字。
- [struct_codegen.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/struct/struct_codegen.py)（implementation）：30–100、178–195；模板与 do_compatibility/exec_cmd 定向读。
- [model.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/model.py)（implementation）：159–189、200–272；返回参数与 cmd_args 展开定向读。
- [model.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/struct/model.py)（implementation）：60–96、190–249；ResInfo 解析/返回参数/cmd_args 展开定向读。
- [op_api_common.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）：60–160、330–500；DO_COMPATIBILITY 与 EXEC_NPU_CMD_V1/V2 定向逐字。
- [op_api_common.h dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）：92–116、435–445；DO_COMPATIBILITY 与 EXEC_NPU_CMD 定向读。
- [gencode.sh d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/gencode.sh)（implementation）：1–79；完整本地小文件，第 68–71 行为 gen_struct_opapi 调用。
- [gencode.sh dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/gencode.sh)（implementation）：1–73；完整本地小文件，gen_struct_opapi 调用与主线相同（其余差异为 minor 版本与 atb 段）。
- [test_add_relu.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_add_relu.py)（example）：1–218；完整本地小文件。
- [test_add_relu.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_add_relu.py)（example）：1–218；与主线字节相同。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：74–93；仅 _add_relu 三条完整条目（该文件已列于 frontmatter 来源）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：74–93；仅 _add_relu 三条完整条目，第 93 行缩进多两格（该文件已列于 frontmatter 来源）。

## ELU/CELU、GLU 与 LeakyReLU 的生成直发与 acl_op 回退

本节核对激活主题级 67 名中的三个子族：ELU/CELU（7 名）、GLU（4 名）、LeakyReLU（5 名），共 16 名，其余子族维持 UNASSESSED 不因本节核对。主线与发布两版本 yaml 对 16 名都登记 acl_op+op_api all_version；除 `leaky_relu_backward.grad_input`（主线与发布两版本 均仅 op_api、无 acl_op 行）外均为 gen_opapi exec 直发 aclnn，生成器模板、DO_COMPATIBILITY 与 out 类缺省 dtype 的自洽规则复用 _add_relu 小节已核对的结构（yaml/struct_codegen.py/model.py 已列于 frontmatter 来源），本节不重复展开。文档表的 elu/glu/leaky_relu dtype 行保持原范围，此处只补实现层。

| 入口 | gen_opapi（主线与发布两版本 同语义） | acl_op 回退（aclops，主线与发布两版本 语义等价） |
| --- | --- | --- |
| elu | out size/dtype=self，exec aclnnElu | `apply_tensor(self)` 后单 OpCommand "Elu" |
| elu.out | 只注 size=self、dtype 缺省→out 自身 dtype 自洽，exec aclnnElu | CheckOut({self},out,self)+check_match/format_contiguous/format_fresh_view |
| elu_ | exec aclnnInplaceElu | check_match 分支计算 result 后 `self.copy_(result)`（本地复制，同 SiLU ACL 分支型）；非匹配分支 format_contiguous+format_fresh_view |
| elu_backward | out size/dtype=grad_output，exec aclnnEluBackward | `apply_tensor(grad_output)`；OpCommand "EluGradV2" |
| elu_backward.grad_input | 只注 size=grad_output、dtype 缺省自洽 | 同上；`is_result` 且 alpha<0 时 TORCH_CHECK 抛「原地前向负斜率不可反传」 |
| celu | out size/dtype=self，exec aclnnCelu | `apply_tensor(self)`；OpCommand "CeluV2" |
| celu_ | exec aclnnInplaceCelu | 与 elu_ 相同的 copy_/格式分支模式 |
| glu | out size=`glu_npu_output_size(self,dim)`（wrap 后 `shape[dim]/2` 整数除）、dtype=self，exec aclnnGlu | 前向先 TORCH_CHECK self.dim()>0、折半维为偶数，再 `apply_tensor(self, output_size)`；OpCommand "GLU" |
| glu.out | 只注 size=`glu_npu_output_size`、dtype 缺省自洽，exec aclnnGlu | 同样先做两个 TORCH_CHECK；CheckOut({self},out,self,output_size)+格式分支 |
| glu_backward | out size/dtype=self，exec aclnnGluBackward | `apply_tensor(self)`；OpCommand "GLUGrad" |
| glu_backward.grad_input | grad_input size=self、**dtype=grad_output**，exec aclnnGluBackward | CheckOut({grad_output,self},grad_input,grad_output,input_same_output_size(self))+格式分支 |
| leaky_relu | structured_inherit 指向 out 规格，exec aclnnLeakyRelu | `apply_tensor(self)`；OpCommand "LeakyRelu" |
| leaky_relu.out | out size/dtype=self，exec aclnnLeakyRelu | CheckOut({self},out,self)+格式分支 |
| leaky_relu_ | exec aclnnInplaceLeakyRelu | 直接委托 `leaky_relu_out(self,…,self)`，继承校验与格式整理 |
| leaky_relu_backward | out size/dtype=self，exec aclnnLeakyReluBackward | `apply_tensor(self)`；OpCommand "LeakyReluGrad"；**签名收到的 is_result 未传给命令** |
| leaky_relu_backward.grad_input | 主线与发布两版本 仅 op_api；grad_input 只注 size=self、dtype 缺省自洽，exec aclnnLeakyReluBackward | aclops 文件只有 functional 实现，无 out 变体可回退 |

三条需要单独记录的门槛差异：

1. **GLU 偶数与 0 维检查只在 acl_op 回退**。生成的 op_api 路径直接以 `glu_npu_output_size` 的整数除计算输出（奇数折半维静默向下取整）后直发 aclnnGlu；「折半维必须为偶数」「不支持 0 维」两条 TORCH_CHECK 都在 aclops 包装内。aclnnGlu 缺失时回退路会对奇数维抛错而直发路不会；aclnnGlu 内核对奇数维的行为未核对，不据此宣称直发路可用奇数维。
2. **glu_backward 两个重载的输出 dtype 来源不同**：functional 按 self（gen dtype=self、aclops `apply_tensor(self)`）；`.grad_input` 重载按 grad_output（gen dtype=grad_output、aclops CheckOut 模板亦为 grad_output）。grad_output 与 self dtype 不同时，两个重载产出/接受的梯度 dtype 不同；aclnnGluBackward 能否实际接受混合 dtype 属设备侧未核对。acl_op 包装 `apply_tensor(grad_output)` 只出现在 elu_backward（按 grad_output），与 glu 的按 self 相反，两个家族不能互换申请依据。
3. **标量 attr 编码不同**：ELU 把 alpha/scale/input_scale 经 `get_scalar_float_value` 收窄为 float 后传 OpCommand，CeluV2/LeakyRelu 的 Scalar 原样传；直发路径把 Schema Scalar 原样交 aclnn 命令。仅提示两条路径 attr 编码差异，不改变源码参数类型。

版本与标记：`leaky_relu`/`leaky_relu_` 在主线 yaml 另带 `dvm: all_version`，发布无该标记；DVM 路径的 LeakyReLU 表达式与 leaky_relu_ 的 LazyFusionFlush 已由 [DVM 逐元素卡](../../inference/guides/optimization/torch_npu/torch_npu_eager_dvm_elementwise_precision_and_fallback.md)核对，本节不重复。本节 16 名的 aclops 文件主线与发布两版本 语义等价（Elu/EluBackward/Celu 仅排版差异，LeakyRelu 两对去空白 token 流相同）；SELU 小节已建议的「前向用 aten.elu」现在有了实现层依据：elu 前后向均为单命令直发/回退，无显式 CPU 路径，但 950/产品组合的可执行性仍需按该节原口径核对。

### ELU/CELU、GLU、LeakyReLU 补充证据

- [GluKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/GluKernelNpu.cpp)（implementation）：1–76；完整本地小文件。
- [GluKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/GluKernelNpu.cpp)（implementation）：1–76；与主线去空白 token 流相同。
- [GluBackwardKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/GluBackwardKernelNpu.cpp)（implementation）：1–78；完整本地小文件。
- [GluBackwardKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/GluBackwardKernelNpu.cpp)（implementation）：1–78；与主线去空白 token 流相同。
- [EluKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/EluKernelNpu.cpp)（implementation）：1–88；完整本地小文件。
- [EluKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/EluKernelNpu.cpp)（implementation）：1–96；仅排版差异。
- [EluBackwardKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/EluBackwardKernelNpu.cpp)（implementation）：1–82；完整本地小文件。
- [EluBackwardKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/EluBackwardKernelNpu.cpp)（implementation）：1–80；仅排版差异。
- [CeluKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/CeluKernelNpu.cpp)（implementation）：1–53；完整本地小文件。
- [CeluKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/CeluKernelNpu.cpp)（implementation）：1–57；仅排版差异。
- [LeakyReluKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LeakyReluKernelNpu.cpp)（implementation）：1–66；完整本地小文件。
- [LeakyReluKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LeakyReluKernelNpu.cpp)（implementation）：1–66；与主线去空白 token 流相同。
- [LeakyReluBackwardKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LeakyReluBackwardKernelNpu.cpp)（implementation）：1–49；完整本地小文件。
- [LeakyReluBackwardKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LeakyReluBackwardKernelNpu.cpp)（implementation）：1–49；与主线去空白 token 流相同。
- [KernelNpuOutputSize.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1344–1358、1612–1616；仅 glu_npu_output_size 与 repeat_npu_output_size 两个 helper。
- [KernelNpuOutputSize.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1191–1204、1427–1431；同两个 helper，语义与主线相同。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：1616–1629、1995–2033、2457–2490、2925–2961；仅本节 16 名 Schema 条目（该文件已列于 frontmatter 来源）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：1557–1566、1932–1972、2378–2411、2837–2872；同 16 名条目，发布无 dvm 标记（该文件已列于 frontmatter 来源）。

## Hard* 五子族与 Mish/Softplus/LogSigmoid：直发、手写与回退的三层差异

本节核对激活主题级 67 名中的其余 34 名：Hard* 五子族 21 名（hardshrink 4、hardsigmoid 4、hardswish 4、hardtanh 5、softshrink 4）、Mish 4 名、Softplus 3 名、LogSigmoid 6 名；最后 17 名原地/补充名见下一节。主线与发布两版本 yaml 对 34 名均登记 acl_op+op_api（个别 gen 直发规格见表）；上层文档表（Hardshrink/Hardsigmoid/Hardswish/Hardtanh 的可能 CPU 回退标注、F.hardsigmoid 仅 FP16/FP32 等）保持原范围，本节只补实现层。生成路径的模板/DO_COMPATIBILITY 语义复用 _add_relu 小节已核对的结构，不重复展开。

| 入口 | gen_opapi（主线与发布两版本 同语义） | acl_op 回退（aclops，主线与发布两版本 语义等价） |
| --- | --- | --- |
| hardshrink | out size/dtype=self，exec aclnnHardshrink | `apply_tensor(self)`；OpCommand "HardShrink"（lambd 为 attr） |
| hardshrink.out | 只注 size=self、dtype 缺省自洽 | CheckOut({self},out,self)+check_match/format 分支 |
| hardshrink_backward | grad_input size=`broadcast_ops_npu_output_size(grad_out,self)`、dtype=`result_type(grad_out,self)`，exec aclnnHardshrinkBackward | `apply_tensor(self)`；OpCommand "HardShrinkGrad"；**out 变体无 check_match/format 分支**，直写传入 grad_input |
| hardshrink_backward.grad_input | 同上 size、dtype 缺省自洽 | 同一 `hardshrink_backward_out` 实现（functional 委托它） |
| hardsigmoid | structured_inherit 指向 out 规格 | `apply_tensor(self)`；"HardSigmoid" |
| hardsigmoid.out | size/dtype=self，exec aclnnHardsigmoid | CheckOut+格式分支 |
| hardsigmoid_ | exec aclnnInplaceHardsigmoid | 委托 `hardsigmoid_out(self,self)`，继承校验与格式分支 |
| hardsigmoid_backward | out size=self、**dtype=`result_type(grad_output,self)`**，exec aclnnHardsigmoidBackward | **`apply_tensor(grad_output)`（按 grad_output 申请）**；"HardSigmoidGrad" |
| hardswish | structured_inherit 指向 out 规格 | `apply_tensor(self)`；"HardSwish"；hardswish_ 委托 `hardswish_out(self,self)` |
| hardswish.out | size/dtype=self，exec aclnnHardswish | CheckOut({self},result,self)+格式分支；**不匹配分支实参顺序与 hardsigmoid 不同**：`hardswish_out_nocheck(contiguous_result, result)`——self 形参位传入的是 result 而非 self（hardsigmoid 同分支为 `(contiguous_result, self)`）。本卡只记录主线与发布两版本 一致存在的字面绑定顺序，不推断运行后果 |
| hardswish_ | exec aclnnInplaceHardswish | 委托 `hardswish_out(self,self)` |
| hardswish_backward | **无 gen_opapi：手写 opapi 文件**（见下） | 两个 VERSION_BETWEEN 分支：V1R11–V2R7 单命令 "HardSwishGrad"；V2R8+ "HardSwishGrad" 后追加 `at::empty`×2+`acl_op::fill_`(0.0f/1.0f)+`self.eq(∓3.0f)`+`index_put_` 的 ±3 边界掩盖组合 |
| hardtanh | structured_inherit 指向 out 规格 | functional `apply_tensor(self)` 后仍走 `hardtanh_out`；**OpCommand "ClipByValue"，min/max 以 `self.scalar_type()` 标量输入而非 attr**；hardtanh_ 委托 `hardtanh_out(self,…,self)` |
| hardtanh.out | size/dtype=self，exec aclnnHardtanh | CheckOut+格式分支 |
| hardtanh_ | exec aclnnInplaceHardtanh | 委托 `hardtanh_out(self,…,self)` |
| hardtanh_backward | structured_inherit 指向 .grad_input | `apply_tensor(self)`；"HardtanhGrad"（self、grad_output 输入序；min/max 为 attr） |
| hardtanh_backward.grad_input | grad_input size/dtype=self，exec aclnnHardtanhBackward | CheckOut({grad_output,self},grad_input,self)+格式分支 |
| softshrink | size/dtype=self，exec aclnnSoftshrink | **TORCH_CHECK lambd≥0（functional 与 out 均有）**；`apply_tensor(self)`；"SoftShrink" |
| softshrink.out | 只注 size=self、**dtype=out** | 同上 TORCH_CHECK；CheckOut({self},result,self)+格式分支 |
| softshrink_backward | grad_input size=`broadcast_ops_npu_output_size`、dtype=`result_type`，exec aclnnSoftshrinkBackward | `apply_tensor(self)`；"SoftShrinkGrad" |
| softshrink_backward.grad_input | 同上 size、dtype=grad_input 缺省自洽 | CheckOut({self,grad_output},grad_input,self)+格式分支 |
| mish | **无 gen_opapi：手写 opapi** `apply_tensor(self)`+EXEC aclnnMish | aclops `mish_out` CheckOut({self},result,self)+格式分支；functional 委托；另有 MishKernelNpu.cpp 提供 npu_mish/npu_mish_backward（"Mish"/"MishGrad"） |
| mish.out | 手写 `mish_out`：CheckOut({self},result,self) 后 EXEC aclnnMish，**无 check_match/format 分支** | CheckOut+格式分支（"Mish"） |
| mish_ | 手写 DO_COMPATIBILITY(aclnnInplaceMish)；EXEC aclnnInplaceMish(self) | 委托 `mish_out(self,self)` |
| mish_backward | out size=`broadcast_ops_npu_output_size(grad_output,self)`、dtype=`result_type(grad_output,self)`，exec aclnnMishBackward | `apply_tensor(self)`；"MishGrad" |
| softplus | structured_inherit 指向 out 规格 | `apply_tensor(self)`；"SoftplusV2"（beta/threshold 为 attr） |
| softplus.out | size/dtype=self，exec aclnnSoftplus | CheckOut+格式分支 |
| softplus_backward.grad_input | **仅注 exec aclnnSoftplusBackward（无 out 规格）** | CheckOut({grad_output,self},grad_input,self)+格式分支；命令为 inner_compute 的 `softplus_backward_out_common_nocheck`（"SoftplusV2Grad"） |
| log_sigmoid | **手写 opapi（无 gen）**：委托 `at::log_sigmoid_forward` 取第一个输出 | 同构委托（acl_op 版 forward 无 CheckOut） |
| log_sigmoid.out | 手写：`check_tensor({self},out,self)` 后构造零元素 buffer，**以 `at::log_sigmoid_forward_out(out, buffer, self)` 调用**——该函数签名为 (self, output, buffer)，字面绑定把用户 out 绑到 self 位、零元素 buffer 绑到 output 位、原输入绑到 buffer 位，并返回该调用的第一个输出 | aclops `log_sigmoid_out` 同样以 `(result, buffer, self)` 顺序调用 forward_out（acl_op 版 forward_out 对 output 与 buffer 都做 CheckOut）。本卡只记录主线与发布两版本 一致存在的字面绑定顺序；check_tensor/CheckOut 对零元素 buffer 的实际校验行为未核对、未执行，不判定运行后果 |
| log_sigmoid_backward | structured_inherit 指向 .grad_input | `apply_tensor(grad_output)`；"LogSigmoidGrad"；CheckOut({grad_output,self},grad_input,grad_output)+格式分支（校验/申请按 grad_output） |
| log_sigmoid_backward.grad_input | grad_input size/dtype=grad_output，exec aclnnLogSigmoidBackward | 同上 |
| log_sigmoid_forward | **手写 opapi**：out=`apply_tensor_without_format(self)`、**buffer=`apply_tensor_with_sizes({0},…)` 零元素**；EXEC aclnnLogSigmoidForward | acl_op 版：output=`apply_tensor(self)`、buffer 同为零元素；直接 nocheck |
| log_sigmoid_forward.output | 手写：`check_tensor({self},out,self)`（**buffer 不做 check**）；同命令 | acl_op 版对 output 与 buffer 都 CheckOut |

三条需要单独记录的差异：

1. **手写 LogSigmoid 的探测与执行符号不同**：三个入口的 DO_COMPATIBILITY 探测 `aclnnLogSigmoid`，实际 EXEC 的是 `aclnnLogSigmoidForward`。aclnnLogSigmoid 存在而 aclnnLogSigmoidForward 缺失（或相反）时，该 DO_COMPATIBILITY 门不拦截，EXEC_NPU_CMD 自身的符号 TORCH_CHECK 才会失败；本卡不据此推断任一符号的实际存在性。
2. **hardswish_backward 的主线与发布两版本 行为差异**：主线手写 opapi 在 V2R8+ 分支先用函数级 static `check_aclnn_kernel_available("aclnnHardswishBackwardV2")` 探测，可用即单命令 aclnnHardswishBackwardV2；不可用才走 aclnnHardswishBackward+index_put_ 组合。**发布版本 无该探测**，V2R8+ 恒为 aclnnHardswishBackward+组合。输出申请主线与发布两版本 一致：按 self.sizes()/self.scalar_type() 以 grad_output options 申请（apply_tensor_without_format）。
3. **反向申请依据在两条路径间普遍不对称**：hardsigmoid_backward gen 用 `result_type(grad_output,self)` 而 aclops 按 grad_output `apply_tensor`；hardtanh/mish/hardshrink/softshrink 反向 gen 用 broadcast/result_type 而 aclops 一律按 self `apply_tensor`。grad_output 与 self 形状/dtype 不同时，两条路径产出的梯度 dtype/形状依据不同；aclnn 侧能否接受这些差异未核对。

Mish 的手写 opapi 三入口均带 DO_COMPATIBILITY（mish/mish_out 探测 aclnnMish、mish_ 探测 aclnnInplaceMish）；MishV2 的 aclops 三个变体与 MishKernelNpu.cpp 的 npu_mish 系列是两套并存实现（前者承接 ATen 调度，后者为 npu_ 前缀 custom 侧），本节不混用。SELU 小节建议的 aten.elu 替换与本卡 ELU 事实互补，hard* 家族不改变该建议的适用条件。

### Hard*、Mish/Softplus/LogSigmoid 补充证据

- [HardShrinkKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/HardShrinkKernelNpu.cpp)（implementation）：1–67；完整本地小文件。
- [HardShrinkKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/HardShrinkKernelNpu.cpp)（implementation）：1–67；与主线字节相同。

- [HardShrinkBackwardKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/HardShrinkBackwardKernelNpu.cpp)（implementation）：1–48；完整本地小文件。
- [HardShrinkBackwardKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/HardShrinkBackwardKernelNpu.cpp)（implementation）：1–48；与主线字节相同。

- [SoftShrinkKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SoftShrinkKernelNpu.cpp)（implementation）：1–55；完整本地小文件。
- [SoftShrinkKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SoftShrinkKernelNpu.cpp)（implementation）：1–70；仅排版差异。

- [SoftShrinkBackwardKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SoftShrinkBackwardKernelNpu.cpp)（implementation）：1–61；完整本地小文件。
- [SoftShrinkBackwardKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SoftShrinkBackwardKernelNpu.cpp)（implementation）：1–73；仅排版差异。

- [HardsigmoidKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/HardsigmoidKernelNpu.cpp)（implementation）：1–65；完整本地小文件。
- [HardsigmoidKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/HardsigmoidKernelNpu.cpp)（implementation）：1–65；与主线字节相同。

- [HardsigmoidBackwardKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/HardsigmoidBackwardKernelNpu.cpp)（implementation）：1–37；完整本地小文件。
- [HardsigmoidBackwardKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/HardsigmoidBackwardKernelNpu.cpp)（implementation）：1–37；与主线字节相同。

- [HardSwishKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/HardSwishKernelNpu.cpp)（implementation）：1–63；完整本地小文件，不匹配分支实参顺序按正文记录。
- [HardSwishKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/HardSwishKernelNpu.cpp)（implementation）：1–63；与主线字节相同。

- [HardSwishBackwardKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/HardSwishBackwardKernelNpu.cpp)（implementation）：1–54；完整本地小文件，V2R8+ 含 index_put_ 组合。
- [HardSwishBackwardKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/HardSwishBackwardKernelNpu.cpp)（implementation）：1–54；与主线字节相同。

- [HardtanhKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/HardtanhKernelNpu.cpp)（implementation）：1–70；完整本地小文件，ClipByValue 命令。
- [HardtanhKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/HardtanhKernelNpu.cpp)（implementation）：1–70；与主线字节相同。

- [HardtanhBackwardKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/HardtanhBackwardKernelNpu.cpp)（implementation）：1–77；完整本地小文件。
- [HardtanhBackwardKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/HardtanhBackwardKernelNpu.cpp)（implementation）：1–77；与主线字节相同。

- [MishKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MishKernelNpu.cpp)（implementation）：1–36；完整本地小文件（npu_mish/npu_mish_backward）。
- [MishKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MishKernelNpu.cpp)（implementation）：1–45；仅排版差异。

- [MishV2KernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MishV2KernelNpu.cpp)（implementation）：1–55；完整本地小文件（ATen 侧 mish 三变体）。
- [MishV2KernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MishV2KernelNpu.cpp)（implementation）：1–58；仅排版差异。

- [MishBackwardV2KernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MishBackwardV2KernelNpu.cpp)（implementation）：1–29；完整本地小文件。
- [MishBackwardV2KernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MishBackwardV2KernelNpu.cpp)（implementation）：1–34；仅排版差异。

- [SoftplusKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SoftplusKernelNpu.cpp)（implementation）：1–50；完整本地小文件。
- [SoftplusKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SoftplusKernelNpu.cpp)（implementation）：1–72；仅排版差异。

- [SoftplusBackwardKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SoftplusBackwardKernelNpu.cpp)（implementation）：1–40；完整本地小文件。
- [SoftplusBackwardKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SoftplusBackwardKernelNpu.cpp)（implementation）：1–44；仅排版差异。

- [LogSigmoidKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogSigmoidKernelNpu.cpp)（implementation）：1–67；完整本地小文件。
- [LogSigmoidKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LogSigmoidKernelNpu.cpp)（implementation）：1–70；仅排版差异。

- [LogSigmoidBackwardKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogSigmoidBackwardKernelNpu.cpp)（implementation）：1–58；完整本地小文件。
- [LogSigmoidBackwardKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LogSigmoidBackwardKernelNpu.cpp)（implementation）：1–68；仅排版差异（大括号位置），token 流相同。

- [HardSwishBackwardKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/HardSwishBackwardKernelNpuOpApi.cpp)（implementation）：1–56；完整本地小文件，V2R8+ 含 aclnnHardswishBackwardV2 静态探测。
- [HardSwishBackwardKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/HardSwishBackwardKernelNpuOpApi.cpp)（implementation）：1–51；完整本地小文件，**无 V2 探测**（主线与发布两版本 真实差异）。

- [MishKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MishKernelNpuOpApi.cpp)（implementation）：1–45；完整本地小文件。
- [MishKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MishKernelNpuOpApi.cpp)（implementation）：1–48；仅排版差异。

- [LogSigmoidNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LogSigmoidNpuOpApi.cpp)（implementation）：1–51；完整本地小文件。
- [LogSigmoidNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LogSigmoidNpuOpApi.cpp)（implementation）：1–54；仅排版差异。

- [SoftplusBackwardKernelNpu.cpp（custom_functions） d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/SoftplusBackwardKernelNpu.cpp)（implementation）：1–36；完整本地小文件（SoftplusV2Grad helper）。
- [SoftplusBackwardKernelNpu.cpp（custom_functions） dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/SoftplusBackwardKernelNpu.cpp)（implementation）：1–37；仅排版差异。

- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：2568–2692、3144–3174、3570–3590、4845–4901；仅本节 34 名 Schema 条目（该文件已列于 frontmatter 来源）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：2482–2606、3045–3075、3471–3491、4691–4747；同 34 名条目（该文件已列于 frontmatter 来源）。

## 原地变体与 PReLU：申请依据、RNG 来源与回退形态

本节核对激活主题级 67 名的最后一组 17 名：_prelu_kernel/_prelu_kernel_backward、rrelu_with_noise_、relu/relu_、sigmoid(.out/_)、tanh(.out/_)、silu_、threshold_、logit_、erf_/erfc_/erfinv_。其中 threshold_（EXEC aclnnInplaceThreshold）、logit_（委托 at::native::logit_）、silu_（structured_inherit 复用 silu.out 规格）已由前文 Threshold/Logit/SiLU 小节在实现层核对，本节不重复，只补 yaml 与回退侧；其余 14 名为新读。

| 入口 | gen_opapi / 手写 opapi | acl_op 回退（aclops） |
| --- | --- | --- |
| relu | gen out size/dtype/name=self，exec aclnnRelu（主线 dvm: all_version，发布无该标记） | `apply_tensor(self)`；"Relu" |
| relu_ | gen exec aclnnInplaceRelu（dvm 标记同上） | **原地内联格式分支：`relu_out_npu_nocheck(contiguous_self, contiguous_self)`**——格式化副本同时作输入与输出；与 sigmoid_/tanh_ 的「委托 out(self,self)」形态不同 |
| sigmoid | gen out dtype=`isIntegralType(self) ? at::kFloat : self`、name=self，exec aclnnSigmoid（主线 dvm，发布无） | `apply_tensor(self)`；"Sigmoid" |
| sigmoid.out | gen 只注 size=self、**dtype=out**（out 自身 dtype 自洽） | CheckOut({self},result,self)+格式分支 |
| sigmoid_ | gen exec aclnnInplaceSigmoid | 委托 `sigmoid_out(self,self)` |
| tanh | **手写 opapi（无 gen）**：integral self → 输出 dtype Float（apply_tensor_without_format），否则 self dtype；EXEC aclnnTanh+propagate_names（主线 dvm，发布无） | `apply_tensor(self)`；"Tanh" |
| tanh.out | 手写：**TORCH_CHECK 拒绝 integral result dtype**（"result dtype can't be cast to the desired output type."）+`check_tensor({self},result,result,self.sizes())`+`check_memory({self},{result})`；EXEC aclnnTanh | CheckOut({self},result,self)+格式分支 |
| tanh_ | 手写 DO_COMPATIBILITY(aclnnInplaceTanh)；EXEC aclnnInplaceTanh（dvm 标记同上） | 委托 `tanh_out(self,self)` |
| rrelu_with_noise_ | **手写 opapi（无 gen）**：DO_COMPATIBILITY(aclnnInplaceRReluWithNoise)；从 NPUGeneratorImpl（默认或传入）取 `philox_engine_inputs(1<<28)` 的 seed/offset 标量，EXEC aclnnInplaceRReluWithNoise(self,noise,lower,upper,training,seed,offset) | **逐元素 host 循环**：TORCH_CHECK noise 形状==self 后委托 `rrelu_with_noise_out(self,…,self)`（CheckOut({self,noise},self,self)+格式分支）；training 分支 `input_data[i].item().toFloat()` 逐元素读回、**CPUGeneratorImpl** uniform 采样、output/noise 逐元素写回；eval 分支委托 `leaky_relu_out(self,(lower+upper)/2)` |
| _prelu_kernel | gen out size/dtype=self，exec aclnnPrelu | `prelu_common_nocheck`：`apply_tensor(self)`+OpCommand "PRelu"(self,weight) |
| _prelu_kernel_backward | **手写 opapi（V2R1+ 守卫）**：DO_COMPATIBILITY(aclnnPreluBackward)；weight 先 reshape(-1)、grad_input=**apply_tensor_without_format(grad_output)**、grad_weight 按展平 weight；EXEC aclnnPreluBackward 后 grad_weight reshape 回 weight_shape | grad_input=**apply_tensor(self)**（申请依据不同）、grad_weight 同按展平 weight；"PReluGrad" 双输出后同样 reshape 回 |
| erf_ | gen exec aclnnInplaceErf（前向 erf 已在 special_functions 卡实现级核对） | 委托 `acl_op::erf_out(self,self)`，继承 CheckOut+格式分支 |
| erfc_ | gen exec aclnnInplaceErfc | 委托 `acl_op::erfc_out(self,self)` |
| erfinv_ | gen exec aclnnInplaceErfinv | 委托 `acl_op::erfinv_out(self,self)` |
| silu_ / threshold_ / logit_ | 见前文 SiLU/Threshold/Logit 小节（已核对） | — |

四条需要单独记录的边界：

1. **rrelu_with_noise_ 的两条路径没有共享随机性来源**：op_api 路把 NPU philox 引擎的 seed/offset 标量交给 aclnn 内核采样；acl_op 回退的 training 分支在 host 上用 **CPU 生成器**逐元素采样（每元素一次 `.item()` 设备读回）。两条路径对同一输入产出不同噪声序列，大张量回退还伴随逐元素同步成本；eval 分支回退取 (lower+upper)/2 平均斜率的 leaky。`rrelu_with_noise`（functional）与 `.out` 变体在同一手写文件中，不在本卡名单。
2. **integral dtype 的三种处理**：sigmoid functional（gen）与 tanh functional（手写）都把整型输入的输出提升为 Float；sigmoid.out（gen）用 out 自身 dtype 自洽接受；tanh.out（手写）显式 TORCH_CHECK 拒绝整型 out。不能把任一规则外推到第三个入口。
3. **_prelu_kernel_backward 的 grad_input 申请依据两路径不同**：手写 opapi 按 grad_output（apply_tensor_without_format），aclops 按 self（apply_tensor）。grad_output 与 self dtype 不同时两条路径产出不同的 grad_input dtype；aclnnPreluBackward 侧接受性未核对。
4. relu_ 的 aclops 原地格式分支对格式化副本「自入自出」后 format_fresh_view 回 self，与其他原地入口（委托 out(self,self)）不同；acl_op functional relu 无格式分支。

### 原地变体与 PReLU 补充证据

- [PreluKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/PreluKernelNpu.cpp)（implementation）：1–26；完整本地小文件。
- [PreluKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/PreluKernelNpu.cpp)（implementation）：1–26；仅排版差异。

- [PreluBackwardKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/PreluBackwardKernelNpu.cpp)（implementation）：1–38；完整本地小文件。
- [PreluBackwardKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/PreluBackwardKernelNpu.cpp)（implementation）：1–39；仅排版差异。

- [ReluKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ReluKernelNpu.cpp)（implementation）：1–52；完整本地小文件。
- [ReluKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ReluKernelNpu.cpp)（implementation）：1–58；仅排版差异。

- [SigmoidKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SigmoidKernelNpu.cpp)（implementation）：1–57；完整本地小文件。
- [SigmoidKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SigmoidKernelNpu.cpp)（implementation）：1–68；仅排版差异。

- [TanhKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/TanhKernelNpu.cpp)（implementation）：1–54；完整本地小文件。
- [TanhKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/TanhKernelNpu.cpp)（implementation）：1–64；仅排版差异。

- [RreluWithNoiseKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RreluWithNoiseKernelNpu.cpp)（implementation）：1–135；完整本地小文件（training host 循环）。
- [RreluWithNoiseKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/RreluWithNoiseKernelNpu.cpp)（implementation）：1–109；去空白 token 流与主线相同。

- [ErfKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ErfKernelNpu.cpp)（implementation）：34–59；erf_out/erf/erf_ 委托段。
- [ErfKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ErfKernelNpu.cpp)（implementation）：34–59；与主线字节相同。

- [ErfcKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ErfcKernelNpu.cpp)（implementation）：31–52；erfc_out/erfc/erfc_ 委托段。
- [ErfcKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ErfcKernelNpu.cpp)（implementation）：31–62；仅排版差异，erfc_ 委托同构（58–62）。

- [ErfinvKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ErfinvKernelNpu.cpp)（implementation）：35–62；erfinv_out/erfinv/erfinv_ 委托段。
- [ErfinvKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ErfinvKernelNpu.cpp)（implementation）：35–62；与主线字节相同。

- [TanhKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/TanhKernelNpuOpApi.cpp)（implementation）：1–53；完整本地小文件。
- [TanhKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/TanhKernelNpuOpApi.cpp)（implementation）：1–52；仅排版差异。

- [RReluWithNoiseKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RReluWithNoiseKernelNpuOpApi.cpp)（implementation）：1–84；完整本地小文件（philox seed/offset）。
- [RReluWithNoiseKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RReluWithNoiseKernelNpuOpApi.cpp)（implementation）：1–90；仅排版差异。

- [PreluBackwardKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/PreluBackwardKernelNpuOpApi.cpp)（implementation）：13–39；_prelu_kernel_backward 实现段。
- [PreluBackwardKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/PreluBackwardKernelNpuOpApi.cpp)（implementation）：13–40；仅排版差异。

- [PreluKernelNpu.cpp（custom_functions） d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/PreluKernelNpu.cpp)（implementation）：1–29；完整本地小文件（PRelu helper）。
- [PreluKernelNpu.cpp（custom_functions） dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/PreluKernelNpu.cpp)（implementation）：1–34；仅排版差异。

- [PreluBackwardKernelNpu.cpp（custom_functions） d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/PreluBackwardKernelNpu.cpp)（implementation）：1–31；完整本地小文件（PReluGrad helper）。
- [PreluBackwardKernelNpu.cpp（custom_functions） dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/PreluBackwardKernelNpu.cpp)（implementation）：1–38；仅排版差异。

- [inner_compute.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/inner_compute.h)（implementation）：40–110；prelu/softplus_backward 等声明段。
- [inner_compute.h dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/inner_compute.h)（implementation）：40–71；同声明段，仅排版差异。

- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：735–743、752–755、2101–2106、2126–2131、2151–2156、4208–4225、4432–4435、4576–4602、4668–4673、5073–5086、5111–5114、5549–5551；仅本节 17 名 Schema 条目（该文件已列于 frontmatter 来源）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：710–718、727–730、2036–2041、2061–2066、2086–2091、4095–4110、4313–4316、4426–4451、4515–4520、4913–4924、4948–4951、5380–5382；同 17 名条目，发布无 dvm 标记（该文件已列于 frontmatter 来源）。
