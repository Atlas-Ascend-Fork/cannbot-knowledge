---
type: API
title: NpuFusedOptimizerBase：构造、继承与首次参数组合
description: 明确基类需子类实现更新，保存default字典、FP16/FP32与一次组合的前提。
tags:
- task.lookup
- topic.optimizer
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedOptimizerBase.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedOptimizerBase.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedOptimizerBase.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_optim_base.py
  role: implementation
created_at: '2026-11-09T19:09:59Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# NpuFusedOptimizerBase：构造、继承与首次参数组合

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5的中文页及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda的中英文页。A2/A3在本卡指训练系列，主线新增950DT确认不回推到发布版，不扩到950PR。旧Atlas产品只保留来源条目，不自动映射其他新型号。

发布配对PyTorch提交为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；补充独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf时单独指出，两个main不构成自动配套。以下为静态合同，没有编译、导入、加载模型、设备运行或性能测量。


## 构造与返回

`torch_npu.optim.NpuFusedOptimizerBase(params, default)`接收参数/参数组迭代对象及其他默认超参数字典，返回基类对象。文档明确不能独立用作具体优化器，需继承子类实现状态和更新；示例仅展示构造及__setstate__，没有完整step实现，不能当可训练算法。

发布配对实现1–92行，基类继承torch.optim.Optimizer并保存多组组合缓存标志，首次按有grad参数扫描：FP32/FP16分别组合；其他参数dtype抛TypeError；grad=None跳过。参数与梯度格式不一致会转换梯度并contiguous，不是无拷贝保证。已组合标志会跳过再次扫描，不能据此宣称新解冻参数自动加入。

基类与[张量合并工具](../../../inference/apis/torch_npu/combine_tensors.md)分开：底层指针重定向支持某dtype不使整个融合优化器接受该dtype。zero_grad、裁剪、AMP反缩放及对象恢复次序见[生命周期指南](../../guides/torch_npu_fused_optimizer_lifecycle.md)，该指南独立保留自己的硬件与实现范围。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedOptimizerBase.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedOptimizerBase.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedOptimizerBase.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_optim_base.py)（implementation）
