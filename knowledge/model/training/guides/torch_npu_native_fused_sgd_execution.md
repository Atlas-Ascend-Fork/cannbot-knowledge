---
type: Guide
title: 原生融合SGD：溢出跳过、设备检查与Host标量
description: 区分scalar/tensor_lr重载的found_inf检查顺序、正动量、设备条件与item读取，限定原生列表更新及AMP接入边界。
tags:
- task.optimization
- topic.optimizer
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedSgdKernelOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-10T12:50:20Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# 原生融合SGD：溢出跳过、设备检查与Host标量

## 固定入口与同名优化器区别

本卡审阅OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`的aten::_fused_sgd_与tensor_lr重载。两者更新参数/梯度/动量TensorList，Schema返回空元组，OpAPI注册范围标为v2.7至newest；这不是完整产品或配套矩阵。发布`dedc316708372c9a8bfde4527abd2a94b74840f5`无同路径FusedSgdKernelOpApi.cpp，仅记录准确tree差异，不据此否定其他发布SGD实现。

[NpuFusedSGD类](../apis/torch_npu/npu_fused_sgd.md)及其[组合存储生命周期](torch_npu_fused_optimizer_lifecycle.md)是另一条准确接口，类构造器可用零momentum的规则不能直接套到这里。整卡平台未知，保持draft、空平台；没有执行上游、设备、AMP或性能实验。

## 两个学习率重载的检查顺序不同

| 重载 | 手写函数中的前置顺序 |
| --- | --- |
| Scalar lr | found_inf存在且item().toFloat()==1时立即返回；否则先把momentum转float并要求>0，再对params/grads调用ATen fast_path限制检查，检查首步提示，最后准备其余标量和调用。 |
| Tensor lr | 先检查params/grads fast_path，输出首步提示，检查可选grad_scale/found_inf及lr的device与params[0]一致；再读found_inf判断是否立即返回，之后检查正momentum并读取lr。 |

因此overflow跳过与输入校验不是同一件事：Scalar重载可在后面的局部动量/fast_path检查之前退出，Tensor重载仍先做所列检查。不能从一次跳过调用成功推断其余参数已经验合法，也不把两个重载的异常顺序合成统一保证。

所选代码对found_inf判断的是转换后**精确等于1**，没有本地把任意非零数或NaN统一解释为应跳过；本卡未运行这些异常标志。正常AMP调用方应维持其实际标志协议。found_inf缺省或不命中该条件时继续准备调用，本层没有把它下传给aclnnFusedSgd。

## 正动量与动量缓冲须由实际调用链核对

两个重载都要求转换为float后的momentum>0，条件不依赖nesterov。它不是通用SGD的momentum=0默认路线。weight_decay、lr、dampening也被收窄为float，但手写函数没有建立它们全部合法值域或Nesterov组合矩阵；不由透传认定所有组合有效。

is_first_step=True且momentum_buffer_list为空时，只发一次警告“首步参数无效”，没有在这段函数中自动申请并加入动量Tensor；随后仍继续调用。首步/恢复训练时需由真实caller保持动量历史，不能从标志名字推导已替调用方构建状态。

fast_path helper只以params/grads两组列表作为所选实参；本卡未展开ATen头文件里的全部限制，不能据函数名补造BF16、任意stride、跨设备或所有动量列表的支持矩阵。Schema还将tensor_lr标为device_check:NoCheck，应沿真实生成包装与手写检查判断设备合同，不把默认检查假设代替源码。

## Tensor学习率仍被读取为Host数值

Tensor重载虽然先要求lr与params[0]同device，实际调用前仍执行lr.item().toFloat()。因此Tensor lr不是直接传给ACLNN的设备端学习率Tensor；设备上的found_inf在两个重载中也通过item读取。不能用Tensor签名认证纯设备控制、无Host读取或可直接图捕获；具体同步与时间线没有实测依据。

Scalar重载的手写函数没有复刻Tensor重载针对Optional项的那组单独device检查；这只是局部代码区别，生成包装/dispatcher和后端可能另行校验，本卡不据此放宽Scalar路径的输入域。

## 真正传给ACLNN的内容与验收

未跳过时，两个重载都把params、grads、momentum_buffer_list及grad_scale（缺省为未定义Tensor），连同收窄后的weight_decay/momentum/lr/dampening和nesterov/maximize/is_first_step传给aclnnFusedSgd。所选函数没有CPU回退表达式或[原生Adam](torch_npu_native_fused_adam_execution.md)的512项分批循环；这些局部差异不说明kernel内部如何并行或所有设备均支持。

grad_scale被转发不等于已证明完整AMP协议；found_inf的本地跳过、梯度反缩放、caller状态和动态学习率要按真实[GradScaler路径](torch_npu_grad_scaler_contract.md)一起核对。本卡未展开标准torch.optim完整caller、生成式自动求导或底层SGD算法，也不宣称整个AMP必然成功或失败。

验收覆盖两个lr重载、found_inf为0/1及缺省、momentum为0/正值、首步/后续/恢复、可选Tensor设备及Nesterov/衰减，比较多步参数与动量再测端到端耗时。局部guard、注册或符号存在均不替代数值与性能验证；本卡没有新增verified。


## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedSgdKernelOpApi.cpp)（primary）：1–90。

- [固定实现来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：5591–5596。
