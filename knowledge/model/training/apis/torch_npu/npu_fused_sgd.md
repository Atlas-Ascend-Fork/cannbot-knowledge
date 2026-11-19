---
type: API
title: NpuFusedSGD：必填学习率与 Nesterov 条件
description: 以真实构造器限定动量和 Nesterov，记录文档对零动量条件的遗漏。
tags:
- task.lookup
- topic.optimizer
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedSGD.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_optim_base.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_sgd.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedSGD.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedSGD.md
  role: constraint
created_at: '2026-11-09T03:49:48Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
- '950'
---

# NpuFusedSGD：必填学习率与 Nesterov 条件

## 版本与范围

依据 OpPlugin `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页，发布页为A2/A3训练，主线页另确认950DT；补充 PyTorch `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的静态实现。两仓主线不自动构成配套，不回推为发布包或所有 PyTorch 同名优化器选项均兼容。


```text
NpuFusedSGD(params, lr, momentum=0, dampening=0,
    weight_decay=0, nesterov=False)
```

lr 必填且非负，momentum/weight_decay 非负。nesterov=True 时，所查实现要求 momentum>0，并通过 math.isclose(dampening,0,abs_tol=1e-15) 检查零 dampening；文档写 momentum<0 的触发描述遗漏了 momentum=0 也会被拒绝。

该容差是固定实现细节，不推荐依赖接近零的非零参数来绕过语义约束。第一次动量 buffer 来自当前梯度（含适用的权重衰减），后续才按动量和 dampening 更新；验收应包含首步及恢复后的多步。


## 生命周期与验证

固定基类仅组合 FP16/FP32 参数；初始化组合后不应更换参数对象或存储，zero_grad(set_to_none=True) 会报错。融合和分片、量化优化器是不同机制，不能据名字宣称 BF16、FSDP/ZeRO 或所有动态图组合兼容。

先比较相同初始参数、梯度及超参数下多步更新、状态和恢复，再测稳态时间；本卡没有执行优化器或 NPU 实验。

- [组合存储、梯度清零和裁剪](../../guides/torch_npu_fused_optimizer_lifecycle.md)
- [AMP 梯度缩放](../../guides/torch_npu_grad_scaler_contract.md)

## 双语和发布页的产品、参数补充

发布中文列A2/A3训练及旧Atlas训练，主线中文/英文另确认950DT；metadata新增950只对应这份主线产品表，不扩大到950PR，不把独立PyTorch主线实现当配套发布。

SGD发布把Nesterov条件错误写TypeError，主线中英文改为ValueError；文档momentum<0仍漏了0，实际已核对实现要求>0，保留该区别。

参数对象禁止重新申请、一次step样例未用所导入AMP及未做数值对照的边界保持；本卡只补完整文档差异，不消除已有源码限制或声称性能实测。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedSGD.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_optim_base.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_sgd.py)（implementation）

- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedSGD.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedSGD.md)（constraint）
