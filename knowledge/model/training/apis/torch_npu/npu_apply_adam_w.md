---
type: API
title: npu_apply_adam_w：950 Eager 的 out 原地更新
description: 说明必须提供 var/m/v、无 out 实现拒绝，以及 AMSGrad 描述不等于当前支持 True。
tags:
- task.lookup
- topic.optimizer
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_apply_adam_w.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ApplyAdamWKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_apply_adam_w.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ApplyAdamWKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ApplyAdamWKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ApplyAdamWKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T06:21:37Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- '950'
---

# npu_apply_adam_w：950 Eager 的 out 原地更新

## 固定来源

依据 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的接口页和同提交 Schema。产品、模式和参数范围以本卡明确限定为准，不回推发布快照或推定主线软件栈配套；未执行算子或NPU实验。

## 接口与支持子集

```text
npu_apply_adam_w(beta1_power, beta2_power, lr, weight_decay,
    beta1, beta2, epsilon, grad, max_grad_norm, amsgrad, maximize,
    out=(var, m, v)) -> (var, m, v)
```

显式提供out，原地更新参数、一阶矩与二阶矩，并返回同一组Tensor对象；不是创建三个新状态。固定OpAPI实现的无out分支直接报未实现，不能省略out。文档给max_grad_norm/amsgrad/maximize默认None，但Schema的Optional参数没有省略默认值，明确传None/False/False可避免把“允许None”理解成一定可省略。

var/m/v/grad的shape一致，支持FP16/BF16/FP32 ND，m/v同var类型，max_grad_norm若传入同grad shape/dtype。标量超参数按文档同类浮点表示。weight decay先以1-lr*weight_decay作用于var，再结合矩估计更新，是解耦衰减；maximize支持反向梯度方向。

通用公式虽描述AMSGrad，当前产品页明确amsgrad仅False；“True时必须提供max_grad_norm”的必要检查不代表True已受支持。它是历史二阶矩最大值参数，不是常见梯度裁剪global norm。

仅950、训练、Eager范围；不能把本接口BF16或maximize支持套给NpuFusedAdamW类。OpAPI包装还按运行路径选择aclnn或旧acl_op，不能从代码中存在aclnn调用推定任意CANN都走它。

- [另一入口NpuFusedAdamW的生命周期](npu_fused_adamw.md)


## 验证

在相同输入和计算口径下比较参考输出，核对每个中间量的shape/dtype、原地关系及有效性；训练覆盖梯度与多步调用，再测稳态时间和内存。单次导入或构造成功不代表该模式已验证。

## 标量搬运、旧回退与发布缺页

主线中英文仅列950PR及950DT、训练和Eager；发布快照没有该公开页。同名ACL/OpAPI实现在两提交都存在，但无out分支均直接报错，不能把存在实现推成发布产品支持。

两版OpAPI在ACLNN-only分支将七个Scalar复制为grad.dtype、grad.device上的设备Tensor后调用aclnnApplyAdamW，amsgrad/maximize无值时取False；其他路径走旧ACL，缺符号也按兼容机制回退。旧ACL处理var/m/v格式并写回相同状态，只有可选bool有值时传属性。源码检查True时有max_grad_norm只是必要检查，不能覆盖文档仅False约束；也不把该状态Tensor误当全局梯度范数裁剪。幂次乘beta及epsilon在平方根外的公式须与原优化器状态更新时点共同核对。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_apply_adam_w.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ApplyAdamWKernelNpuOpApi.cpp)（implementation）

- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_apply_adam_w.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ApplyAdamWKernelNpu.cpp)（implementation）

- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ApplyAdamWKernelNpu.cpp)（implementation）

- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ApplyAdamWKernelNpuOpApi.cpp)（implementation）

- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
