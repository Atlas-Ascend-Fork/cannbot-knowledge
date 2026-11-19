---
type: API
title: reinit_process_group：重建分支、恢复范围与返回差异
description: 区分接口文档与固定 Python 实现，避免把通信域处理当成完整训练状态恢复。
tags:
- task.lookup
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/distributed/（beta）torch_npu-distributed-reinit_process_group.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/distributed_c10d.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/__init__.py
  role: header
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/distributed/（beta）torch_npu-distributed-reinit_process_group.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/distributed/(beta)torch_npu-distributed-reinit_process_group.md
  role: constraint
created_at: '2026-11-09T03:49:48Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# reinit_process_group：重建分支、恢复范围与返回差异

## 版本与范围

依据 OpPlugin 固定主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的该接口产品页，以及 TorchNPU 固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 Python 包装层。本卡按固定主线产品表补充A2/A3训练和950DT，发布范围另列；两仓主线没有自动配套证明，不推定发布版已具有相同实现或底层绑定。


## 文档契约

```text
torch_npu.distributed.reinit_process_group(group=None, rebuild_link=True)
```

必须已经 init_process_group；文档说 True 销毁并重建 HCCL 链路，False 继续用原链接，返回 None。group=None 指向默认组。产品表不替代具体软件组合及真实链路完成验证。

## 固定实现的实际分支

所查 Python 包装层首先读取 current_device：

- rebuild_link=True：对所选 HCCL 组调用 _delete_tcpstore_key()、abort_hccl_comm("reinit")，随后返回 group 对象，和文档 None 标注不同。Python 函数里没有直接创建新 ProcessGroup 的步骤，不能仅据函数返回就宣称实际通信链路已经重建完成。
- rebuild_link=False：遍历已登记且有 NPU 后端的进程组，分别调用 resume_hccl_comm(device_id)，返回 None；处理范围不只传入的 group。不要用它声称只恢复某一个子组。

这里仅核对 Python 包装层，底层 abort/resume 的完整状态机及何时完成真实建链未在本卡生产。部署必须核对自己的版本，不用两仓不同固定主线的差异静默改写发布 API。

## 恢复边界

所有相关 rank 的故障状态、未完成 Work、通信顺序与设备绑定应先明确。该接口不自动恢复模型、优化器、数据位置或 checkpoint，也不能证明失联进程已恢复。验证时分别检查返回分支、实际域状态和随后受控通信能否推进，避免直接继续未完成的训练更新。


## 验证边界

核对实际包中的公开入口、NPU 后端方法和软件配套；分别验证数据、返回值、组成员、调用顺序及同步语义。本文没有执行上游代码或通信实验，Python 符号存在不等于实际 HCCL 后端已提供对应能力。

- [分布式故障分阶段诊断](../../guides/torch_npu_collective_failure_triage.md)
- [软件栈来源身份](../../../inference/concepts/frameworks/ascend_software_stack_baselines.md)

## 固定发布与主线产品、前置条件补充

发布页列A2/A3训练，主线中文和英文新增950DT；本卡新增950仅指后者，不覆盖950PR或证明两个main配套。发布约束泛称有效device，主线改为必须先init_process_group完成集合通信域初始化；不能把本接口作为首次建域入口。

文档仍标None，已有独立PyTorch主线返回/abort/resume差异继续保留；发布示例只在reinit后做all_reduce，没有完整模型、优化器、数据进度或故障恢复验证。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/distributed/（beta）torch_npu-distributed-reinit_process_group.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/distributed_c10d.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/__init__.py)（header）

- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/distributed/（beta）torch_npu-distributed-reinit_process_group.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/distributed/(beta)torch_npu-distributed-reinit_process_group.md)（constraint）
