---
type: API
title: get_hccl_comm_name：惰性初始化、副作用与全局 rank
description: 区分后端注册、ProcessGroup 创建和 HCCL 实际初始化，记录 init_comm=False 的空字符串。
tags:
- task.lookup
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/distributed/torch-distributed-distributed_c10d.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/distributed_c10d.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/__init__.py
  role: header
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/distributed/torch-distributed-distributed_c10d.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/distributed/torch-distributed-distributed_c10d.md
  role: constraint
created_at: '2026-11-09T03:49:48Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# get_hccl_comm_name：惰性初始化、副作用与全局 rank

## 版本与范围

依据 OpPlugin 固定主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的该接口产品页，以及 TorchNPU 固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 Python 包装层。本卡范围为 A2/A3，不扩大到产品页未列出的产品；两仓主线没有自动配套证明，不推定发布版已具有相同实现或底层绑定。


## 入口

```text
pg._get_backend(torch.device("npu")).get_hccl_comm_name(rankid, init_comm=True)
```

这是 ProcessGroup 的 NPU 后端方法，可用于默认组或 new_group 所建子组，不是标准 torch_npu 顶层函数。文档将 PyTorch 2.1 及以上与之前的调用形式分开；不使用版本字符串的字典序比较判断安装版本。

先 init_process_group(backend="hccl")，再确认正确 current device。rankid 文档明确为全局 rank，不能用 LOCAL_RANK 在多节点中替代；也不要与 all_to_all_vc 的组内矩阵索引混淆。

## 名称查询可触发资源申请

init_comm=True 时，尚未初始化的 HCCL 域会进行初始化并返回名字；False 则不初始化，未初始化时返回空字符串。空字符串不必然表示查询失败，也不能将 True 当成无副作用的健康探针。

文档描述默认 Send/Recv buffer 各 200MB，由 HCCL_BUFFSIZE 控制；实际域级选项与安装版本会影响资源配置，不能将查询后内存增长固定为所有场景恰好 400MB。

固定 Python 中 is_hccl_available() 仅检查 hccl 是否已登记在 Backend.backend_list；可注册、ProcessGroup 已创建、HCCL 已完成初始化和通信正常是不同层次。一次名称查询也不证明整个多 rank 任务健康。


## 验证边界

核对实际包中的公开入口、NPU 后端方法和软件配套；分别验证数据、返回值、组成员、调用顺序及同步语义。本文没有执行上游代码或通信实验，Python 符号存在不等于实际 HCCL 后端已提供对应能力。

- [分布式故障分阶段诊断](../../guides/torch_npu_collective_failure_triage.md)
- [软件栈来源身份](../../../inference/concepts/frameworks/ascend_software_stack_baselines.md)

## 发布与英文页补充的参数差异

发布中文、主线中文及英文均保留正确current device、先init_process_group并使用HCCL后端的前提；来源产品表仍未列950。主线原型把发布的`rankid->int`伪标注改为rankid、返回str，不能把旧伪标注当Python可执行语法。

中文参数表把init_comm写int，英文明确bool，默认True、False的行为一致；实际调用使用明确布尔值，不据中文类型标签扩成任意整数协议。默认Send/Recv各200MB是文档默认描述，不等于所有域/所有配置固定增长400MB。示例的`torch.__version__ > '2.0'`不是完整版本解析配方，已有调用形式的2.1分界仍须核对真实版本对象和API。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/distributed/torch-distributed-distributed_c10d.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/distributed_c10d.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/__init__.py)（header）

- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/distributed/torch-distributed-distributed_c10d.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/distributed/torch-distributed-distributed_c10d.md)（constraint）
