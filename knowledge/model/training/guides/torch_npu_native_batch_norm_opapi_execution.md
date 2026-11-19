---
type: Guide
title: 原生BatchNorm的OpAPI：统计输出、补写与掩码分配
description: 区分主线与发布的训练/推理统计输出、out引用和重叠保护，核对BatchNorm反向掩码及FP32仿射梯度申请。
tags:
- task.optimization
- topic.precision
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BatchNormKernelOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/BatchNormKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BatchNormBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/BatchNormBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
created_at: '2026-11-10T13:42:28Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 原生BatchNorm的OpAPI：统计输出、补写与掩码分配

## 固定范围与已有合同

本卡主要核对 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的 `native_batch_norm`、out、legit/no_stats 和反向 OpAPI，发布 `dedc316708372c9a8bfde4527abd2a94b74840f5` 用于对照所选 C++ 与 Schema。完整平台和软件配套未知，保持 draft、空平台，未新增 verified。

[公开Norm限制](torch_npu_native_normalization_constraints.md)已列产品与 dtype，[GE BatchNorm](../../inference/guides/optimization/torchair/torchair_ge_batch_norm_lowering.md)已描述构图、统计量和函数化拷贝。本卡补独立 Eager OpAPI 的真实申请与推理统计补写，不把 GE 空统计量合同或其它同步片段直接套用。没有导入、生成、编译或运行上游，也未进行设备、训练或性能实验。

## 原生前向返回哪些存储

主线 `native_batch_norm` 先按 input shape/options 经 `apply_tensor_without_format` 申请 out，再以通道轴 `input.size(1)` 申请两份统计：训练为 FP32，推理为 input dtype。两份统计是独立申请，不是直接把 running_mean/var 返回成别名；这里也没有因推理模式把它们统一设为空 Tensor。

它随即调用同文件 `native_batch_norm_out`。out 入口把提供的 out/save_mean/save_invstd 原对象作为输出交给 `aclnnBatchNorm`，最后返回三份引用；running_mean/var、weight/bias 则以原 Optional 参数下传，调用前没有在此做函数化 clone。`_native_batch_norm_legit` 的 Schema 对 running_mean/var 有可变别名标注，但运行统计如何更新仍由实际底层算子及模式决定，不能把标注或透传说成已测量的写回数值。

out 入口有三次 `check_tensor`，传入的目标 dtype/size分别取对应输出自身。不能把这些调用概括为本地已按通道数和训练 dtype完整重新推导、验证了输出规格。函数也未在这里验证所有 rank、仿射尺寸、eps 或 running 参数组合。

## 推理统计在ACLNN之后补写

调用 `aclnnBatchNorm` 后，仅当 training=False 且 running_mean、running_var 两者都有值且已定义时，包装才补写：save_mean来自 running_mean，save_invstd来自 `(running_var+eps)^(-1/2)`。缺其中一项时，这个后处理分支不运行，不能由包装已经分配统计就推定内容有效。

running_var 为 FP16/BF16 时，先转 FP32作为后处理 variance；其他 dtype 不在此统一提升。然后检查 variance shape 能广播到 save_invstd shape，再进入写入 helper。普通前向申请的推理统计仍为 input dtype，所以中间 FP32和最终存储精度是不同问题。

### mean的直接复制条件

`write_inference_mean` 要求源/目标 dtype、shape、device一致，双方内部格式都是 ND、contiguous 且 `NpuUtils::check_match`，并且 `get_overlap_status(save_mean,mean)==NO`。满足才直接调用 `copy_d2d_by_memcpy`，传入 save_mean.numel()；其余调用 `save_mean.copy_(mean)`。

这条路径仍然复制数据，不是把 save_mean变成 running_mean的别名，也不能把跳过一般 copy 分析等同于没有设备任务或已经取得性能收益。

### invstd减少临时量的条件

`write_inference_invstd` 先以函数局部 static bool缓存 `aclnnAdds` 与 `aclnnInplaceRsqrt` 的可用性。其分支如下：

| 条件 | 局部写入 |
| --- | --- |
| 目标与 variance dtype/shape相同、双方ND、目标check_match，且两个算子可用并判断无重叠 | 先 `aclnnAdds` 直接写 save_invstd，再 `aclnnInplaceRsqrt` 原地变换。 |
| 上述类型/shape/格式条件成立，但算子可用性或无重叠条件不成立 | `rsqrt_out(save_invstd, variance+eps)`，加法仍先形成表达式结果。 |
| 外层类型/shape/格式条件不成立 | `save_invstd.copy_(rsqrt(variance+eps))`。 |

代码没有在此分支要求与 mean helper完全相同的 device/双侧contiguous/check_match条件；不能把两个 helper的保护项合并成源码并不存在的统一矩阵。重叠判断的目的限定于这段补写避免过早覆盖 variance，发生在先前 ACLNN调用之后；它不证明任意用户out与running参数别名都被全流程提前拒绝或安全支持。

直接写入分支可减少这里的临时Tensor与一般分派路径，但仍有加法、rsqrt设备调用。源码注释的加速目标不是本卡性能结果，实际分配和收益须在固定输入及软件栈下测量。

## legit和反向掩码按实际消费者解释

主线带 running参数的 `_native_batch_norm_legit` 通过 `at::native_batch_norm` 委托，保留 ATen分派；新增 no_stats 形式显式要求 training=True，再用两个 nullopt委托。不要把 no_stats当成允许缺running统计的推理入口，也不能由这份局部函数认证整个 BatchNorm模块所有配置。

两版 OpAPI反向的非注释词法 token相同，均先检查 `aclnnBatchNormBackward` 兼容性，并按 mask准备：

- mask[0]为真：按 self.shape/options申请输入梯度。
- mask[1]/[2]为真：分别按 `{self.size(1)}`、self设备选项和 FP32申请 weight/bias梯度。
- 对应 mask为假：局部槽保持未定义，完整 mask与 running/saved Optional统计原样交给 ACLNN。

即使全false，包装仍走执行宏，没有本地全mask短路；不能据未申请输出推定 kernel成本或工作区必为零。也没有在返回前统一把 FP32仿射梯度cast回权重dtype，本卡不推断外层 autograd叶子grad最终类型。

前后向兼容宏分别检查普通BatchNorm/Backward和其GetWorkspaceSize符号；缺符号时仅在非ACLNN-only路线返回ACL表达式，其他情况报错。符号检查不认证算子能力。ACL回退的布局变换、统计解释和mask效果不是本卡已核对范围，不能把此处 OpAPI分配结论外推；宏机制另见[原生LayerNorm](torch_npu_native_layer_norm_execution.md)。

## 发布声明与主线补写要分开

发布的所选 BatchNormKernelOpApi.cpp只有带running参数的legit委托；native_batch_norm及out由该固定Schema中的 gen_opapi描述：训练统计为通道长度FP32，推理统计为shape `{0}`、input dtype，exec指向aclnnBatchNorm。out生成描述也只列该exec。这里审的是声明，没有执行生成器、查看安装包生成物或证明设备行为。

主线同一Schema移除了这两处gen_opapi描述，改为前述显式C++：普通前向统计总按通道长度申请，并在推理且running参数齐全时补写。主线新增no_stats声明/实现不在所选发布段和该C++文件中，不能由此声称发布所有后端都没有等价能力。

排查版本迁移时，分别记录准确入口、train、running参数是否齐全、统计shape/dtype、是否用户提供out、重叠和格式条件，再比对数值、别名、running状态及反向mask。复用存储必须同时验证整条调用链，不能只照抄补写helper条件。本文没有执行这些实验。

- [BatchNorm归约：通道和/平方和，不负责running更新](../apis/torch_npu/batch_norm_reduce.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BatchNormKernelOpApi.cpp)（primary）：35–134。
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/BatchNormKernelOpApi.cpp)（implementation）：17–32。
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BatchNormBackwardKernelNpuOpApi.cpp)（implementation）：20–79。
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/BatchNormBackwardKernelNpuOpApi.cpp)（implementation）：20–50。
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：679–686,3734–3746。
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：655–657,3618–3641。
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）：94–119。
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）：96–112。