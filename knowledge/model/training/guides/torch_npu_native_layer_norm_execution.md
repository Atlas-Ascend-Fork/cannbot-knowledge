---
type: Guide
title: 原生LayerNorm执行：统计精度、掩码分配与兼容分派
description: 核对原生LayerNorm的版本门控、空batch统计shape、反向FP32仿射梯度与ACL回退掩码差异，区分公开限制和实际包装。
tags:
- task.optimization
- topic.precision
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LayerNormKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LayerNormKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LayerNormBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LayerNormBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LayerNormKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LayerNormKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LayerNormBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LayerNormBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NpuVariables.cpp
  role: implementation
created_at: '2026-11-10T13:27:04Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 原生LayerNorm执行：统计精度、掩码分配与兼容分派

## 固定版本与优化入口

本卡核对 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 与发布快照 `dedc316708372c9a8bfde4527abd2a94b74840f5` 的 `native_layer_norm`、`native_layer_norm_backward` C++ 调用链；主线 `IsAclnnOnly` 定义另定向绑定 TorchNPU `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`。这是固定源码合同，完整平台与配套范围未知，保持 draft、空平台，不新增 verified。

[原生归一化支持页](torch_npu_native_normalization_constraints.md)已记录公开 dtype 和兼容实现提示，[GE Norm 转换](../../inference/guides/optimization/torchair/torchair_ge_layer_group_rms_norm_lowering.md)已记录 LayerNormV4/GradV3。本卡补 Eager 的统计输出、梯度申请和回退差异，不重复支持矩阵，也不把公开 FP16/BF16/FP32范围扩展为任意类型。未导入、编译或运行上游，未执行设备、数值或性能实验。

## 路由检查与兼容开关不是同一个条件

两版 Schema 对这两个原生入口均声明 ACL 与 OpAPI 路线；前向用 `DO_COMPATIBILITY(aclnnLayerNorm, ...)`，反向检查 `aclnnLayerNormBackward`。宏缓存函数及 GetWorkspaceSize 地址：缺符号且 `IsAclnnOnly` 为真时报错，其他情况才返回 ACL 表达式。它检查库符号存在，不认证该设备、shape、dtype 或底层实现实际可执行。

前向通过这一检查后，还会以函数内 `static layer_sc=CheckCompatibleImpl()` 保存首次取得的兼容配置，再选择普通或 Fast ACLNN：

| 固定版本 | 后续前向分派 |
| --- | --- |
| 主线 | `!layer_sc` 或 `IsAclnnOnly()` 为真用 `aclnnLayerNorm`；否则用 `aclnnFastLayerNorm`。 |
| 发布 | 只按 `!layer_sc` 选择普通，否则 Fast。 |

所查主线 helper 的 `IsAclnnOnly` 为 `GetSocVersion()>=Ascend950`。这解释代码门控，不提供产品支持表；也不能据开关文档宣称主线该区间必定切到 Fast。普通 `aclnnLayerNorm` 的兼容探测不等于另外认证了 Fast 符号和行为。静态局部配置不支持“每次调用都会重新读取开关”的描述；设定时机按实际进程和版本验证。

## OpAPI前向的统计shape和精度

包装要求 normalized_shape 至少一维，已定义 weight/bias 的 shape 与它完全相同，input 的对应尾轴也匹配。已定义仿射项经过 `resize_(normalized_shape)`；未定义时保持未定义 Tensor 传给 ACLNN，前向没有在此构造全 1/0 替代参数。输出按 input 经 `apply_tensor_without_format` 申请。

令归一化轴之前的尺寸乘积为 M。统计分配 dtype 为 input 是 Double 时 Double，否则 Float；这是包装申请类型，不证明整个 kernel 累加都同精度，也不认证 Double 设备能力。

一般 mean/rstd 形状保留输入前缀，归一化尾轴改为 1。发布在 `M<=0` 时改分配 `{M}` 一维统计；主线只有 `M<=0` 且 SoC 小于 Ascend950 才走此分支，主线较新区间仍用保留维度形状。包装分配后继续调用 ACLNN，没有因 M 为 0 直接返回并显式填统计值。

因此空 batch 的统计 shape 必须按固定版本和路线消费，不能只因元素数同为 0 就当作 rank 相同。本层没有统一先对 input 执行 `.contiguous()`，也不能由 `without_format` 的名称推定所有输入布局或 stride 都免去底层整理。

## OpAPI反向：掩码省的是哪些输出

反向对已定义 weight/bias 做 resize；缺失则按 input.options 构造 normalized_shape 大小的 ones/zeros。它们在检查输出掩码前就被准备，不能把全 false mask 解释为包装完全不分配、不调用算子。

mean 与 rstd 均 reshape 为“输入前缀加归一化轴 1”的形状后交给 `aclnnLayerNormBackward`。本地变量名 `variance_refined` 保存的是传入 rstd 的 reshape，不代表这里又计算了 variance。

| mask槽 | 包装申请 |
| --- | --- |
| 0 为真 | `empty_like(input)`，保留 input dtype，要求 legacy contiguous memory format。 |
| 1 为真 | `empty_like(weight_refined, Float)`，FP32 仿射梯度。 |
| 2 为真 | `empty_like(bias_refined, Float)`，FP32 仿射梯度。 |
| 对应槽为假 | 该局部 Tensor 保持未定义，同时把完整 mask 传给 ACLNN。 |

没有在返回前将 FP32 仿射梯度统一 cast 回原 weight/bias dtype，也没有在这个函数内按 M 为 0 改为 zeros 或省略 ACLNN 调用。这里仅记录原生返回包装；普通 autograd 如何消费/转换梯度还须追真实调用者，不能直接推断叶子 `.grad` 的最终类型或训练故障。

## ACL回退不能套用相同的掩码和精度假设

ACL 前向入口对 input、weight、bias 按 `is_contiguous()` 选择原对象或 `.contiguous()`；helper 可构造缺失仿射项，并用 OpCommand `LayerNorm`。统计申请使用 weight.options 和 ND，末尾 reshape 为 `{M}`，没有 OpAPI 的统一 FP32统计申请。helper 的 `M<0` 分支也不是 `M==0` 的提前返回；零尺寸路线仍需单独验证。

ACL 反向的公开 C++ 形参有 bias 和 output_mask，但函数体没有读取它们，helper 始终准备三份输出；不要把 OpAPI 的按 mask 返回未定义槽外推到这一路线。

`nums_before_axis<=0` 时，ACL helper 返回 input 的 empty_like，以及 gamma_temp 的两份 zeros_like；否则按 input/gamma_temp 申请三份结果后调用 `LayerNormGrad`。本层没有像 OpAPI 那样为两个仿射梯度显式指定 FP32。它对传入 rstd reshape 后直接作为该算子的对应输入，不应因内部变量名叫 variance 就自行更换传值或恢复公式。

这些是实际回退表达式中的分配、调用和局部未消费参数，不是对整个 autograd、AMP、空输入或某设备数值错误的运行复现。LayerNorm 与原生/融合 GroupNorm、RMSNorm 的掩码、格式和统计合同仍需分别使用。

## 版本差异和验收方式

逐一对照所选四对 C++ 文件，去注释/空白并拼接宏续行后：OpAPI反向、ACL前向及ACL反向 token 相同；OpAPI前向仅有前述 M/SoC 和 Fast 门控两处代码变化，另去掉一行注释。两个 Schema 条目相同，兼容宏关键块也独立核对；不把局部一致扩大成两版整个 runtime 或 kernel 相同。

评估内存或兼容开关时，先记录准确入口与是否回退、首次配置值、输入/仿射 dtype 和 stride、归一化轴、M及三个 mask，再检查输出/统计的 shape、dtype、未定义槽与空输入行为。通过相同梯度参考和真实 autograd 验证后，再度量 contiguous、默认仿射、FP32梯度及格式整理的实际分配与时间；本卡未执行这些实验。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LayerNormKernelNpuOpApi.cpp)（primary）：20–104。
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LayerNormKernelNpuOpApi.cpp)（implementation）：20–105。
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LayerNormBackwardKernelNpuOpApi.cpp)（implementation）：20–82。
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LayerNormBackwardKernelNpuOpApi.cpp)（implementation）：20–82。
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LayerNormKernelNpu.cpp)（implementation）：20–151。
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LayerNormKernelNpu.cpp)（implementation）：20–151。
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LayerNormBackwardKernelNpu.cpp)（implementation）：20–129。
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LayerNormBackwardKernelNpu.cpp)（implementation）：20–129。
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）：94–119。
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）：96–112。
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：3775–3782。
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：3670–3677。
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NpuVariables.cpp)（implementation）：109–111。
