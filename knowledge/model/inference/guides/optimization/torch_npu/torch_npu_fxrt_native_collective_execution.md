---
type: Guide
title: FXRT原生集合通信：连续性、组句柄与状态传播
description: 连接FXRT AllReduce和AllGather的推形、通信组缓存与HCCL调用，区分输入连续性、输出容量及返回状态和设备完成。
tags:
- task.optimization
- topic.parallelism
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/hccl/hccl_all_reduce.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/hccl/hccl_all_gather.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_all_reduce.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_all_gather.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/hccl/hcom_utils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/hccl/hcom_utils.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/hccl/hccl_adapter.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/collective/collective_manager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/collective/communication_group.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/hccl/hccl_all_to_all.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/hccl/hccl_all_to_all.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/hccl/hccl_reduce_scatter.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/hccl/hccl_reduce_scatter.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/hccl/tensor_copy.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/hccl/tensor_copy.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/hccl/wait_tensor.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/hccl/wait_tensor.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/hccl/hccl_kernel.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/hccl/hccl_kernel.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/hccl/hccl_plugin.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/hccl/hccl_adapter.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_all_to_all.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_all_to_all.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_reduce_scatter.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_reduce_scatter.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_all_reduce.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_all_gather.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/collective/collective_manager.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/collective/communication_group.h
  role: implementation
created_at: '2026-11-10T14:59:48Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---


# FXRT原生集合通信：连续性、组句柄与状态传播

## 固定版本与范围

仅静态审阅 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 FXRT 原生 AllReduce/AllGather 调用链。未知产品和配套，保持 `draft`、空平台；发布快照不在本卡证据范围。未加载通信库、导入上游或运行设备/分布式实验。

前端如何从 FX 图发现 ProcessGroup、如何适配 vLLM 的 dim=0 all_gather，见[前端降级](torch_npu_fxrt_frontend_lowering.md)。本卡补实际原生消费者，不将前端映射表或同名 TorchNPU Work 合同替代此实现。

## 连续性检查发生在执行准备阶段

`HcclAllReduce::CalcWorkspace` 和 `HcclAllGather::CalcWorkspace` 都先调用 `InitHccl`，再调用 `CheckHcclInputContiguous`；后者检查 FXRT Tensor 的 `IsContiguous()`，不满足时走异常日志路径，没有在这里自动插入连续化拷贝。随后从输入的 shape/dtype 计算通信 count/type，并按第三个输入的 groupName 取通信器。

因此 view 的布局问题不能只用“FX 前端能转换”来排除。若业务需要显式连续化，应分别统计准备拷贝和通信本体，并按实际 Tensor 布局核对该检查；本卡没有展开 `IsContiguous` 的全部格式语义。

两个 CalcWorkspace 函数虽然接收 workspaceSize 指针，却未在这两个函数体给它赋值；Launch 也不消费传入 workspace/workspaceSize。这里只描述局部接口，不据此断言外层状态未初始化，或底层 HCCL 没有内存开销。

## 推形数量与通信组必须一致

|原生算子|推形与实际调用|
|---|---|
|AllReduce|输出复制输入 shape/dtype 后 Resize；Init 通过字符串表取归约类型，表中列 min/max/prod/sum。Launch 将输入、输出地址、准备好的 count/type、归约类型和传入 stream 交适配器。|
|AllGather|输出先复制输入 shape，再将 shape[0] 乘第二个输入 rankSize，并复制 dtype 后 Resize；Launch 的 count/type 仍来自本地输入，实际通信器来自 groupName。|

AllGather 的所读 InferShape 没有在本函数先检查 rank 非零，也没有在本地将 rankSize 与 manager 中的实际 group_size 比较。需要核对正整数 rankSize、输入首维和真实通信组规模；这是一项采用前提，尚未做不匹配或标量输入复现。

`GetHcclCountAndTypeFromTensor` 在这两条路径以单输入计算 count；不要把 `GetHcomCount` 中多输入的对齐规则自动套到这里。dtype 映射中 Bool 对应 HCCL INT8；部分低精度条目受 `EXPERIMENT_A5` 编译宏控制，该宏名不是 Ascend950系列（包含旧称Atlas A5）的整卡产品支持证明，也不保证实际构建已启用。

## 同名通信组缓存不是自动刷新

Python `_set_communication_info_for_group` 从 Torch ProcessGroup 取 rank 列表、group rank 和 HCCL handle，转交 `create_communication_group`。管理器以 groupName 保存 CommunicationGroup，已有同名项时返回 false，不替换；普通 `_extract_and_setup_comm_groups` 也在名字已存在时提前返回。

CommunicationGroup 保存 rank 信息和整数通信器句柄；`LoadHcclLibrary` 这个名字在所读 helper 中只做组查找与句柄转换，不在这里新建通信器。模型重编译、换 ProcessGroup 或复用同名组时，不能仅凭再次执行前端就认为旧句柄已刷新；通信组及外部句柄生命周期需保持一致并验证。本卡没有认证跨线程修改、组销毁重建或任意拓扑。

## 返回成功不等于通信完成

两条原生 Launch 在适配器正常返回非 `HCCL_SUCCESS` 时记录 ERROR 日志，之后仍返回 FXRT `SUCCESS`。这不抹去可能更早抛出的异常，也不证明该错误已在全链路被恢复；调用方不能只检查这层返回值就认定结果有效。

适配器的 AllGather 包装先检查函数符号和通信器/输入/输出指针，空符号通过 `CHECK_SYMBOL_NULL` 返回 `HCCL_E_RESERVED`；所读 AllReduce 包装没有相同的局部前置检查，直接调用存储的函数指针。差异不等于已复现空指针失败，也不能从库初始化步骤推定所有错误都安全返回。

两条包装都把调用者的 stream 传给 HCCL。本段没有创建 Torch Work 或在返回处执行设备同步；不能将这里的返回当作设备通信完成、任意跨流依赖满足或与 ProcessGroup Work.wait 完全等价。捕获与执行模式的其他限制见[FXRT运行时](torch_npu_fxrt_runtime.md)。

## 采用前验证

固定软件栈、构建宏、真实 ProcessGroup 和布局，检查前端是否选择这两条原生路径；分别核对 groupName/handle、rankSize、count/type、归约字符串和输出容量。用实际多 rank 输入比较结果，区分主机返回、错误日志和设备完成信号，再评估连续化与通信重叠收益。上述是待执行的验收建议，本次没有通信正确性、故障恢复、性能或 verified 记录。

## 增补：其余HCCL族算子与头文件边界

同一主线提交下补齐hccl目录其余实现（P2对账批次，静态阅读，未运行）。`all_to_all`先按groupName取rankSize（为0报INVALID_PARAM），InitHccl并检查输入连续；`IsAllToAllV`比较send/recv Numel列表是否有不等都项，有则走`HcclAlltoAllV`变长路径（按strideOfDim0累计sendCounts/sdispls/recvCounts/rdispls），否则等长`HcclAlltoAll`（count取输入count/rankSize）。**变长判定只看Numel列表，不看dtype/shape对齐**；all_to_all_v参数组装发生在Launch内，失败返回LAUNCH_OP_FAILED。

`reduce_scatter`与op_base的`OpAllToAll`/`OpReduceScatter`为对应基类推形/转发。`tensor_copy`（注册名`copy`）的输出取input[0]，Launch把src到dst按Numel×itemsize做`AscendResManager::MemcpyDeviceToDevice`（aclrtMemcpyAsync），失败仅ERROR日志仍返回SUCCESS——与本卡AllReduce/AllGather的返回边界一致。`wait_tensor`是no-op：InferShape复制输入shape，`NeedLaunch()`为false，Launch直接SUCCESS；**它的语义是图序占位，不提供任何设备同步**。`hccl_kernel.cpp`只是HcclKernel构造器（count/rootId/comm成员初始化）。`hccl_plugin.h`用ORIGIN_METHOD声明Broadcast/AllReduce/Reduce/Scatter/ReduceScatter/AllGather/Send/Recv/AlltoAllV等HCCL符号表；`hccl_adapter.h`定义AllToAllV/AllGatherV/ReduceScatterV参数结构、HcclMode（kGraph/kPynative/kKernelByKernel）与单例适配器接口，是本卡既有adapter.cpp描述的声明面。op_base四个.h与collective两个.h为对应类声明，无独立执行语义。这些补充沿用本卡"返回成功不等于通信完成"与同名组缓存边界，不新增verified。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/hccl/hccl_all_reduce.cpp)（primary）：1–64。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/hccl/hccl_all_gather.cpp)（implementation）：1–55。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_all_reduce.cpp)（implementation）：1–23。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_all_gather.cpp)（implementation）：1–26。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/hccl/hcom_utils.cpp)（implementation）：1–145,155–161。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/hccl/hcom_utils.h)（implementation）：1–127。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/hccl/hccl_adapter.cpp)（implementation）：9–15,177–188,230–243。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/collective/collective_manager.cpp)（implementation）：1–37。
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/hardware/hardware_abstract/collective/communication_group.cpp)（implementation）：1–30。
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/utils.py)（implementation）：32–72。
