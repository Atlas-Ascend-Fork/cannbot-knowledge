---
type: Guide
title: TorchNPU DTensor Dropout数据和mask分片
description: TorchNPU DTensor Dropout数据和mask分片的固定双版本本地规则、重分布边界与验收条件。
tags:
- task.optimization
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/tensor/_matrix_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/distributed/tensor/_matrix_ops.py
  role: implementation
created_at: '2026-11-11T06:44:03Z'
updated_at: '2026-11-11T06:44:03Z'
platforms: []
---

# TorchNPU DTensor Dropout数据和mask分片

固定PyTorch仓主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`与发布快照`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的distributed/tensor/_matrix_ops.py。本文仅说明本地候选和派发实现，不据注册推导全部产品、dtype、shape或通信组合可用；未导入运行上游或设备实验。

## 数据输出与mask不沿同一张量维

native_dropout策略只看input第一条策略的spec。若其首mesh placement是Shard且该张量维长度小于mesh.size(0)，直接返回数据输出复用input_spec、mask=[Shard(0)]的特殊spec，没有另外给mask写tensor_meta；其余情况先给复制候选，再为每个输入dim加入数据Shard(dim)、mask固定Shard(0)、输入Shard(dim)的单维方案，以input_index=2交外部mesh展开。

这不是把mask按数据dim同样切分；不同dim、空分片和多维mesh应分别检查真实mask形状与位置。函数没有依据dropout概率或train标志另分支，也没有在此证明各rank随机流与单卡一致，不能由前向placement推导随机数或数值等价。

backward收集各OpStrategy输入的第一份output_spec作为输入目标，输出直接采用第一个参数首spec；没有在函数体重新校验grad与mask布局或重算mask切分。是否需要转换、如何处理NPU底层mask属于外部消费合同，未在本组运行。

## 本地最大可分片维helper的边界

_get_max_shardable_dim使用默认进程组get_world_size，筛出shape中可被它整除的维，选尺寸最大者的索引，无候选返回-1，同尺寸保留前面的维。它没有读取传入Tensor的DeviceMesh，也没有在本模块其它已读函数中被调用；不能把这个helper写成Dropout或Matmul已经启用的自动布局优化器。

验收记录参与rank、input与mask局部shape、placements、随机状态和反向数值；比较实际重分布开销。逐点与其他注册分支见[DTensor重分布与注册](torch_npu_dtensor_redistribution_and_registration.md)，不能把所有逐点算子视为同一种mask合同。
