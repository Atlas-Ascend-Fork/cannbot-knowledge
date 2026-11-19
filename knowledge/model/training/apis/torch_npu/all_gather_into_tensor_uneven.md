---
type: API
title: all_gather_into_tensor_uneven：单机非等长收集与同步返回
description: 记录第零维分割、组大小和原地输出，区分文档返回标注与实际同步 None。
tags:
- task.lookup
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/distributed/（beta）torch_npu-distributed-all_gather_into_tensor_uneven.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/distributed_c10d.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/__init__.py
  role: header
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/distributed/（beta）torch_npu-distributed-all_gather_into_tensor_uneven.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/distributed/(beta)torch_npu-distributed-all_gather_into_tensor_uneven.md
  role: constraint
created_at: '2026-11-09T03:49:48Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- '950'
---

# all_gather_into_tensor_uneven：单机非等长收集与同步返回

## 版本与范围

依据 OpPlugin 固定主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的该接口产品页，以及 TorchNPU 固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 Python 包装层。本卡范围为 A2/950，不扩大到产品页未列出的产品；两仓主线没有自动配套证明，不推定发布版已具有相同实现或底层绑定。


## 接口与数据

```text
torch_npu.distributed.all_gather_into_tensor_uneven(output, input,
    output_split_sizes=None, group=None, async_op=False)
```

output 是预先提供的输出 Tensor，结果为组内 input 的拼接；output_split_sizes 按第零维切分，长度必须等于 group size，总和必须等于 output.shape[0]。它不是每个块的字节数，也不能直接用全局 WORLD 的长度替代子组大小。文档限定单机。

产品页列 A2、950DT 和 Atlas 推理产品，没有列 A3；本卡仅取 A2/950。未列出不等于证明底层绝对不支持，不能由通用 GE 入图清单补出产品支持。

## 返回值和跳过路径

文档原型标注 Work、返回说明描述输出 shape；固定 Python 实现却在 async_op=False 时调用 work.wait() 后返回 None，True 才返回 Work。结果写入 output，不是把返回值当 Tensor。

非 group 成员、input/output 非 NPU 的包装层路径会告警并返回 None；因此 None 也可能表示未执行，不能仅凭返回值确认成功。group=None/WORLD 选择默认组，None 的 split 转为空列表交后端处理；若需非等长，显式给出满足约束的分割，不根据空列表猜测动态推导规则。

异步使用时保留 input、output 及相关存储，等待真实完成后再读取或复用；返回 Work 本身不是结果已经可用的证明。


## 验证边界

核对实际包中的公开入口、NPU 后端方法和软件配套；分别验证数据、返回值、组成员、调用顺序及同步语义。本文没有执行上游代码或通信实验，Python 符号存在不等于实际 HCCL 后端已提供对应能力。

- [分布式故障分阶段诊断](../../guides/torch_npu_collective_failure_triage.md)
- [软件栈来源身份](../../../inference/concepts/frameworks/ascend_software_stack_baselines.md)

## 中英文与发布页的独立约束

发布中文只列A2训练/800I A2推理及旧Atlas推理，主线中英文新增950DT，均未列A3；不能把主线950支持或其他通用分布式接口的A3支持回灌到发布组合。本卡a2/950范围继续按主线独立确认。

三页均保留单机、第零维split数量等于group size及split和等于对应总维度的条件。示例固定两本地进程，按LOCAL_RANK取长度2和3输入/输出，不是多机global rank映射配方。“零拷贝”是功能描述，不能承诺任意拓扑/布局无需额外转换；文档Work标注未细分同步分支，仍按本卡已核对包装层区分None与Work。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/distributed/（beta）torch_npu-distributed-all_gather_into_tensor_uneven.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/distributed_c10d.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/__init__.py)（header）

- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/distributed/（beta）torch_npu-distributed-all_gather_into_tensor_uneven.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/distributed/(beta)torch_npu-distributed-all_gather_into_tensor_uneven.md)（constraint）
