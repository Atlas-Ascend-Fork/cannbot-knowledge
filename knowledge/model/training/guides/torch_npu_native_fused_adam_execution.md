---
type: Guide
title: 原生融合Adam执行：CPU回退、分批与AMP参数边界
description: 区分原生Adam的CPU回退/512项批处理与AdamW逐参数调用、临时状态、学习率读取及局部未消费AMP参数。
tags:
- task.optimization
- topic.optimizer
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedAdamKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedAdamWKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FusedAdamWKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_fused_adam_.py
  role: implementation
created_at: '2026-11-10T12:38:26Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 原生融合Adam执行：CPU回退、分批与AMP参数边界

## 准确入口与版本

本卡审阅OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`的aten::_fused_adam_（scalar/tensor_lr）与aten::_fused_adamw_包装。它们是原生TensorList原地更新入口，返回空元组；[NpuFusedAdam/AdamW类的组合存储生命周期](torch_npu_fused_optimizer_lifecycle.md)及自定义[npu_apply_adam_w](../apis/torch_npu/npu_apply_adam_w.md)另有准确接口与条件，不能按相近名字套用。

发布`dedc316708372c9a8bfde4527abd2a94b74840f5`存在FusedAdamWKernelNpuOpApi.cpp，两版去注释token相同；主线FusedAdamKernelNpuOpApi.cpp在发布同路径不存在。仅记录所选tree/Schema差异，不据此否定发布软件的所有优化器后端。整卡产品与配套未知，保持draft、空平台；本卡不执行上游、CPU回退、NPU或训练实验。

## Adam按SoC选择CPU回退或NPU列表分批

主线_fused_adam_先检查self/grads/exp_avgs/exp_avg_sqs/state_steps列表长度一致，max_exp_avg_sqs为空或同长度。它没有在该层建立全部Tensor的shape、dtype、device、AMSGrad状态或超参数值域矩阵。

| 路由 | 所选实现中的工作 |
| --- | --- |
| GetSocVersion()<Ascend950 | 警告后对参数、梯度、moments、max状态、step及可选grad_scale/found_inf逐项调用.cpu()形成CPU侧实参，再调用at::_fused_adam_；再把参数、moments及启用AMSGrad时的max状态copy_回原对象。 |
| 其他SoC枚举分支 | 为每个state_step创建sub(1)结果；max列表空时按每个参数zeros_like补齐临时列表；随后以最多512个参数Tensor一批调用aclnnFusedAdam。 |

这是代码的SoC门槛，不是完整设备支持矩阵。950前即使运行库有相关符号，也会走本函数的CPU分支；950后本函数未提供按缺失符号改走该CPU helper的表达式。CPU调用存在不认证目标Torch的CPU fused kernel、CPU AMP或完整训练步均可用。

CPU回退的写回循环没有把grads_cpu或state_steps_cpu复制回原列表。它的可见状态迁移要按实际caller与CPU算子的原地合同验证，不能只比较返回值（该入口没有新参数返回）。参数与状态的搬运可能增加调用成本，实际同步/耗时需设备时间线确认。

512是参数Tensor条数，不是元素数、字节数或参数组数量；P>0时本地批次数为ceil(P/512)。很多小Tensor与少数大Tensor的算子调用数和搬运不同。max列表空时，即使不使用AMSGrad也会zeros_like申请整组临时缓冲；启用AMSGrad时则要另外保证跨步最大值状态正确，不把本地临时补零当作长期历史自动维护。

## step准备和Tensor学习率仍有额外工作

NPU Adam和AdamW包装都以state_steps[i].sub(1)得到临时step再调用后端，不在这段准备代码中给原state_steps原地递增。实际步次应与PyTorch caller何时更新step及后端算法共同对照，不能只看sub(1)就宣布已经复现偏一错误。

Adam的tensor_lr重载通过lr.item<double>()读取学习率，再调用scalar重载；因此Tensor参数签名不等于保持学习率为纯设备数据、无Host读取或可直接图捕获。学习率所在设备及实际同步需要独立核对，本卡没有运行捕获或测时。

## AdamW逐参数调用，标量先收窄到float

两版_fused_adamw_检查上述列表长度后，将double形式的lr、beta1、beta2、weight_decay、eps静态转为float；遍历每个参数分别调用aclnnApplyAdamWV2，max列表空时传空Optional，否则传对应项。它没有Adam主线的512项列表批处理，也没有同一CPU回退分支。

因而这个名字中的fused不表示所有参数合并成一个调用；P个参数对应P次这里的ACLNN调用，另有每项step临时Tensor。float收窄也不等于这两个入口保留相同的Host超参数精度；本卡未展开kernel内部累加、舍入或最终数值误差。

列表长度允许max列表为空，不是证明amsgrad=True时缺失状态也有效。实际AMSGrad/maximize子集、dtype和设备继续由真实caller与后端合同确认，不能借NpuFusedAdamW类的参数页给原生入口扩权。

## AMP参数是否被消费要看这条调用链

Adam主线的NPU分支把grad_scale/found_inf作为Tensor传入aclnnFusedAdam，缺省时传未定义Tensor；CPU回退也将可选值传给CPU算子。但本卡没有审阅这些底层算法，传参不等于已证明溢出跳步、梯度反缩放和step回退均正确。

AdamW的Schema同样接收grad_scale/found_inf，C++形参名写grade_scale/found_inf；所选两版函数没有读取或转发它们，aclnnApplyAdamWV2调用参数也不含这两项。因此不能只看到原型存在Optional参数就把本地包装认证为已实现AMP协议。

这是**该局部函数未消费参数**的事实，不是整个torch.optim或GradScaler必然故障的结论。实际caller可能在到达这里前反缩放、按overflow跳过调用或维护step；需用实际优化器trace核对[GradScaler合同](torch_npu_grad_scaler_contract.md)，再覆盖有限/非有限梯度、非1缩放、连续多步和状态恢复。此处没有生成或执行完整自动求导/AMP流程。

## Eager实现与GE占位分开

已读TorchAir主线`92e1e967bd35ebc37a442b4a969730bf3cf77a3c`的aten/_fused_adam_.py只注册torch.ops.aten._fused_adam_.default，并无条件抛NotImplementedError。不能用上面的NPU Eager包装存在来证明这个准确GE重载已实现，也不从这一文件否定其他重载/后端；全量占位索引见[GE未实现重载](../../inference/guides/optimization/torchair/torchair_ge_unimplemented_overloads.md)。

对比优化器时记录实际FX/ATen入口、SoC分支、参数列表条数与大小、临时max/step分配、CPU往返、学习率读取和AMP调用顺序，再比较多步参数/moments/step与参考及完整耗时。本卡没有性能数字、设备运行或新增verified。


## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedAdamKernelNpuOpApi.cpp)（primary）：18–284。

- [固定实现来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedAdamWKernelNpuOpApi.cpp)（implementation）：1–66。

- [固定实现来源 3](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FusedAdamWKernelNpuOpApi.cpp)（implementation）：20–66。

- [固定实现来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：615–622。

- [固定实现来源 5](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：606–607。

- [固定实现来源 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_fused_adam_.py)（implementation）：1–24。
