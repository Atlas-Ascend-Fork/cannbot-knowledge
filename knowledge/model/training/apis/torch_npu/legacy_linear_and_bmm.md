---
type: API
title: 旧线性与BMMV2：矩阵形状、格式和输出尺寸
description: 记录二维Linear约束、BMMV2的INT8拒绝及替换时的广播/形状边界。并含npu_bmmV2 aclops 实现层（pure_bmm_v2/reshape helper/反向接线）。
tags:
- task.lookup
- topic.precision
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_bmmV2.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_bmmV2.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_bmmV2.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_linear.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_linear.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_linear.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LinearKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LinearKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LinearKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LinearKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/BmmV2KernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/BmmV2KernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
created_at: '2026-11-09T20:27:55Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
---

# 旧线性与BMMV2：矩阵形状、格式和输出尺寸

## 固定版本及消费边界

文档固定为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文与主线d84e9b1d6a558e5f27973cd4329f62968e46fdda实际收录的中英文页。发布对应ascend_26_0_pt28；TorchNPU实现发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b、独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf分别消费，不将两个main当配套发行。

默认平台A2/A3仅指各页所列范围；主线新增产品或参数另明确版本，旧Atlas不自动映射新型号。beta及计划废弃是上游接口状态，知识卡stable不表示推荐新模型使用或运行verified。本卡未做上游导入、模型加载、设备执行、反向或性能实验；注册all_version不是全硬件保证，底层Kernel实现不在本卡结论范围。


## npu_linear

文档输入x为(m,k)、weight为(n,k)，可选bias为(n)，输出(m,n)，计算x@weight.T+bias。input/weight列FP16、FP32、INT32、INT8及ND/NHWC/NZ；bias列FP16、FP32、INT32及ND/NHWC，不能加入INT8 bias。主线明确ND输出及仅eager，不把同名原生Linear的任意高维输入、BF16、图模式自动带入。主线950另外明确不支持INT8/INT32，不能用通用dtype列覆盖产品限制。

两固定ACL Op实现按进程首次读取的环境/SoC条件缓存MM/BMM格式选择，可能临时ND→NZ或按格式29输出，反向也有格式处理；OpAPI则调用aclnnMM/Addmm并消费cube math设置。文档逻辑ND与内部私有存储/执行分支分开，不承诺每次调用都重新读环境、无转换成本或必然提速。

## npu_bmmV2

旧页计划废弃，建议bmm、view、expand组合；列FP16/FP32/INT32与ND/NHWC/NZ、FakeTensor。output_sizes服务特定反向输出形状，不能当任意reshape开关。文档介绍二维以上矩阵而动机涉及1D广播，公开包装本身明确拒绝INT8；这不证明其余任意rank/广播组合均可用。

本卡未审完整BMMV2内部广播和反向helper。迁移保持批维、扩展、逻辑shape与梯度归约维，不以FakeTensor推导成功充当设备数值验证。

## npu_bmmV2 实现层与反向 helper

上文 npu_bmmV2 节声明"未审完整内部广播和反向helper"；本节以两固定 pin 的 `BmmV2KernelNpu.cpp`（355 行，主线与发布两版本 去空白等价）补齐该欠账。注册面：custom 段 `exposed: all_version` + `acl_op: all_version`、无 `op_api`——旧 ACE 路径独占；反向两名 `npu_bmm_v2_mat1_backward`/`npu_bmm_v2_mat2_backward`（acl_op [v2.1,newest] + symint 段）由 `derivatives.yaml` 85–86 行接到 npu_bmmV2 的 self/mat2 梯度。

`npu_bmmV2_impl(self, mat2, output_sizes)` 三分支：`output_sizes` 为空且两输入同 dim 时直发 `pure_bmm_v2`；为空但 dim 不同时先 `expand_tensor`（源注释：避免 transdata 精度误差）再计算并 view，1D 输入按 `[k][b,k,n]→[b,n]`、`[b,m,k][k]→[b,m]` 折叠输出维；非空时求 expect 与 infer 尺寸差集 `axis_reduce`——无差集按上条处理，有差集（需要沿某些维求和）时 `reshape` + `reshape_tensor_self`/`reshape_tensor_mat2` 把 batch 维折进 M/K（源注释例：`[5,6,7,17]→[6,7,85]`、`[5,6,17,65]→[6,85,65]`），单次 BatchMatMul 后 view 回 expect，源注释明示该路径为 "reduce sum without accuracy error"。

`pure_bmm_v2`：1D self/mat2 先 view 成 `[1,k]`/`[k,1]`；输出 Half 按 `ACL_FORMAT_FRACTAL_NZ` 分配、其余 ND；`is_transpose_last_two_dims_v2` 命中的输入跳过 `format_contiguous` 并以 `adj_x1`/`adj_x2` 属性传转置标志，命令为 ACE `BatchMatMul`（两输入 `InputWithoutContiguous`）。反向 helper 是 host 组合：恢复 1D 维（grad view 插 1）后 `mat1 梯度 = npu_bmmV2(grad, mat2 转置)`、`mat2 梯度 = npu_bmmV2(mat1 转置, grad)`，即复用前向内核承载转置乘。

- 设备侧 `BatchMatMul` 数值语义、`expand_tensor`/reshape 的 transdata 实际成本未测；本节为主线与发布两版本 静态阅读。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_bmmV2.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_bmmV2.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_bmmV2.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_linear.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_linear.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_linear.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LinearKernelNpu.cpp)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LinearKernelNpu.cpp)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LinearKernelNpuOpApi.cpp)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LinearKernelNpuOpApi.cpp)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/BmmV2KernelNpu.cpp)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/BmmV2KernelNpu.cpp)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [BmmV2KernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/BmmV2KernelNpu.cpp)（implementation）：全文 355 行；[发布版](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/BmmV2KernelNpu.cpp)与主线去空白等价（`tr -d` 比对）。
- [derivatives.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）：85–86；npu_bmmV2 的 self/mat2 梯度接线.
