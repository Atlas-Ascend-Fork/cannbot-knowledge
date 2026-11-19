---
type: Guide
title: OpPlugin aclops 旧ACL公共内核层：十个回退算子的命令与准备行为
description: 聚合utils/custom_functions/aclops中未被opapi卡片展开的十个旧ACL公共内核（zeros/embedding/where/sum/mean/var/index/gelu_backward/svd/repeat_interleave）的ACE命令、dtype/format准备与入口捷径，主线与发布两版本排版一致。
tags:
- task.implementation
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/ZerosKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/EmbeddingKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/WhereKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/SumKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/MeanKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/VarKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/IndexKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/GeluBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/LinalgSvdKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/RepeatInterLeaveKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/ZerosKernelNpu.cpp
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/EmbeddingKernelNpu.cpp
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/WhereKernelNpu.cpp
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/SumKernelNpu.cpp
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/MeanKernelNpu.cpp
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/VarKernelNpu.cpp
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/IndexKernelNpu.cpp
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/GeluBackwardKernelNpu.cpp
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/LinalgSvdKernelNpu.cpp
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/RepeatInterLeaveKernelNpu.cpp
  role: constraint
created_at: '2026-11-13T04:24:01Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# OpPlugin aclops 旧ACL公共内核层：十个回退算子的命令与准备行为

## 固定版本与范围

本卡聚合 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda`、发布 `dedc316708372c9a8bfde4527abd2a94b74840f5` 的 `op_plugin/utils/custom_functions/aclops/` 下十个 `*_common_nocheck` 公共内核。它们是各 `ops/aclops/*.cpp` 包装在 DO_COMPATIBILITY 缺 aclnn 符号（非 ACLNN-only 模式）时落入的旧 ACL 实现；各 opapi 主路线见既有家族卡（[归约准备](torch_npu_reduction_scan_dtype_empty_and_alias_preparation.md)、[where/动态选择](torch_npu_dynamic_selection_sync_and_where_scalar_execution.md)、[SVD/三角求解](torch_npu_native_linalg_constraints.md)、[repeat_interleave](torch_npu_repeat_interleave_length_and_backward_preparation.md)、[embedding](torch_npu_native_embedding_linear_constraints.md)），那些卡已声明「完整旧ACL实现不在本卡范围」，本卡即补这层。十个文件主线与发布两版本 去空白 token 流一致（仅排版差异），下文行号为主线。未执行任何 ACE 命令、运行库或设备；这些是静态可读的请求构造，不证明运行成功或数值正确。

## 逐内核的命令与准备

| 内核 | ACE 命令与属性 | 静态可读准备行为 |
| --- | --- | --- |
| zeros_common_nocheck | 无独立命令：`apply_tensor_with_format(size, option, ACL_FORMAT_ND)` 后 `result.zero_()` | 创建固定 ND 格式张量再原地清零；dtype/layout/device/pin_memory 全走 TensorOptions 组合 |
| embedding_common_nocheck | `GatherV2(weight, indices, dim_vec={0})`，attr `batch_dims=0` | TORCH_CHECK 要求 weight 非空；输出 shape 为 indices.shape 追加 weight 末维（与 [embedding 卡](torch_npu_native_embedding_linear_constraints.md)的 aclnnEmbedding 主路线合同同构，本层是回退落点） |
| where_out_nocheck | `Select(condition, self_cp, other_cp)` | dtype 不一致时按 `at::native::result_type(self, other)` 对两个输入各做 `_npu_dtype_cast`；condition 只接受 Byte/Bool，其余 dtype 在本地 TORCH_CHECK 拒绝 |
| sum_out_npu_nocheck | `ReduceSum(self, dim_list)`，attr `keep_dims` | dim 为空时用 `get_dimlist_for_tensor(self)` 展开全部轴；`check_dtype` 把整型 out_type 提升为 Float 再按需 dtype_cast 输入 |
| mean_out_no_dtype_nocheck | `ReduceMean(self, dim_vec)`，attr `keep_dims` | numel==0 且 dim 空时结果 `_npu_dtype_cast(Float).fill_(NAN)`（源码注释：NPU 的 NaN 只能 FP32）；out 的 rank<2 时 NCHW 作为 CheckOut 参照格式（标量与一维不支持 NZ），不匹配时 format_contiguous+format_fresh_view 往返 |
| var_after_out_nocheck | `ReduceStdV2Update(self, mean_broadcast)`，attr `dim` 原样、`if_std=false`、`unbiased`、`keepdim`、`correction` | dim 先 `maybe_wrap_dim` 再排序去重次序；`var_get_shape_prod` 逐步累乘并两处 TORCH_CHECK 防止 int64 溢出；先走 mean 的前段（mean_broadcast 为已广播均值） |
| index_out_nocheck | `Index(x, masks, indexed_sizes, indexed_strides, indices0..n)`；非 aicore 分支另设 attr `_exclude_engines="AiCore"` | masks/indexed_sizes/indexed_strides 以 `MEMORY_HOST_COMPILE_DEPENDENT` Long 输入（host 编译依赖）；`check_index_aicore` 要求各索引同 shape 且 masks 单调不减才允许 aicore，否则显式排除 AiCore 引擎 |
| gelu_backward_common_nocheck | `GeluGrad(grad, self, grad)` | 输出 `apply_tensor(self)`；第三个输入再次传 grad（源码把 grad 同时当 self 与 dout 两用），approximate 信息不在命令里 |
| linalg_svd（批内准备） | SVD 相关命令由 wrapper 层组装 | `cloneBatchedColumnMajor` 把 (B,M,N) 逐批克隆为列主序、按批对齐存储；`single/batch_check_errors` 把 info<0 映射非法参数、info>0 映射不收敛（svd 走 SBDSDC 未收敛文案、symeig 走未收敛文案、`allow_singular=false` 时 U(i,i)==0 报奇异） |
| repeat_interleave_common_nocheck | `RepeatInterleave(self, repeat|repeats)`，attr `axis=real_dim` | dim 缺省时先 flatten、real_dim=0；scalar 分支 `repeats>=1` 且 **`repeats==1` 直接返回 self**（不构造输出）；tensor 分支把 0 维 repeats `unsqueeze_(0)` |

## 与主路线的分工边界

- 回退触发由各 `ops/aclops/*.cpp` 包装层的 DO_COMPATIBILITY 决定（[兼容宏指南](../../inference/guides/optimization/torch_npu/torch_npu_opplugin_adaptation.md)已核对其静态符号+模式门语义）；本卡不重复该合同，也不把任何一列提升为该算子的完整执行事实——wrapper 层在进入这些 nocheck 前还各自有输出 shape 推导与 CheckOut，未在本卡逐文件展开。
- dtype/format 准备（where 的 result_type 输入提升、mean 的 NCHW 参照、sum 的整型→Float）只存在于旧 ACL 路线；aclnn 主路线的输出 dtype 合同见各家族卡，两者不能互换引用。
- `Index` 的 `_exclude_engines="AiCore"` 是 op-plugin 侧可静态读到的引擎排除请求；实际引擎调度归 GE/ACE，本卡不推断被排除后的执行设备。
- `GeluGrad` 的 (grad, self, grad) 输入三连来自源码按原文记录，其数值含义（是否假设 grad==dout）需要结合内核语义另行核对，不能由输入复用推论精度等价。
- gelu/approximate 的主线主路线（aclnnGelu/aclnnGeluBackward）见 [npu_gelu 卡](../../inference/apis/torch_npu/npu_gelu.md)；本层只在符号缺失回退时可达。

## 验证与关联

调试回退行为时记录：触发原因（缺哪个 aclnn 符号/模式）、进入本表哪一行、输入 dtype/format 与被 cast 的中间张量、host 编译依赖输入（Index 的 masks/sizes/strides）是否随 shape 改变、以及重复调用是否稳定复现。命中本层的模型迁移建议优先切回 aclnn 主路线或原生算子；本卡不提供性能结论，未执行任何运行验证。

- [归约准备卡](torch_npu_reduction_scan_dtype_empty_and_alias_preparation.md)
- [where/动态选择卡](torch_npu_dynamic_selection_sync_and_where_scalar_execution.md)
- [SVD/线性代数卡](torch_npu_native_linalg_constraints.md)
- [repeat_interleave 卡](torch_npu_repeat_interleave_length_and_backward_preparation.md)

## Evidence

- [ZerosKernelNpu.cpp d84e9b1d](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/ZerosKernelNpu.cpp)（primary）：16-34 全文。
- [EmbeddingKernelNpu.cpp d84e9b1d](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/EmbeddingKernelNpu.cpp)（primary）：16-34 全文。
- [WhereKernelNpu.cpp d84e9b1d](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/WhereKernelNpu.cpp)（primary）：18-73 全文。
- [SumKernelNpu.cpp d84e9b1d](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/SumKernelNpu.cpp)（primary）：24-108 全文。
- [MeanKernelNpu.cpp d84e9b1d](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/MeanKernelNpu.cpp)（primary）：22-106 全文。
- [VarKernelNpu.cpp d84e9b1d](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/VarKernelNpu.cpp)（primary）：20-187 全文。
- [IndexKernelNpu.cpp d84e9b1d](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/IndexKernelNpu.cpp)（primary）：20-129 全文。
- [GeluBackwardKernelNpu.cpp d84e9b1d](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/GeluBackwardKernelNpu.cpp)（primary）：16-25 全文。
- [LinalgSvdKernelNpu.cpp d84e9b1d](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/LinalgSvdKernelNpu.cpp)（primary）：22-287 全文。
- [RepeatInterLeaveKernelNpu.cpp d84e9b1d](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/aclops/RepeatInterLeaveKernelNpu.cpp)（primary）：22-102 全文。
- [ZerosKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/ZerosKernelNpu.cpp)（constraint）：16-34，去空白 token 流与主线一致。
- [EmbeddingKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/EmbeddingKernelNpu.cpp)（constraint）：16-34，同上。
- [WhereKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/WhereKernelNpu.cpp)（constraint）：16-66，同上。
- [SumKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/SumKernelNpu.cpp)（constraint）：24-131，同上。
- [MeanKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/MeanKernelNpu.cpp)（constraint）：22-128，同上。
- [VarKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/VarKernelNpu.cpp)（constraint）：20-158，同上。
- [IndexKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/IndexKernelNpu.cpp)（constraint）：20-129，同上。
- [GeluBackwardKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/GeluBackwardKernelNpu.cpp)（constraint）：16-31，同上。
- [LinalgSvdKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/LinalgSvdKernelNpu.cpp)（constraint）：22-267，同上。
- [RepeatInterLeaveKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/aclops/RepeatInterLeaveKernelNpu.cpp)（constraint）：22-119，同上。
