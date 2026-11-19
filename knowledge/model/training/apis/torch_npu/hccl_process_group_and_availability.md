---
type: API
title: HCCL Python入口：ProcessGroup构造与后端可用性
description: 区分直接构造ProcessGroupHCCL、后端可用探测和通信已初始化，保留超时参数文档边界。
tags:
- task.lookup
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/distributed/（beta）torch-distributed-ProcessGroupHCCL.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/distributed/（beta）torch-distributed-ProcessGroupHCCL.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/distributed/(beta)torch-distributed-ProcessGroupHCCL.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/distributed/（beta）torch-distributed-is_hccl_available.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/distributed/（beta）torch-distributed-is_hccl_available.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/distributed/(beta)torch-distributed-is_hccl_available.md
  role: constraint
created_at: '2026-11-09T19:09:59Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# HCCL Python入口：ProcessGroup构造与后端可用性

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5的中文页及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda的中英文页。A2/A3在本卡指训练系列，主线新增950DT确认不回推到发布版，不扩到950PR。旧Atlas产品只保留来源条目，不自动映射其他新型号。

发布配对PyTorch提交为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；补充独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf时单独指出，两个main不构成自动配套。以下为静态合同，没有编译、导入、加载模型、设备运行或性能测量。


## 两个入口

```text
torch.distributed.ProcessGroupHCCL(store, rank, size, timeout) -> ProcessGroup
torch.distributed.is_hccl_available() -> bool
```

文档的store是`torch.distributed.distributed_c10d.PrefixStore`对象，rank描述当前参与者的rank，size为参与通信的总数；不能把“节点”措辞当每机器只允许一个rank的保证。timeout描述超时判断，参数表写默认1800秒，但简写原型没有默认实参或完整Python类型，不据此生成任意版本都可省略timeout的调用。

两页发布版列A2/A3训练和旧Atlas训练/推理，主线另列950DT。Python入口的950确认不扩大[C++ ProcessGroupHCCL页](cpp_processgroup_hccl.md)的独立产品表，也不自动确认所有通信成员。

## 可用、初始化和健康分开

is_hccl_available返回后端可用性布尔值，示例True只是文档示例，未在本卡执行。后端可注册、ProcessGroup对象已创建、HCCL已分配资源与实际多rank通信成功是不同条件；不能把该探针当训练链路健康检查。

[get_hccl_comm_name](get_hccl_comm_name.md)还可能因init_comm=True触发资源申请；[reinit_process_group](reinit_process_group.md)的重建/恢复分支也不能由这两个入口代替。设备映射、各rank参数、调用顺序与超时行为需按真实包和任务核验。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/distributed/（beta）torch-distributed-ProcessGroupHCCL.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/distributed/（beta）torch-distributed-ProcessGroupHCCL.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/distributed/(beta)torch-distributed-ProcessGroupHCCL.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/distributed/（beta）torch-distributed-is_hccl_available.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/distributed/（beta）torch-distributed-is_hccl_available.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/distributed/(beta)torch-distributed-is_hccl_available.md)（constraint）
