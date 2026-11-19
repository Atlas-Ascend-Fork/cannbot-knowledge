---
type: API
title: reduce_scatter_tensor_uneven：单机分割归约与输出缓冲区
description: 限定输入第零维分割及单机范围，记录 PRODUCT 限制、异步句柄与同步返回差异。
tags:
- task.lookup
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/distributed/torch_npu-distributed-reduce_scatter_tensor_uneven.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/distributed_c10d.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/__init__.py
  role: header
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/communication_graph.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/distributed/torch_npu-distributed-reduce_scatter_tensor_uneven.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/distributed/torch_npu-distributed-reduce_scatter_tensor_uneven.md
  role: constraint
created_at: '2026-11-09T03:49:48Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- '950'
---

# reduce_scatter_tensor_uneven：单机分割归约与输出缓冲区

## 版本与范围

依据 OpPlugin 固定主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的该接口产品页，以及 TorchNPU 固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 Python 包装层。本卡范围为 A2/950，不扩大到产品页未列出的产品；两仓主线没有自动配套证明，不推定发布版已具有相同实现或底层绑定。


## 接口

```text
torch_npu.distributed.reduce_scatter_tensor_uneven(output, input,
    input_split_sizes=None, op=dist.ReduceOp.SUM, group=None, async_op=False)
```

归约并按组内 rank 切分到 output；input 的大小对应各 rank 输出拼接。input_split_sizes 的长度等于 group size，总和等于 input.shape[0]，每个 rank 的 output 应匹配其分片；默认 SUM，文档限定单机。

独立产品页列 A2/950DT 与 Atlas 推理产品，没有列 A3。本卡仅取 A2/950；不能用通用入图支持清单替代这一产品证据。固定 TorchAir 通信页还明确该 uneven 接口不支持 PRODUCT，本卡不提供 PRODUCT 配方，也不据此推定其他未核对归约项均可用。

## 返回与调用前提

文档的工作句柄描述没有区分同步分支；固定 Python 包装层 async_op=True 返回 Work，False 执行 wait() 后返回 None。真实数据写入 output；非成员或非 NPU 输入还可能告警后直接返回 None。

使用子组时，分割长度和 rank 顺序按实际 group 解释，保持所有参与者调用一致。异步读写、缓冲区复用和生命周期须等候完成；不把该 API 的“零拷贝”描述当作所有布局、拓扑和存储组合的保证。


## 验证边界

核对实际包中的公开入口、NPU 后端方法和软件配套；分别验证数据、返回值、组成员、调用顺序及同步语义。本文没有执行上游代码或通信实验，Python 符号存在不等于实际 HCCL 后端已提供对应能力。

- [分布式故障分阶段诊断](../../guides/torch_npu_collective_failure_triage.md)
- [软件栈来源身份](../../../inference/concepts/frameworks/ascend_software_stack_baselines.md)

## 中英文与发布页的独立约束

发布中文只列A2训练/800I A2推理及旧Atlas推理，主线中英文新增950DT，均未列A3；不能把主线950支持或其他通用分布式接口的A3支持回灌到发布组合。本卡a2/950范围继续按主线独立确认。

三页均保留单机、第零维split数量等于group size及split和等于对应总维度的条件。示例固定两本地进程，按LOCAL_RANK取长度2和3输入/输出，不是多机global rank映射配方。“零拷贝”是功能描述，不能承诺任意拓扑/布局无需额外转换；文档Work标注未细分同步分支，仍按本卡已核对包装层区分None与Work。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/distributed/torch_npu-distributed-reduce_scatter_tensor_uneven.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/distributed_c10d.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/__init__.py)（header）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/communication_graph.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/distributed/torch_npu-distributed-reduce_scatter_tensor_uneven.md)（constraint）

- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/distributed/torch_npu-distributed-reduce_scatter_tensor_uneven.md)（constraint）
