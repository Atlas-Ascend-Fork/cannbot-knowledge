---
type: Guide
title: TorchNPU DTensor通信Matmul的布局和全局Meta修正
description: TorchNPU DTensor通信Matmul的布局和全局Meta修正的固定双版本本地规则、重分布边界与验收条件。
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

# TorchNPU DTensor通信Matmul的布局和全局Meta修正

固定PyTorch仓主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`与发布快照`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的distributed/tensor/_matrix_ops.py。本文仅说明本地候选和派发实现，不据注册推导全部产品、dtype、shape或通信组合可用；未导入运行上游或设备实验。

## 融合通信没有全部复制的通用回退

all_gather_base_mm只接受gather_index=0。两候选均让x1沿0分片；x2复制时输出和gather_out复制，存在的bias/x2_scale复制、x1_scale沿0；x2沿1分片时输出沿1、gather_out仍复制，bias沿0、x1_scale沿0、x2_scale沿1。gather_output仅是非张量槽，不在此改变第二输出spec。

mm_reduce_scatter_base只接受reduce_op='sum'，仅一条候选：x1沿1、x2沿0、输出沿0；存在的bias和x2_scale沿0，x1_scale沿1。其余comm_turn/output_dtype/comm_mode只是占位，本地没有把任意通信算法或dtype组合逐一验证。

## kwargs与全局shape修正是独立步骤

all-gather kwargs推导只接受输出Replicate或Shard(1)：复制输出下x1_scale仍Shard(0)，其余复制；列分片输出下x2_scale为Shard(1)，其余张量kwargs为Shard(0)。reduce-scatter只接受输出Shard(0)，x1_scale映射1，其余张量kwargs映射0；意外输出placement抛ValueError。两个helper保留原kwargs spec的mesh和tensor_meta，不在此检查通信group与DeviceMesh相同。

handler先传播分片，再修正输出全局Meta第0维：all-gather把两个输出的shape[0]整除args[3]的world_size，reduce-scatter把输出shape[0]乘world_size；world_size==0时原样返回Meta。新TensorMeta保留原stride/dtype，不重新计算stride，也没有在此检查整除余数、负world_size或group实际大小。它原位更新output_spec.tensor_meta，不是另外分配实际输出Tensor。

参与mesh的rank之后才重分布args和相应kwargs、调用op并wrap；非参与rank用公共空结果helper。两种路径都先经过Meta修正，不能因为某rank不执行本地算子就忽略全局spec是否正确。

## 验收重点

固定通信group、实际world_size、x1/x2局部shape和DeviceMesh，检查全局Meta与局部返回相符，覆盖gather_output、有/无bias和scale、列分片及非参与rank。观测实际融合与布局转换通信，不仅比较算子名字；没有在本组承诺通信重叠收益。公共空结果与kwargs规则见[DTensor重分布](torch_npu_dtensor_redistribution_and_registration.md)。
