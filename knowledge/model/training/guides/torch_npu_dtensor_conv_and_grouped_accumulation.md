---
type: Guide
title: TorchNPU DTensor卷积与分组原地累加布局
description: 说明卷积batch和输出通道候选的梯度归约，以及分组原地累加的输出布局保护。
tags:
- task.optimization
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/tensor/_math_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/distributed/tensor/_math_ops.py
  role: implementation
created_at: '2026-11-11T06:35:50Z'
updated_at: '2026-11-11T06:35:50Z'
platforms: []
---

# TorchNPU DTensor卷积与分组原地累加布局

## 来源范围

依据PyTorch仓主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`和发布快照`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的_math_ops.py，卷积前反向和npu_grouped_matmul_add_策略函数完整AST相同。这里只覆盖注册候选，不替代算子shape、dtype、产品与通信合同；未运行上游或设备实验。

## 卷积的batch与输出通道候选

前向注释布局为x=(N,Ci,Hi,Wi)，weight=(Co,Ci/groups,Hk,Wk)，输出=(N,Co,Ho,Wo)。始终给全部复制及batch候选：x/输出Shard(0)，weight与存在的bias复制。仅groups==1时再给输出通道候选：x复制、weight及存在的bias沿Shard(0)，输出Shard(1)。stride/padding/dilation/groups作为非张量槽，除groups条件外没有在策略中验证完整卷积合法性。

反向先读取grad_output.placements[0]，不是遍历所有mesh维。始终给复制候选；仅当这个placement是Shard(0)才加入batch反向：dx=Shard(0)，dweight=Partial，存在时dbias=Partial；输入x/grad_output沿0分片，weight复制。

当首个grad_output placement为Shard(1)且groups==1时加入通道反向：dx=Partial，dweight及存在的dbias=Shard(0)；x复制、grad_output=Shard(1)、weight=Shard(0)。因此“前向按通道分片”不意味着输入梯度仍是可直接消费的完整复制Tensor；Partial可能要求后续归约。

output_mask仅用索引2控制bias梯度是否None，这些策略没有根据mask[0]/mask[1]移除dx/dweight spec。不能把任意output_mask或多维mesh声明为已完整验证，也不能由首placement判断扩写成检查了全部placement。

## 分组原地累加保护输出已有布局

npu_grouped_matmul_add_首先读取y.placements[0]；若它是Shard(0)立即抛ValueError，即使随后存在复制候选也不会先尝试自动重分布。否则加入两种候选：全部复制；或者y输出/y输入/weight沿Shard(1)，x与group_list复制。

transpose_x、transpose_weight和group_type仅占非张量None位置，函数不据它们重算维度或分别过滤；也不对所有mesh维的Shard(0)进行检查。这里的原地布局规则不能推广为所有转置和group模式都等价合法，更不能解释为会自动消除原地写别名风险。

## 优化验收

将权重、激活和梯度布局一起核对，分别观察batch方案的dweight归约、通道方案的dx归约，以及原地y的实际placement；比较端到端通信、显存和数值，不只看前向候选是否存在。[归一化与激活规则](torch_npu_dtensor_norm_rope_and_activation.md)和[损失归约规则](torch_npu_dtensor_loss_and_repeat_layouts.md)属于同模块不同算子，不能相互继承候选。
