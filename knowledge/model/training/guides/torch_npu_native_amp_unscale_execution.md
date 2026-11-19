---
type: Guide
title: 原生AMP反缩放：分批、溢出状态与更新入口
description: 核对原生AMP的250 Tensor分批、状态读取与原地写入，并区分TorchNPU GradScaler的实际scale更新消费者。
tags:
- task.optimization
- topic.precision
- topic.optimizer
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AmpForeachNonFiniteCheckAndUnscaleKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AmpForeachNonFiniteCheckAndUnscaleKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AmpForeachNonFiniteCheckAndUnscaleKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AmpForeachNonFiniteCheckAndUnscaleKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AmpUpdateScaleKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AmpUpdateScaleKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/amp/grad_scaler.py
  role: implementation
created_at: '2026-11-10T13:11:53Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# 原生AMP反缩放：分批、溢出状态与更新入口

## 固定版本与使用边界

核对 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 与发布快照 `dedc316708372c9a8bfde4527abd2a94b74840f5` 的原生 AMP 包装，并在 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 定向追 `_unscale_grads_`、`update` 和 `_npu_update_scale`。后者不证明发布栈调用链；完整产品及软件配套范围未知，保持 draft 和空平台。

本卡补充[GradScaler 状态机](torch_npu_grad_scaler_contract.md)未展开的原生调用粒度、Host 读取和状态写入。不据注册或局部类型检查推定设备支持；未导入、编译或执行上游，也未运行训练、设备或通信实验。

## 先区分入口与调用者

Schema 的 `aten._amp_foreach_non_finite_check_and_unscale_` 原地处理 Tensor 列表和 `found_inf`，没有 Tensor 返回，同时声明 ACL 与 OpAPI 路线。`aten._amp_update_scale_` 原地更新 scale、growth tracker，返回与 scale 同别名的 Tensor，仅声明 OpAPI。`all_version` 是生成/注册选择，不能当作任意 CANN、dtype 或产品能力保证。

所查 GradScaler 动态路径按设备和 dtype 收集普通梯度后调用前一入口；稀疏梯度用 `_values()`，允许的 FP16 稀疏路径先 coalesce。融合优化器使用各 dtype 的组合梯度，把一个组合 Tensor 放进列表。普通路径对 FP16 grad 的拒绝条件、组合存储和调用次序仍按已有状态机卡核对，不能为获得分批路径绕过条件。

## OpAPI：Inf/NaN 分批与饱和模式

入口先要求 `inv_scale` 为 NPU、单元素、FP32，`found_inf` 为单元素、FP32，再检查梯度列表是否为空。空列表直接返回，没有替调用者清零 `found_inf`。这里没有独立检查 `found_inf` 是否为 NPU，不能反过来解释成任意设备均被支持。

| 源码选择 | 局部执行 | 状态和分配边界 |
| --- | --- | --- |
| `IsSupportInfNan()` 为真 | 连续子列表每 250 个 Tensor 调用 `aclnnForeachNonFiniteCheckAndUnscale`，余数另调一次 | 每段传同一 `found_inf` 和 `inv_scale`，C++ 不逐段清零；此分支没有逐项执行下述梯度检查。实际检测和累计语义仍由对应 ACLNN 决定。 |
| 饱和模式且状态检测报告溢出 | 直接调用 `acl_op::_amp_foreach_non_finite_check`；`ones_out(1, found_inf)` 后返回 | 本卡不乘 `inv_scale`；不是对原值加一。 |
| 饱和模式且检测有限 | 检查每项为 NPU、与首项同 device/dtype、strided，再逐个 `op_api::mul_out(t, inv_scale, t)` | 原地逐 Tensor 乘比例，没有在此合并成上述 foreach ACLNN，也没有显式重置 `found_inf`。 |

250 是 Tensor 数量，不是参数元素数或 batch size，也不能替代调用者的 dtype/device 分组。251 个 Tensor 静态上发两次 ACLNN，500 个也发两次。子列表是 TensorList 视图，包装没有在分批循环复制全部梯度元素；这不证明底层 workspace、同步或调度成本为零。

饱和模式的梯度检查位于溢出短路之后；有限分支中又是检查一个、更新一个，不能把包装描述成先验证全列表的事务。后续元素报错时，不保证前面元素没有被修改；本卡未构造错误输入复现该状态。

## ACL：状态读取和 Inf/NaN 检测不同

`acl_op::_amp_foreach_non_finite_check` 新建 8 元素 FP32 float-status Tensor，读 `npu_get_float_status` 第 0 项并 `item().to<bool>()`，报告溢出才清状态。helper 虽接收 `scaled_grads`，函数体没有遍历这些梯度，不能当作逐元素 isfinite。

ACL 版完整反缩放入口在支持 Inf/NaN 时逐个 Tensor 计算 FP32 `sum`，以 `item().toFloat()` 取回标量并检查 `std::isfinite`，发现非有限即停止。这是归约结果检测，不等价于逐元素有限性证明；有限元素的归约也可能超出 FP32 范围。本卡记录静态算法和数值风险，未测出具体错误样本。

检测有限时，ACL 版检查 NPU、同 device/dtype、strided 后逐项 `t.mul_(inv_scale)`；否则 `found_inf.add_(1)`。它与 OpAPI 饱和分支写 1 的局部行为不同，不能依赖任意非零初值获得相同计数。ACL 入口只有上述 `inv_scale` 检查，没有 OpAPI 的两项 `found_inf` 检查；缺少本地检查不认证其余输入有效。

OpAPI 文件另有读取 RTS overflow status 的 static helper，包含 64 字节 Host/device 内存和两次流同步。审阅文件内只见其定义；实际饱和入口直接调用上述 `acl_op` helper，没有调用该 RTS helper。不能仅见 malloc/同步代码就把它们计为当前入口每次必经的成本，也不据此推定下游没有同步。

## scale 更新要追实际消费者

两版 `_amp_update_scale_` 直接调用 `aclnnAmpUpdateScale`，将 `current_scale` 和 `growth_tracker` 同时作为输入、输出，返回原 scale 引用；包装没有新建输出，也没有在本函数实现完整增长、回退及参数验证算法。底层数值规则和有效范围需另核配套 ACLNN，不能从薄包装补出保证。

所查 TorchNPU GradScaler 的 `update()` 在动态模式调用自己的 `_npu_update_scale()`：溢出时 scale 乘 backoff 并清 tracker，否则递增 tracker，到间隔时检查候选 scale 非 Inf 后更新并清计数。这两个方法没有调用上述原生 `_amp_update_scale_`。公开 GradScaler、其他实现及直接私有 ATen 调用分别追踪，不能把原生算子存在或双语产品表分歧扩大成整个 AMP 训练路径是否有效的结论。

## 版本对照与验证入口

三个 C++ 文件分别对照两版文本，并在拼接宏续行后移除注释、空白比较词法 token，均一致；两个 AMP Schema 条目也一致。这仅限定所查包装与声明，不扩展为完整 runtime、GradScaler 或数值等价认证。

定位开销时记录实际入口、Inf/NaN 模式、梯度 Tensor 数量及 dtype/device 分组，再区分 ACLNN 分批、逐 Tensor mul、float-status/item 和调用者状态读取。保持同一初始状态和软件栈，在适用设备验证空列表、250/251 个 Tensor、有限/溢出输入、重复调用及 scale/tracker 变化，再测稳态时间与峰值内存。本卡只完成静态审阅，没有执行这些实验。

- [原生融合 Adam/AdamW 的局部 AMP 参数](torch_npu_native_fused_adam_execution.md)
- [原生融合 SGD 的溢出次序](torch_npu_native_fused_sgd_execution.md)
- [融合优化器的组合存储](torch_npu_fused_optimizer_lifecycle.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AmpForeachNonFiniteCheckAndUnscaleKernelNpuOpApi.cpp)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AmpForeachNonFiniteCheckAndUnscaleKernelNpuOpApi.cpp)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/AmpForeachNonFiniteCheckAndUnscaleKernelNpu.cpp)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/AmpForeachNonFiniteCheckAndUnscaleKernelNpu.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AmpUpdateScaleKernelNpuOpApi.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AmpUpdateScaleKernelNpuOpApi.cpp)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/amp/grad_scaler.py)（implementation）
