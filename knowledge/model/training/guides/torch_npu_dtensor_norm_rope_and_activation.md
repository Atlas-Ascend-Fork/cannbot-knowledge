---
type: Guide
title: TorchNPU DTensor归一化、RoPE和激活分片
description: 说明归一化复制范围、RoPE广播梯度Partial和SwiGLU及gather非操作维分片。
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

# TorchNPU DTensor归一化、RoPE和激活分片

## 固定实现与候选策略

固定PyTorch仓主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`、发布快照`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的_math_ops.py。本组两版18个函数的完整AST相同；register_op_strategy的导入来自不同兼容入口，不据函数相同推定所有外部注册语义一致。这里只描述本地候选、spec与成本构造，没有运行上游或设备实验，不补产品与dtype支持。

## RMS与AddRMS保持归一化范围复制

RMS策略由gamma.shape确定归一化维数，axis=input.ndim-len(normalized_shape)。遍历input的每条策略，对input placements调用_replicate_dims_start_at(..., axis)，gamma调用无axis形式，并通过generate_redistribute_costs计入输入转换成本。前向output_specs直接设为input目标spec；不能由此局部spec构造自行补出完整算子每个返回值的spec或统计shape。

反向同样使grad_out和input使用归一化范围复制后的placement；gamma输入、rstd输入按相同idx的已有spec加入并给出零成本列表。gamma梯度通过outer_dims=range(axis)、_infer_reduce_dims_map和map_placements_after_reduction(..., "sum")构造；外维分片产生的梯度贡献需要按最终布局归约，不能视为任何局部gamma梯度都完整。grad_out目标tensor_meta实际来自input_src_spec，不是另外读取grad_out元数据后做全面校验。

AddRMS以x1布局为锚，x2目标placement跟随x1，gamma按复制目标处理，分别计转换成本；y与残差x输出均复用x1_target_spec。rstd spec的placements实际取x1_target_placements[:axis]，tensor_meta也沿用x1，不是对统计shape重新计算的完整证明。placements数组按mesh维组织，不能把这个切片自动解释为所有mesh都满足“删除归一化张量维”；集成时应单独核对rstd的mesh/shape/placements。

三条策略虽然部分分支检查gamma或x2是否None，但在此前已读取gamma.shape；各输入策略还以同一idx访问，没有本地长度一致与任意缺省输入的完整防御。源码注释“x1/x2应同shape”也不是运行shape检查。优化时记录实际候选与通信，不由成本列表推出已测吞吐提升。

## RoPE广播决定旋转参数梯度是否Partial

npu_rotary_mul及backward先给全部复制候选，再枚举x除最后一维之外的每个维度i；最后D维不加入分片候选。如果r1.shape[i]==1，x/grad沿Shard(i)，r1/r2保持复制，反向dr1/dr2声明Partial；否则r1/r2和输出及其梯度均随Shard(i)。rotary_mode只作为非张量None槽，不在策略中分支验证。

源码依赖r1/r2同形和与x布局对应的假设，只读取r1.shape[i]，没有逐项验证r2或广播合法性。广播分支的参数梯度是局部贡献，应观察后续归约，不能把全部输出统一当作已经完整的Shard梯度。

## SwiGLU与gather反向避开被操作维

SwiGLU先normalize_dim，再枚举除切分dim之外各维的Shard；反向令grad和x同Shard，输出placement列表实际为[Shard(i), None]，复制分支同样是[Replicate(), None]。这是本地注册返回结构，不能由额外None槽创造一个有数据的梯度输出。

gather反向先把dim按input_shape rank规范化。只有input_shape、index和grad rank相同，才对非gather维d且三者该维尺寸相等加入grad/index均Shard(d)、输出Shard(d)的候选；其余只保留复制。不据这一局部规则推导gather维分片、任意稀疏梯度或索引范围合法。

验收覆盖归一化外维与内维布局、gamma梯度归约、RoPE广播与参数梯度、负dim和不同rank，并比较前向/梯度与真实重分布开销。接口名单见[原生TP约束](torch_npu_native_tensor_parallel_constraints.md)，Partial与公共处理见[DTensor重分布](torch_npu_dtensor_redistribution_and_registration.md)。
