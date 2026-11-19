---
type: Guide
title: TorchNPU QAT的观察器状态与FakeQuant掩码
description: 说明QAT双开关、可写观察器状态、移动平均、scale保护和Host FakeQuant掩码调用的版本边界。
tags:
- task.optimization
- topic.compute.quantization
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FakeQuantizeKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/opapi/FakeQuantizeKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FakeQuantizeKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/opapi/FakeQuantizeKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-11T07:31:03Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU QAT的观察器状态与FakeQuant掩码

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 与固定发布快照 `dedc316708372c9a8bfde4527abd2a94b74840f5`。两版FakeQuant入口CPP和公共观察器实现各自逐字节相同；主线两文件已完整静态阅读，发布按整文件原始字节同一复用。未导入、执行观察器、训练或设备实验，平台暂不标记已验证。

## Schema范围与实际入口

已审两版Schema仅为下面三个入口登记op_api v2.1、v2.2；入口CPP自身的VERSION_BETWEEN从V2R1到VERSION_NEWEST，不可只凭宏范围声称所有更新版本都已注册。

```text
fake_quantize_per_channel_affine_cachemask(self, scale, zero_point,
    axis, quant_min, quant_max) -> (output, mask)
_fake_quantize_per_tensor_affine_cachemask_tensor_qparams(self, scale,
    zero_point, fake_quant_enabled, quant_min, quant_max) -> (output, mask)
_fused_moving_avg_obs_fq_helper(self, observer_on, fake_quant_on,
    running_min, running_max, scale, zero_point, averaging_const,
    quant_min, quant_max, ch_axis, per_row_fake_quant=False,
    symmetric_quant=False) -> (output, mask)
```

Schema为running_min、running_max、scale、zero_point声明四个独立可写Tensor别名，观察器状态不是本卡输出元组中的独立副本。两个cachemask入口均按self形状分配同类output和BOOL mask，分别调用 `aclnnFakeQuantPerChannelAffineCachemask` 与 `aclnnFakeQuantPerTensorAffineCachemask`。后者把fake_quant_enabled经 `.item().toFloat()` 提取成Host浮点值再下传；入口没有自行实现量化、截断或反向掩码算法，不能据名称补成底层数值承诺。

所谓fused helper只是转发公共Host实现，包含标量提取、逐通道循环和Tensor更新，不能当作整条观察器与FakeQuant均由单个设备融合Kernel完成的证据。

## observer与fake_quant两个开关独立

公共helper先检查 `ch_axis < self.dim()`，读取observer_on.item().toInt()；这一前置检查没有同时显式保护非负axis，不要把它当作完整轴归一化。running_min只有一个元素时，会同时把running_min/running_max重新绑定为reshape(1)。

per_row模式下，非2维self先把ch_axis与第0轴交换，再flatten(1)供统计；若running_min为空，则按self.size(ch_axis)同时resize四个状态，min填+inf、max填-inf，scale/zero_point只resize。该初始化即使observer关闭也发生，不能假定关闭observer时完全不改状态。

| observer_on | fake_quant_on | 此Host实现的行为 |
| --- | --- | --- |
| 真 | 真 | 先更新min/max，再重算scale/zero_point并调用对应cachemask FakeQuant。 |
| 真 | 假 | 更新min/max；返回self.clone()与全True BOOL mask，不重算qparams。 |
| 假 | 真 | 不更新min/max，但仍从现有min/max重新计算qparams并FakeQuant；不是简单沿用旧scale/zero_point。 |
| 假 | 假 | 仍执行前置reshape及可能的per_row空状态resize；结果为self.clone()与全True BOOL mask。 |

因此首次调用前要准备有效观察器状态；per_row空状态被填成±inf不表示observer关闭、fake_quant开启时也有可用qparams。这里没有独立检查所有状态长度、设备或类型，失败与合法性还取决于被调Tensor操作。

## min/max移动平均与Host读取成本

per_row统计函数要求ch_axis==0，并对传入y执行aminmax(y,1)，逐项更新到 `min(x_min.numel(),running_min.numel())`；普通模式执行全张量aminmax并更新状态第0项。单项旧min/max若为任意符号的inf就直接取新统计，否则按 `old + averaging_const*(current-old)` 更新。该函数没有将averaging_const限制在[0,1]，也没有把running_min/running_max所有长度自动修复一致。

“仅axis0”是实际统计更新函数的检查；不能由外层先做了permute就声称其它ch_axis已被整体支持，特别是2维self不会执行那段permute。多个逐项 `.item().toFloat()`、Host循环、标量回写和临时Tensor分配存在成本，是否引发同步、图中断及多少耗时须按真实运行测量，不能用fused名称忽略。

## qparams的数值保护与不活跃选项

choose_quantization_params先要求min≤max；可选reduce_range会将qmin/qmax各除以2。preserve_sparsity且范围跨0时，先用对称整数边界 `-((qmax-qmin)/2+1)` 与 `(qmax-qmin)/2` 扩展min/max，再把范围包含0。它要求qmin<qmax，以double计算 `(max-min)/(qmax-qmin)`；若float(scale)==0或float倒数为inf，则置scale=0.1，随后要求scale>0。

内部还有force_scale_power_of_two的幂次调整分支。当前fused helper通过symmetric_quant传preserve_sparsity，但force_scale_power_of_two显式false、reduce_range使用缺省false；不要把这些未开启分支宣传为该入口已启用的量化配置。

小scale低于 `6.1e-5f` 会提升至此阈值，并相应扩展min/max：min==0时只改max，max==0时只改min，否则按阈值/旧scale同时放大两端。zero_point分别从两端估计，依据代码中的 `abs(qmin)-abs(min/scale)` 与 `abs(qmax)-abs(max/scale)` 比较选取；preserve_sparsity跨0时改为(qmin+qmax)/2，最后夹到qmin/qmax或用nearbyint舍入。不能把这套规则替换成始终对称零点或只按min端计算。

per_row路径循环running_min.numel()更新scale/zero_point，再以原始self、ch_axis调用per-channel cachemask；代码还取得running_min/max的float data_ptr，不能跳过其实际类型前提。普通路径以整个running_min/max `.item()` 选参数，更新第0项，并构造Long类型ones作为fake_quant_enabled调用per-tensor cachemask。状态的有效shape、数值与类型都需要由调用方与下层共同满足，空状态或NaN不在此被统一修复。

## 图转换与验收边界

既有 [GE未实现重载清单](../../inference/guides/optimization/torchair/torchair_ge_unimplemented_overloads.md) 已将两个固定TorchAir版本的 `_fused_moving_avg_obs_fq_helper.default/out` 列为显式未实现；这里复用该已审记录，不重新宣称整文件或其他后端都不支持。Eager Host实现存在不能用来证明TorchAir GE完整捕获、QAT反向或观察器跨步状态已经可用。

核对真实训练时，要分开观察状态更新、qparams变化、output及mask，并区分observer冻结与FakeQuant关闭。本卡没有参考测试执行、梯度或精度结果，也没有确认开关动态变更、非零ch_axis、退化范围及更高版本注册的运行支持。

## Evidence

- [FakeQuantizeKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FakeQuantizeKernelNpuOpApi.cpp)（primary）：1–76；完整本地文件。
- [FakeQuantizeKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/opapi/FakeQuantizeKernelNpuOpApi.cpp)（implementation）：1–234；完整本地文件。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：192–194、624–626、2253–2255；仅所列完整Schema条目。
- [FakeQuantizeKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FakeQuantizeKernelNpuOpApi.cpp)（implementation）：1–76；完整本地文件。
- [FakeQuantizeKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/opapi/FakeQuantizeKernelNpuOpApi.cpp)（implementation）：1–234；完整本地文件。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：192–194、609–611、2186–2188；仅所列完整Schema条目。
