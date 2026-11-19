---
type: API
title: all_to_all_vc：全局计数矩阵与非原地变长通信
description: 按组内 rank 解释发送行和接收列，检查元素数、连续布局及异步输出寿命。
tags:
- task.lookup
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/distributed/torch_npu-distributed-all_to_all_vc.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/distributed_c10d.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/__init__.py
  role: header
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/distributed/torch_npu-distributed-all_to_all_vc.md
  role: constraint
created_at: '2026-11-09T03:49:48Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# all_to_all_vc：全局计数矩阵与非原地变长通信

## 版本与范围

依据 OpPlugin 固定主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的该接口产品页，以及 TorchNPU 固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 Python 包装层。本卡按主线页确认A2/A3及950PR&950DT，发布文档没有对应条目；两仓主线没有自动配套证明，不推定发布版已具有相同实现或底层绑定。


## 接口与矩阵

```text
torch_npu.distributed.all_to_all_vc(output, input, send_count_matrix,
    group=None, async_op=False)
```

每个 rank 都传同一份完整 [group_size,group_size] 矩阵；M[i][j] 为组内 rank i 发给 j 的元素个数。input.numel() 等于本 rank 对应行和，output.numel() 等于对应列和；发送按目标 rank 连续排布，接收按来源 rank 连续排布。计数是元素数，不是字节或任意 batch 维大小。

例如 M=[[1,3],[2,1]]，rank0 发4收3，rank1 发3收4。子组的矩阵维度与索引按该组，而不是全部进程的 global rank。

## 输入及返回限制

input/output 必须是 NPU 连续 Tensor，dtype 一致，发送和接收首地址不能相同，不支持原地通信。矩阵须方阵且非负；Python 先检查行/列数量，再将各值 int(...) 化并按行展开，非负性与总元素数等还依赖后端。应主动传整数计数，不把自动转换当成允许小数截断的协议。

async_op=True 返回 Work，False 等待并返回 None；实际数据写入 output。非组成员或非 NPU 的包装层路径可直接告警返回 None，成功与否须结合日志和输出判断。

文档未像 uneven Gather/Scatter 那样声明仅单机，但也没有给出任意集群拓扑的保证；本卡不由“未限制”推导所有多机配套均已验证。


## 验证边界

核对实际包中的公开入口、NPU 后端方法和软件配套；分别验证数据、返回值、组成员、调用顺序及同步语义。本文没有执行上游代码或通信实验，Python 符号存在不等于实际 HCCL 后端已提供对应能力。

- [分布式故障分阶段诊断](../../guides/torch_npu_collective_failure_triage.md)
- [软件栈来源身份](../../../inference/concepts/frameworks/ascend_software_stack_baselines.md)

## 主线双语的950范围和矩阵校验

该接口在此次固定发布文档中没有对应页面，主线中英文明确A2训练/800I A2推理服务器、A3系列及950PR&950DT。metadata新增950仅对应这一主线条目，其他HCCL接口未因此全部获得950PR范围。

所有rank必须传同一完整方阵；本rank发送行和/接收列和分别等于input/output.numel。行数与group size不符、非方阵、负数及总元素数不符有独立错误，不能只检查本rank的一行来替代全矩阵一致性。原型统一标Work，但返回说明明确True为Work、False等待后None，数据写output。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/distributed/torch_npu-distributed-all_to_all_vc.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/distributed_c10d.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/__init__.py)（header）

- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/distributed/torch_npu-distributed-all_to_all_vc.md)（constraint）
