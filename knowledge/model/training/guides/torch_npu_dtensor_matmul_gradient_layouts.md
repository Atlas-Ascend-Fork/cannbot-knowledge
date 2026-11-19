---
type: Guide
title: TorchNPU DTensor Matmul前反向候选与Partial梯度
description: TorchNPU DTensor Matmul前反向候选与Partial梯度的固定双版本本地规则、重分布边界与验收条件。
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

# TorchNPU DTensor Matmul前反向候选与Partial梯度

固定PyTorch仓主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`与发布快照`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的distributed/tensor/_matrix_ops.py。本文仅说明本地候选和派发实现，不据注册推导全部产品、dtype、shape或通信组合可用；未导入运行上游或设备实验。

## 注册开关与通用前向

只有环境变量TORCH_NPU_USE_COMPATIBLE_IMPL不等于字符串"1"时，才在本文件定义并装饰aten.matmul与matmul_backward自定义策略；这是导入时分支，不是每次调用都动态切换。主线另将npu_bmmV2交给兼容_mm_like_strategy("bmk,bkn->bmn", mesh, schema)，发布本文件没有此本地注册；不据路径差异推断全部软件栈缺失。

matmul总给复制候选。向量点积仅保留复制；左向量乘高维矩阵时可分片右侧batch维或末列维，也可把左右收缩维同时分片使结果Partial。右向量时可分片左侧非收缩维，或让左右收缩维分片得到Partial。各候选按相关shape维对各自mesh.size(0)的整除筛选，不是在此遍历全部mesh维或核对两mesh相同。

两边rank至少2时先用torch.broadcast_shapes计算batch广播输出shape；按尾部对齐的共同batch维、较长一侧独有的batch维、左矩阵行维、右矩阵列维产生Shard候选。收缩维成对分片产生Partial。共同batch分支检查两边整除，独有batch与行/列分支只分片对应侧；不是把所有广播维都当相同索引。局部整除与broadcast_shapes不代替完整算子dtype/stride/设备条件。

## 反向输出的Partial应跟随消费端归约

向量点积反向只给复制。左rank>=2且右为向量/矩阵时：收缩维分片可使两个梯度沿对应收缩维；左侧非收缩维分片会使右梯度Partial，右侧矩阵末列分片会使左梯度Partial。

右rank>=2且左为向量/矩阵的对称分支保留局部维度表达，不可简单照抄前一分支：左向量/右二维的特殊分支给第一个输出Shard(tensor1_dim)，而该输入分片仍是Shard(tensor1_dim-1)；右侧batch候选的一条输入placement列表只列grad、左、右三槽，没有其它分支的mask None槽。本文记录静态结构，不把这些差异补写成已通过的向量梯度或注册合法性保证。

高维乘高维反向按grad末列、末行、收缩维和广播batch维生成组合：某一侧承受另一侧分片的归约时对应梯度为Partial；共同batch维两梯度均Shard，较长一侧独有batch维导致较短侧梯度Partial。收缩候选输出索引实际使用grad_dim-1和grad_dim-2，不在这里按全部广播后的原始输入rank重写。

mask形参未用于按需删减候选输出。比较完整前反向、广播/向量特例、实际placement与归约通信，不以“存在候选”视为全部索引和梯度已校验。[损失Partial消费](torch_npu_dtensor_loss_and_repeat_layouts.md)和[分组矩阵策略](torch_npu_dtensor_grouped_matmul_list_strategy.md)需各自核对。
