---
type: API
title: NpuFusedAdadelta：默认参数、rho边界与融合状态
description: 保存Adadelta构造与非负约束，区分接口默认值和一次step样例的验证范围。
tags:
- task.lookup
- topic.optimizer
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdadelta.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdadelta.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdadelta.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_adadelta.py
  role: implementation
created_at: '2026-11-09T19:09:59Z'
updated_at: '2026-11-09T19:09:59Z'
platforms:
- a2
- a3
- '950'
---

# NpuFusedAdadelta：默认参数、rho边界与融合状态

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5的中文页及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda的中英文页。A2/A3在本卡指训练系列，主线新增950DT确认不回推到发布版，不扩到950PR。旧Atlas产品只保留来源条目，不自动映射其他新型号。

发布配对PyTorch提交为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；补充独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf时单独指出，两个main不构成自动配套。以下为静态合同，没有编译、导入、加载模型、设备运行或性能测量。


## 构造与参数

```text
NpuFusedAdadelta(params, lr=1.0, rho=0.9, eps=1e-6, weight_decay=0)
```

lr、eps、weight_decay非负；rho是梯度平方滑动平均衰减系数，允许[0,1]，越界抛ValueError。rho上界与Adam类beta的[0,1)不同。发布配对实现1–60行对应这些检查，square_avg和acc_delta以zeros_like初始化；这里只读到状态初始化附近，不宣称整个更新算法已经验证。

## 对象寿命和验收

返回对应优化器对象，params可为模型参数或参数组。文档要求使用期间不重新申请参数对象：模块移到CPU、参数换对象或置None会破坏前提；原地计算/读取值允许，但不能据此无条件改变底层storage或梯度对象。详见[融合存储生命周期](../../guides/torch_npu_fused_optimizer_lifecycle.md)。

核心功能兼容或“高性能”描述不证明所有PyTorch新版参数、BF16、稀疏梯度、FSDP/ZeRO、图模式或状态格式均兼容。页面示例混用FP16/FP32、手工设置梯度且末参数无grad，只执行一次step；虽导入GradScaler/autocast却未使用，不是完整AMP、多步数值或收敛验收。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdadelta.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdadelta.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-optim/torch_npu-optim-NpuFusedAdadelta.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/npu_fused_adadelta.py)（implementation）
