---
type: API
title: NpuFusedAdamW：解耦衰减与参数对象稳定性
description: 记录默认权重衰减及构造器范围，避免从源码注释推定 maximize 等额外参数可用。
tags:
- task.lookup
- topic.optimizer
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdamW.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_optim_base.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_adamw.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdamW.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdamW.md
  role: constraint
created_at: '2026-11-09T03:49:48Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
- '950'
---

# NpuFusedAdamW：解耦衰减与参数对象稳定性

## 版本与范围

依据 OpPlugin `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页，发布页为A2/A3训练，主线页另确认950DT；补充 PyTorch `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的静态实现。两仓主线不自动构成配套，不回推为发布包或所有 PyTorch 同名优化器选项均兼容。


```text
NpuFusedAdamW(params, lr=1e-3, betas=(0.9,0.999), eps=1e-8,
    weight_decay=1e-2, amsgrad=False)
```

lr/eps/weight_decay 非负，两个 beta 在 [0,1)。默认 weight_decay=1e-2，与 NpuFusedAdam 的 0 不同。所查实现先对参数乘 1-lr*weight_decay，再做 Adam 更新，是解耦衰减；不支持稀疏梯度。

实现的 docstring 虽提 maximize，真实 __init__ 与接口原型均没有该参数；不能把注释中的参数当作受支持签名。核心算法兼容描述不等于 PyTorch AdamW 的所有新版开关或分布式状态格式兼容。


## 生命周期与验证

固定基类仅组合 FP16/FP32 参数；初始化组合后不应更换参数对象或存储，zero_grad(set_to_none=True) 会报错。融合和分片、量化优化器是不同机制，不能据名字宣称 BF16、FSDP/ZeRO 或所有动态图组合兼容。

先比较相同初始参数、梯度及超参数下多步更新、状态和恢复，再测稳态时间；本卡没有执行优化器或 NPU 实验。

- [组合存储、梯度清零和裁剪](../../guides/torch_npu_fused_optimizer_lifecycle.md)
- [AMP 梯度缩放](../../guides/torch_npu_grad_scaler_contract.md)

## 双语和发布页的产品、参数补充

发布中文列A2/A3训练及旧Atlas训练，主线中文/英文另确认950DT；metadata新增950只对应这份主线产品表，不扩大到950PR，不把独立PyTorch主线实现当配套发布。

Adam/AdamW主线将两个beta边界明确为[0,1)，发布参数表写>1，不能把beta=1当已确认合法。

参数对象禁止重新申请、一次step样例未用所导入AMP及未做数值对照的边界保持；本卡只补完整文档差异，不消除已有源码限制或声称性能实测。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdamW.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_optim_base.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_adamw.py)（implementation）

- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdamW.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdamW.md)（constraint）
