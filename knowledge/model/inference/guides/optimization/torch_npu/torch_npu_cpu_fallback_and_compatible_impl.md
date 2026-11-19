---
type: Guide
title: TorchNPU 执行路径：CPU fallback 门控与兼容实现
description: 区分已纳管 CPU 回退的禁止开关和底层算子实现选择，避免用开关宣称获得缺失的 NPU 能力；补主线源码级回退分类与Sparse CSR显式入口。
tags:
- task.optimization
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/TORCH_NPU_FALLBACK_CPU_DISABLE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/TORCH_NPU_USE_COMPATIBLE_IMPL.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScaledDotProductAttentionKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/Quantization.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/Quantization.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/Quantization.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/Quantization.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/Quantization.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/Quantization.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/Quantization.md
  role: constraint
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
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GeluOutKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuNewParams.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/TORCH_NPU_FALLBACK_CPU_DISABLE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/TORCH_NPU_USE_COMPATIBLE_IMPL.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/reference.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/reference.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/troubleshooting_cases/unsupported_op_called.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-are_compatible_impl_enabled.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-are_compatible_impl_enabled.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-are_compatible_impl_enabled.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-use_compatible_impl.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-use_compatible_impl.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-use_compatible_impl.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/CpuFallbackUtils.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/ops/SparseCsrReductionFallbackKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/VariableFallbackKernel.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/VariableFallbackKernel.cpp
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/register/OptionsManager.cpp
  role: constraint
created_at: '2026-11-09T06:01:51Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# TorchNPU 执行路径：CPU fallback 门控与兼容实现

## 固定版本与证据

依据 PyTorch/TorchNPU 固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的环境变量文档，按所列产品和选项限制使用，不推导发布组合具备全部功能。只读来源审阅，未运行上游代码或设备实验。

## CPU fallback 门控

TORCH_NPU_FALLBACK_CPU_DISABLE 默认 0，允许已纳管路径把数据转 CPU 计算后转回；严格设为 1 后，在进入主要 CPU 数值计算前报错，错误包含算子名和变量名，且不打印“即将fallback到CPU”的告警。只支持 0/1，在进程启动前设置，首次读取后缓存，运行中修改 os.environ 不改变行为。

门控覆盖 Dispatcher 缺少 NPU kernel 的 fallback 及已接入门控的显式 CPU kernel；不覆盖所有 Host 计算、控制逻辑、staging、Host 权重预处理、用户显式 .cpu()/CPU Tensor，也不把 ACL Op/AclNN 兼容路径自动算成 CPU fallback。它不更改注册关系、不增加 NPU 实现；开启后报错是支持度诊断信号，关闭后运行成功也不证明性能理想。

## 底层实现一致性

TORCH_NPU_USE_COMPATIBLE_IMPL 默认 0，1 选择与社区对齐的底层实现，并影响 use_compatible_impl 的状态；需在 import torch 前设置，文档范围 TorchNPU≥26.0.0。环境页目前列明torch.nn.functional.gelu、torch.matmul、torch.nn.functional.max_pool1d/max_pool2d，不能外推到所有算子。

两种开关职责不同：实现一致性不意味着模型完全没有 CPU 活动，禁止 fallback 也不自动保证与 CPU/CUDA 数值逐位相同。通过日志与实际 kernel 确认路径，再比较输出。


## 核验

保存解释器、包版本、设备、完整配置及首次生效时机，在新进程中做单项对照。检查数值与实际路径，再分别比较首次启动、稳态时间和资源开销；调试配置关闭后复测。

## SDPA的兼容选择是独立补充

固定TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的PyTorch2.14 SDPA页另外列出use_compatible_impl(True)配合MATH后端选择的用法；这补充了环境变量页列举的算子范围，不能从该页短名单推断SDPA完全不受此选项影响。

OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` SDPA包装在对应重载首次调用时保存兼容标志；启用后按MATH开、FLASH关或尾维大于256强制数学组合实现。同dtype浮点mask、FP32尾维不满足4对齐也可导致数学路径。这里是NPU算子组合，不能与CPU fallback混为一谈，也不据此宣称所有原生后端选择标志都完整生效。

- [SDPA的参数、掩码与路径契约](../../../../training/apis/torch_npu/scaled_dot_product_attention.md)

## 伪量化和Observer的明确回退提示

固定主线的七份原生Quantization支持页（PyTorch2.7.1、2.9至2.14）分别对torch.ao.quantization.fake_quantize.FakeQuantize、FusedMovingAvgObsFakeQuantize及observer.RecordingObserver标注“可能回退至CPU执行”，这些条目列A2/A3训练系列及950DT。支持出现在清单中不等于全程NPU，也不等于每次必回退；其他Observer没有这句话也不能推断完全没有Host活动。

伪量化/观测阶段的调用成功、模型已.to("npu")，均不证明量化训练/校准完全由设备完成。排查这三类入口时对照实际CPU/NPU时间线、数据转移与已纳管fallback门控；门控报错只帮助定位已覆盖的CPU数值路径，不能把它写成可自动生成NPU实现。此处是QAT/Observer层约束，不把它等同于npu_quant_matmul或MX融合接口的量化执行契约。

这次只逐版本核对三个条目的完整产品与限制块，未声称整份数千行Quantization页已完整摄取或验证。

## 原生LayerNorm与图像重采样的补充

固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的七份torch.nn清单还列LayerNorm通过use_compatible_impl(True)从aclnnLayerNorm切至aclnnFastLayerNorm，目的是与社区同名接口的内存一致性对齐。环境变量页的gelu/matmul/max_pool短名单不能被当作穷举，也不能据“Fast”名称报告收益；它仍与CPU fallback门控是两个机制。

同一组页面明确nn.UpsamplingNearest2d可能CPU回退，input列FP16/FP32/UINT8，产品A2/A3训练系列和950DT。不能把这条提示合并成所有interpolate/upsample均必回退，也不能据模型在NPU便排除该Host路径。应核对实际算子/数据转移与门控覆盖，再测完整预处理链路。

- [归一化类/函数及反向条件](../../../../training/guides/torch_npu_native_normalization_constraints.md)
- [重采样与像素重排](../../../../training/guides/torch_npu_native_vision_resampling.md)

## 池化、Padding与损失的逐接口回退提示

固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的七版本条目另明确F.fractional_max_pool2d、nn.ZeroPad2d、F.poisson_nll_loss、nn.HuberLoss、nn.MultiMarginLoss和nn.TripletMarginLoss可能CPU回退；不能将类和functional中一方的提示自动扩展到全部同名入口，或解释为每次必回退。

MaxPool的use_compatible_impl用于内存一致性，indices的INT32/产品差异以及损失的标签/梯度限制仍需独立核对。日志中无fallback报错不证明所有Host活动已消失，也不解除target越界可能静默错误的约束。

- [池化与索引](../../../../training/guides/torch_npu_native_pooling_and_indices.md)
- [Padding模式](../../../../training/guides/torch_npu_native_padding_constraints.md)
- [原生损失](../../../../training/guides/torch_npu_native_loss_constraints.md)

## 激活函数的补充与GELU首次读取

固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的七版本条目还标注nn.Hardshrink、nn.Hardsigmoid、nn.Tanhshrink及F.hardswish可能CPU回退，不能把这句话推广到所有同名functional/类或解释为必回退。

OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的gelu_out重载在首次调用以static保存CheckCompatibleImpl。非ACLNN-only且标志关闭时调用aclnnGelu，另一分支将none/tanh转换为0/1后调用aclnnGeluV2；运行中改标志不证明该重载会重新读取。这是底层实现选择，不是自动转CPU，也不把实现helper接受none等同于公开产品页已扩展近似模式。

- [激活函数与原地/产品差异](../../../../training/guides/torch_npu_native_activation_precision.md)

## DO_COMPATIBILITY的符号检查不等于CPU门控

独立OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中，DO_COMPATIBILITY静态查询aclnn执行及GetWorkspaceSize两个符号；缺任一时，AclnnOnly设备直接报不支持，否则告警并return调用者传入的originCallExpression。后者可能是aclop或框架组合，不统一意味着CPU；符号存在后的dtype/参数/运行错误也不是该宏的自动回退条件。

DO_COMPATIBILITY_COMMON宏没有相同的AclnnOnly拒绝分支，不能忽略宏名差异。TorchNPU适配参考页以“如CPU”举例不能扩大宏本身的行为；与TORCH_NPU_FALLBACK_CPU_DISABLE覆盖的已纳管CPU数值路径分别判断。这是宏局部的源码合同，没有执行动态库查询、完整符号解析链或设备测试。

## 告警后的历史失败不能只按可忽略处理

同提交中文旧案例在aten::linalg_lstsq.out的CPU fallback告警后继续出现_copy_from_and_resize尺寸错误及ERR01007。页面允许仅有告警且不要求性能改进时保留路径，不表示存在后续异常也可忽略；需要结合实际输入、回写和接口支持选择替代方案。

这是历史路径，不把它变成当前全部版本lstsq均不可用的结论，也不把无告警当作全程NPU。严格fallback门控、ACLNN兼容替代及真实CPU活动仍按各自机制核对。

## Python兼容开关的发布与主线名单

[use_compatible_impl及状态查询](../../../apis/torch_npu/compatible_impl.md)的发布页另列GELU、LayerNorm、all_to_all、scatter、gather及两种MaxPool2d，主线加SDPA。名单与环境页各有范围，查询True不能证实某个static重载已经重新读取，更不是全模型数值逐位相同或没有Host活动的证明。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/TORCH_NPU_FALLBACK_CPU_DISABLE.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/TORCH_NPU_USE_COMPATIBLE_IMPL.md)（constraint）

- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn-functional.md)（constraint）

- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScaledDotProductAttentionKernelNpuOpApi.cpp)（implementation）

- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/Quantization.md)（constraint）

- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/Quantization.md)（constraint）

- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/Quantization.md)（constraint）

- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/Quantization.md)（constraint）

- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/Quantization.md)（constraint）

- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/Quantization.md)（constraint）

- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/Quantization.md)（constraint）

- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn.md)（constraint）

- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn.md)（constraint）

- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn.md)（constraint）

- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn.md)（constraint）

- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn.md)（constraint）

- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn.md)（constraint）

- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn.md)（primary）

- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn-functional.md)（constraint）

- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn-functional.md)（constraint）

- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn-functional.md)（constraint）

- [固定来源 22](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn-functional.md)（constraint）

- [固定来源 23](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn-functional.md)（constraint）

- [固定来源 24](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn-functional.md)（constraint）

- [固定来源 25](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GeluOutKernelNpuOpApi.cpp)（implementation）

- [固定来源 26](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuNewParams.cpp)（implementation）

- [固定来源 27](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/TORCH_NPU_FALLBACK_CPU_DISABLE.md)（constraint）

- [固定来源 28](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/TORCH_NPU_USE_COMPATIBLE_IMPL.md)（constraint）

- [固定来源 29](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）

- [固定来源 30](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/reference.md)（primary）

- [固定来源 31](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/reference.md)（constraint）

- [固定来源 32](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/troubleshooting_cases/unsupported_op_called.md)（primary）

- [固定来源 33](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-are_compatible_impl_enabled.md)（constraint）

- [固定来源 34](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-are_compatible_impl_enabled.md)（primary）

- [固定来源 35](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-are_compatible_impl_enabled.md)（constraint）

- [固定来源 36](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-use_compatible_impl.md)（constraint）

- [固定来源 37](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-use_compatible_impl.md)（primary）

- [固定来源 38](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-use_compatible_impl.md)（constraint）

- [固定来源 39](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/__init__.py)（implementation）

- [固定来源 40](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/__init__.py)（implementation）

## 源码级回退分类与 Sparse CSR 显式入口

主线固定提交内，源码级把已纳管回退分为两类，统一经 `CheckCpuFallbackAllowed`（`csrc/framework/utils/CpuFallbackUtils.h:16-33`）把关：`CpuFallbackKind::Dispatcher`（分发器后端回退）与 `CpuFallbackKind::ExplicitKernel`（显式 CPU kernel）。`TORCH_NPU_FALLBACK_CPU_DISABLE=1` 时在进入 CPU 数值计算前 `TORCH_CHECK` 报错，错误文本含算子名、回退类别描述与原因短语；否则直接放行。该头文件与 `OptionsManager::IsCpuFallbackEnable`（`OptionsManager.cpp:98-104`，static 一次读 env 缓存）都是主线独有文件/函数——发布 pin 无 `CpuFallbackUtils.h`，`OptionsManager.cpp` 内 rg `CpuFallback|FALLBACK` 零命中（negative evidence）。

| 类别 | 固定注册点（主线） | 动作顺序 | 失败/版本边界 |
| --- | --- | --- | --- |
| Dispatcher | `VariableFallbackKernel.cpp:240-242` 给 `TORCH_LIBRARY_IMPL(_, PrivateUse1)` 注册 `npu_cpu_fallback`（:224-238） | 先 `CheckCpuFallbackAllowed(op_name, Dispatcher, "no kernel is registered for the NPU PrivateUse1 backend")`（:226-227），再对首个遇到的算子名 `TORCH_NPU_WARN`（CAUTION 告警按算子名去重，:216-222），最后 `at::native::cpu_fallback` | 发布 pin 同名函数（release `VariableFallbackKernel.cpp:247-256`）**没有**门控调用：直接告警后进 `cpu_fallback`——主线才在分发器回退前置报错检查；`SparsePrivateUse1` 的 fallback（主线 :244-253）是硬报错不回 CPU，两版本相同 |
| ExplicitKernel | `SparseCsrReductionFallbackKernelNpu.cpp:54-56` 给 `TORCH_LIBRARY_IMPL(aten, SparseCsrPrivateUse1)` 注册 `_sparse_csr_sum.dim_dtype` 与 `_sparse_csr_prod.dim_dtype` | 各自先 `CheckCpuFallbackAllowed("aten::_sparse_csr_{sum,prod}.dim_dtype", ExplicitKernel, "torch_npu currently provides only a CPU implementation...")`（:17-21/:38-42），放行后 `TORCH_NPU_WARN_ONCE` 提示将回退（:22-26/:43-47），再 `OptionalDeviceGuard` + `self.cpu()`（:28/:49）+ CPU 端 `at::_sparse_csr_sum/prod` + `to(self.device())` | 发布 pin 无此文件且 csrc 内无 sparse_csr 注册（negative evidence）：发布版这两个 Sparse CSR 规约算子未由本仓显式接管；主线实现是整算子 CPU 执行（含 `.cpu()` 数据转移），不是 ACL 兼容实现 |

主线 csrc 全树 rg `CheckCpuFallbackAllowed` 仅上述三处使用点（两处 ExplicitKernel + 一处 Dispatcher），不能把这两类外推为穷举的回退清单：未过该工具的 Host 计算、控制流与用户显式 `.cpu()` 仍按本卡上文各自判断。门控报错发生在 `.cpu()` 转移之前，因此严格模式不会先搬数据再失败；这一顺序是源码直读，未做运行验证。

## 源码级来源

- [固定来源 41](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/CpuFallbackUtils.h)（primary，全文 1–36）

- [固定来源 42](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/ops/SparseCsrReductionFallbackKernelNpu.cpp)（primary，全文 1–59）

- [固定来源 43](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/VariableFallbackKernel.cpp)（primary，215–253）

- [固定来源 44](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.cpp)（implementation，98–104）

- [固定来源 45](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/VariableFallbackKernel.cpp)（constraint，247–256、270–272）

- [固定来源 46](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/register/OptionsManager.cpp)（constraint，rg `CpuFallback|FALLBACK` 零命中 negative evidence）
