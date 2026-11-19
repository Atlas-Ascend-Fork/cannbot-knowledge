---
type: Guide
title: TorchNPU 私有 DistributedMuon：三路正交化与分布式边界
description: 依据主线完整本地模块梳理 BF16 Newton–Schulz、Shard 分派、通信、动量和学习率缩放，保留进程组与 DTensor 适用条件。
tags:
- task.optimization
- topic.optimizer
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/distributed_muon.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/__init__.py
  role: implementation
created_at: '2026-11-11T03:26:02Z'
updated_at: '2026-11-11T03:26:02Z'
platforms: []
---

# TorchNPU 私有 DistributedMuon：三路正交化与分布式边界

## 固定主线与私有入口

依据 PyTorch `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 完整 `torch_npu/optim/distributed_muon.py`。主线门面显式导入 `_DistributedMuon`，但门面 `__all__` 未列入该名，模块自身 `__all__=[]`。发布 `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 的相同路径不存在，门面也无该导入；此结论只针对固定文件和门面，不推导发布版本不存在其他 Muon 实现。它不继承 NpuFusedOptimizerBase，其 dtype/状态/分布式行为应单独核对，不能套用 [融合优化器生命周期](torch_npu_fused_optimizer_lifecycle.md)。无独立产品确认与设备实验，保持 draft/空平台。

## 构造、状态与闭包

真实构造默认 lr=1e-3、weight_decay=0.1、momentum=0.95、nesterov=True，NS 系数 `(3.4445,-4.775,2.0315)`、ns_steps=5、eps=1e-7、adjust_lr_fn=None、process_group=None。Tensor lr 要求 numel=1；lr、momentum、weight_decay 非负，adjust_lr_fn 只接受 None、original、match_rms_adamw。先初始化 Optimizer，再检查所有参数 ndim=2。未在构造中完整检查 NS 步数、系数与 eps，部分错误到执行 helper 才触发。

`_init_group` 每步跳过 grad=None，拒绝复杂参数与稀疏梯度；若梯度是 DTensor 且参数任一 placement 为 Shard，将梯度转 local tensor。无 momentum_buffer 则 zeros_like(实际梯度,preserve_format)；已有 DTensor buffer 且参数分片时也转 local。返回的 has_complex=False；核心函数仍保留 has_complex=True 的拒绝分支。step 为 no_grad，closure 在 enable_grad 中先执行，再每组重新构建有梯度参数列表、准备动量与调用核心。

核心先 `_to_scalar`：Tensor lr 调 `.item()`，普通 lr 原样保留。逐参数再次要求梯度二维，随后 `buf.lerp_(grad,1-momentum)`；Nesterov 的 update=`grad.lerp(buf,momentum)`，否则用 buf。之后才进入 NS helper 的检查，因此后者拒绝输入前动量可能已被修改。checkpoint/异常恢复需要检查状态，而不能假设失败 step 完全无副作用。

## Newton–Schulz 本地与列分片公式

两个正交化 helper 均检查二维梯度、系数长度 3、ns_steps<100；本地没有要求 ns_steps>0 或 eps>0。默认本地 `_newtonschulz_orthogonalize` 先转 BF16，行数>列数时转置，原地除以 `norm().clamp(min=eps)`；每轮令 G=X@X.T，U=bG+cG²，再 X=aX+U@X，最后按需转置返回。BF16 输入的 `.bfloat16()` 不提供始终新分配的保证，不能把局部归一化描述成必然不改输入别名。

列分片 `_distributed_zeropower_via_newtonschulz` 也转 BF16：本地范数平方以 SUM AllReduce 汇总再开方归一化，每轮计算本地 `X_i@X_i.T` 并 SUM AllReduce，基于汇总 Gram 做同一多项式。该 helper 没有本地 tall-matrix 转置步骤，Gram 维度沿本地行轴。默认五轮需要 1 次范数 + 5 次 Gram AllReduce；ns_steps 非负时为 1+ns_steps 次。这条分支不 full_tensor，不代表任意 placements 都满足所需矩阵分解或数值等价条件。

## 三路分派及通信前提

辅助 `_is_dtensor_shard` 检查任一 Shard placement，`_is_dtensor_shard1` 检查任一 dim=1 的 Shard，`_get_shard_dim` 返回第一个 Shard 的维度，否则 0。它们没有验证只有一个 Shard 或进程组与 mesh 一致。

| 条件 | 本地执行与通信 |
| --- | --- |
| process_group 非 None，参数含 Shard(1) | 使用上述分布式 Gram helper，把 local 结果按原 mesh/placements 包回 DTensor |
| process_group 非 None，含 Shard 但无 dim=1 的 Shard | 当前有梯度参数列表索引 i 的 owner=`i % world_size`；所有 rank 先 `DTensor.from_local(...).full_tensor()`，owner 做本地 NS，其余 rank 分配全形 BF16 空 tensor；广播 BF16 结果后，按第一个 Shard 维度 chunk(world_size)，取 group rank 的 chunk，转回原完整梯度 dtype 并 contiguous，再包回 DTensor |
| 其他条件 | 调用普通本地 NS |

第二条的代码注释称 Shard(0)，实际分支是“任意 Shard 且没有 Shard(1)”；不能将注释当作多维 mesh/其他分片维度已验收。owner 按**当前组内有 grad 参数顺序**轮转，各 rank 的参与顺序和 grad=None 分布必须匹配 collective 次序。`get_rank/get_world_size(process_group)` 得到的组内 owner 整数直接作为 `broadcast(...,src=owner_rank,group=process_group)` 入参；局部代码未提供非默认子组的 rank 映射证明。部署前必须核对 Torch distributed 的 src 约定、mesh 与 process_group 成员/大小、chunk 均匀性及全部 rank 的调用顺序。

`_init_group` 的 sharded DTensor 梯度解包不以 process_group 非 None 为条件；因此 process_group=None 但参数分片时，也可能先得到 local update 再进入普通 NS。随后与 DTensor 参数相加的行为取决于 DTensor 运算规则，不能仅凭注释“与上游相同”认定等价于完整矩阵 Muon。源码没有证明任意子组、多维 mesh 或不均匀分片都可直接使用。

## 学习率与参数更新

`_adjust_lr` 使用参数**全局 shape** 的前两维 A、B。None 与 original 都返回 `lr*sqrt(max(1,A/B))`；match_rms_adamw 返回 `lr*0.2*sqrt(max(A,B))`。helper 对其他字符串有不缩放回落，但正常构造会拒绝这些字符串。参数最后先乘 `1-lr*weight_decay`，再加 `-adjusted_lr*update`：衰减用原始标量 lr，正交更新用调整后 lr，二者不能统一替换。

## 验收与依赖边界

应比较非分片、列分片、其他分片三条路线及 nesterov 开关；检查高宽矩阵、BF16 别名、NS 参数错误时动量状态、恢复、多组/缺梯度顺序、子组 rank 映射、mesh/进程组一致性和通信 dtype。这里记录完整本地定义和分派，未执行上游导入、NPU/分布式、收敛或性能实验。注释中的带宽与逐位等价主张不是实测结果；ATen BF16、DTensor collective、HCCL/ProcessGroup、底层设备内核及论文性质需各自独立证据。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/distributed_muon.py)（primary），完整本地模块 1–524 行。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/optim/__init__.py)（implementation），完整本地模块 1–17 行。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/optim/__init__.py)（implementation），完整本地模块 1–16 行。
