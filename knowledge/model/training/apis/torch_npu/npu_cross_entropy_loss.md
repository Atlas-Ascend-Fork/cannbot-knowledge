---
type: API
title: npu_cross_entropy_loss：训练参数限制与四个返回槽
description: 说明仅 loss 支持梯度、requires_grad 下的归约限制以及暂未支持的 zloss 选项。
tags:
- task.lookup
- topic.compute.reduction
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_cross_entropy_loss.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_cross_entropy_loss.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_cross_entropy_loss.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
created_at: '2026-11-09T06:21:37Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
- '950'
---

# npu_cross_entropy_loss：训练参数限制与四个返回槽

## 固定来源

依据 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的接口页和同提交 Schema。产品、模式和参数范围以本卡明确限定为准，不回推发布快照或推定主线软件栈配套；未执行算子或NPU实验。

## 接口与输入

```text
npu_cross_entropy_loss(input, target, weight=None, reduction='mean',
    ignore_index=-100, label_smoothing=0.0,
    lse_square_scale_for_zloss=0.0, return_zloss=False)
    -> (loss, log_prob, zloss, lse_for_zloss)
```

融合log_softmax与NLL。input为FP16/BF16/FP32、shape=(N,C)，0<N≤200000，C>0；target为INT64、shape=(N,)，有效类别在[0,C)。weight若给定为FP32、shape=(C,)、取值(0,1]。ignore_index须<C，文档将负值说明为不指定忽略标签，不直接照搬其他CrossEntropy的负标签语义。

reduction为mean/sum/none；label_smoothing范围[0,1)。input.requires_grad=True时，sum/none只允许默认label_smoothing=0，mean还要求weight、ignore_index等可选项为默认；不能将无梯度的参数组合套到训练反向。

## 输出与未实现能力

loss与input同dtype，none时(N,)，其他模式(1,)；log_prob同input shape/dtype，用作反向中间量。只有loss支持梯度，不能对log_prob再构造任意可微损失并期待自动求导。

签名中的lse_square_scale_for_zloss、return_zloss及对应输出当前暂不支持，保留默认0/False，后两个返回槽不能当有效zloss数据。接口页仅列训练用途，支持Eager与图模式；不是通用推理交叉熵替换承诺。


## 验证

在相同输入和计算口径下比较参考输出，核对每个中间量的shape/dtype、原地关系及有效性；训练覆盖梯度与多步调用，再测稳态时间和内存。单次导入或构造成功不代表该模式已验证。

## 发布、Meta与生成式辅助输出的差异

发布中文已给相同四槽协议、输入及反向参数限制；主线中英文新增950PR及950DT并明确仅训练、Eager/图模式，不将主线产品承诺回推发布。主线两语言lse公式出现log*sum写法，不能照抄为计算参考；log_softmax的数值参考应独立核对。

两固定形状helper在默认return_zloss=False、scale=0时将zloss/lse槽分配为(0,)；但两版Meta始终给zloss与loss同形、lse为(N,)，忽略这两个开关。因此默认辅助槽的Eager/Meta形状存在静态冲突；不能只据Fake/Meta形状消费这些未使能输出。

两版derivatives又将第三槽zloss标为可微，并保留相应反向参数，而产品文档明确暂不支持它，仅loss在公开支持子集中可求梯度。注册条目不等于功能已使能，不能用这份声明解除文档约束；训练图须实际核对辅助形状和反向消费，未有设备验证。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_cross_entropy_loss.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_cross_entropy_loss.md)（primary）

- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_cross_entropy_loss.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）

- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）

- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml)（implementation）

- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）
