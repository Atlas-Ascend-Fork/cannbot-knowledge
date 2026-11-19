---
type: Guide
title: TorchNPU DTensor MoE隐藏维分片与概率梯度归约
description: 按固定双版本说明MoE置换与反置换候选布局、Partial概率梯度及主线v2差异。
tags:
- task.optimization
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/tensor/_moe_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/distributed/tensor/_moe_ops.py
  role: implementation
created_at: '2026-11-11T06:29:26Z'
updated_at: '2026-11-11T06:29:26Z'
platforms: []
---

# TorchNPU DTensor MoE隐藏维分片与概率梯度归约

## 固定实现范围

依据PyTorch仓主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`和发布快照`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的`distributed/tensor/_moe_ops.py`。本文描述本地注册函数返回的候选placement，策略选择、重分布执行与实际算子合法输入仍由外部实现决定。没有运行注册、通信或设备测试，不由这些规则补出产品或dtype支持矩阵。

## 候选策略保留token路由索引的复制布局

两版对下列四个入口各返回“全部复制”和“隐藏维分片”两条候选。`R`表示Replicate，`S1`表示Shard(1)，`P`表示Partial；标量控制参数在策略输入中用None占位。

| 入口 | 隐藏维候选的张量输入 | 张量输出 |
|---|---|---|
| npu_moe_token_permute | tokens=S1，indices=R | permuted_tokens=S1，sorted_indices=R |
| npu_moe_token_permute_grad | tokens和grad_permuted_tokens=S1，indices和sorted_indices=R | tokens梯度=S1 |
| npu_moe_token_unpermute | permuted_tokens=S1，sorted_indices=R，存在时probs=R | unpermuted_tokens=S1 |
| npu_moe_token_unpermute_grad | permuted_tokens和grad_unpermuted_tokens=S1，sorted_indices=R，存在时probs=R | token梯度=S1，概率梯度=P |

它们分片的是二维token表示的第1维，不是对token数量或专家路由索引分片。全部复制候选把实际存在的张量输入和输出设为R；unpermute前向的probs缺省时输入placement为None，反向全部复制候选的概率梯度placement也为None。

## 概率梯度的Partial不能直接当作完整梯度

隐藏维分片的unpermute反向把概率梯度声明为`Partial()`，表示局部贡献尚待后续按布局需求处理。消费端需要核对归约与重分布，不能把S1 token梯度和Partial概率梯度统一视为已经完整的本地梯度，也不能仅据注册策略断言该算子内部已经AllReduce。

源码的隐藏维候选无条件给第二输出Partial，即使probs为None也如此；全部复制候选才对该输出按probs是否存在选择None。本文保留这一静态差异，不把它补成无probs时一定产生有效概率梯度的运行保证。各策略也没有根据padded_mode、restore_shape、num_out_tokens逐一分支验证形状或数值。

## 主线增加的反向与保存张量布局

主线还注册三个本地函数：permute_grad_v2把grad_permuted_tokens设S1、sorted_indices设R，输出S1；tokens_size_0、tokens_dtype、num_topK和padded_mode均只占None位置。

私有`_npu_moe_token_unpermute`返回两个张量，隐藏维候选将unpermuted_tokens和供反向保存的permuted_tokens均设S1；sorted_indices与存在时的probs为R。

unpermute_grad_v2将grad_unpermuted_tokens设S1、sorted_indices设R；存在时probs为R，存在时permuted_tokens为S1；返回token梯度S1和概率梯度Partial。全部复制候选对可选张量及概率梯度按None处理。这三项未在发布快照的此模块中注册，不能据文件差异断言发布版本没有其他实现路径。

## 优化与验收

使模型的hidden维布局与这些候选吻合，可作为减少布局转换的评估起点；实际选择仍可能引入通信，不能承诺零重分布。比较前向、token梯度和概率梯度，保留有/无probs、有/无保存张量、padding与实际形状，并观察重分布和归约。接口名单与dtype条件见[原生张量并行约束](torch_npu_native_tensor_parallel_constraints.md)，注册和关键字参数处理见[DTensor重分布与注册](torch_npu_dtensor_redistribution_and_registration.md)。
