---
type: API
title: NpuFusedAdamP：投影阈值、衰减比例与动量选项
description: 保存delta、wd_ratio、Nesterov参数，限定局部投影实现与未验证的算法组合。
tags:
- task.lookup
- topic.optimizer
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdamP.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdamP.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdamP.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_adamp.py
  role: implementation
created_at: '2026-11-09T19:09:59Z'
updated_at: '2026-11-09T19:09:59Z'
platforms:
- a2
- a3
- '950'
---

# NpuFusedAdamP：投影阈值、衰减比例与动量选项

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5的中文页及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda的中英文页。A2/A3在本卡指训练系列，主线新增950DT确认不回推到发布版，不扩到950PR。旧Atlas产品只保留来源条目，不自动映射其他新型号。

发布配对PyTorch提交为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；补充独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf时单独指出，两个main不构成自动配套。以下为静态合同，没有编译、导入、加载模型、设备运行或性能测量。


## 构造

```text
NpuFusedAdamP(params, lr=1e-3, betas=(0.9,0.999), eps=1e-8,
    weight_decay=0, delta=0.1, wd_ratio=0.1, nesterov=False)
```

lr为学习率，betas为一阶/二阶矩系数，eps用于数值稳定；delta为余弦相似度阈值，wd_ratio为动态衰减比例，nesterov选择动量变体。文档没有给这几个参数完整合法域，不能沿用另一个Adam类的错误检查来补造本接口行为。

发布配对实现1–80行中构造直接保存defaults；局部projection按channel/layer视图的余弦条件，调整更新方向并返回wd_ratio或默认1。它不是所有参数统一投影的保证，也不等于已经复核完整step、所有维度/stride与稀疏分支。论文外链未自动摄入，不能据简介承诺收敛改善。

## 对象寿命和验收

返回对应优化器对象，params可为模型参数或参数组。文档要求使用期间不重新申请参数对象：模块移到CPU、参数换对象或置None会破坏前提；原地计算/读取值允许，但不能据此无条件改变底层storage或梯度对象。详见[融合存储生命周期](../../guides/torch_npu_fused_optimizer_lifecycle.md)。

核心功能兼容或“高性能”描述不证明所有PyTorch新版参数、BF16、稀疏梯度、FSDP/ZeRO、图模式或状态格式均兼容。页面示例混用FP16/FP32、手工设置梯度且末参数无grad，只执行一次step；虽导入GradScaler/autocast却未使用，不是完整AMP、多步数值或收敛验收。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdamP.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdamP.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdamP.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_adamp.py)（implementation）
