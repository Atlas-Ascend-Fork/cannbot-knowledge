---
type: API
title: NpuFusedLamb：Trust Ratio、默认 epsilon 与待核验分支
description: 限定默认全局范数关闭的路径，记录注释默认值及辅助方法缺口，避免未验证的收敛保证。
tags:
- task.lookup
- topic.optimizer
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedLamb.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_optim_base.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_lamb.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedLamb.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedLamb.md
  role: constraint
created_at: '2026-11-09T03:49:48Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
- '950'
---

# NpuFusedLamb：Trust Ratio、默认 epsilon 与待核验分支

## 版本与范围

依据 OpPlugin `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页，发布页为A2/A3训练，主线页另确认950DT；补充 PyTorch `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的静态实现。两仓主线不自动构成配套，不回推为发布包或所有 PyTorch 同名优化器选项均兼容。


```text
NpuFusedLamb(params, lr=1e-3, betas=(0.9,0.999), eps=1e-6,
    weight_decay=0, adam=False, use_global_grad_norm=False)
```

本卡只提供 use_global_grad_norm=False 的静态契约。lr/eps 非负，beta 在 [0,1)；真实构造器与接口页 eps=1e-6，而实现 docstring 写 1e-8，不能据注释覆盖签名。所查实现不支持稀疏梯度。

adam=True 将 trust ratio 置 1；否则按参数范数与更新范数设置比例。实现将参数范数截到 [0,10]，零范数分支使用比例 1；这是所查实现细节，不把论文或接口简介的“大 batch 稳定收敛”当作本任务验证结果。

use_global_grad_norm=True 会进入 _get_global_grad_norm，但所查本类/基类中没有它调用的 get_optimizer_combined_grads/get_optimizer_combined_grad_masks 方法；本快照 torch_npu 树的文本查找也仅找到这些调用。本卡未执行该分支，不能宣称它可用，也不把 global 名称解释成跨 rank AllReduce。该分支保持待核验，不提供启用配方。


## 生命周期与验证

固定基类仅组合 FP16/FP32 参数；初始化组合后不应更换参数对象或存储，zero_grad(set_to_none=True) 会报错。融合和分片、量化优化器是不同机制，不能据名字宣称 BF16、FSDP/ZeRO 或所有动态图组合兼容。

先比较相同初始参数、梯度及超参数下多步更新、状态和恢复，再测稳态时间；本卡没有执行优化器或 NPU 实验。

- [组合存储、梯度清零和裁剪](../../guides/torch_npu_fused_optimizer_lifecycle.md)
- [AMP 梯度缩放](../../guides/torch_npu_grad_scaler_contract.md)

## 双语和发布页的产品、参数补充

发布中文列A2/A3训练及旧Atlas训练，主线中文/英文另确认950DT；metadata新增950只对应这份主线产品表，不扩大到950PR，不把独立PyTorch主线实现当配套发布。

Lamb主线把use_global_grad_norm说明改为全局梯度范数；既有实现缺失辅助方法的待核验分支不由文档支持表消除。

参数对象禁止重新申请、一次step样例未用所导入AMP及未做数值对照的边界保持；本卡只补完整文档差异，不消除已有源码限制或声称性能实测。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedLamb.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_optim_base.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/npu_fused_lamb.py)（implementation）

- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedLamb.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedLamb.md)（constraint）
