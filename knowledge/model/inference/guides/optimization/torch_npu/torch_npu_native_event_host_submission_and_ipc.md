---
type: Guide
title: TorchNPU原生Event的Host提交、IPC与外部流
description: 区分record出队与设备完成，解释query、block、同步计时、IPC句柄和外部流门控的实际消费者，并给出 Python 构造面与
  from_ipc_handle/elapsed_time 绑定契约。
tags:
- task.optimization
- topic.memory
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUEvent.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUEvent.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUEventManager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUEvent.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUEvent.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUEventManager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUStreamUtils.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUStream.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUEventManager.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUEventManager.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Event.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/npu/Event.cpp
  role: implementation
created_at: '2026-11-11T03:50:38Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU原生Event的Host提交、IPC与外部流

固定PyTorch主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf与发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b。本卡完整读取两版Event/头文件及事件管理器，并定向核对主线外部流检查；本卡增补主线 `torch_npu/csrc/npu/Event.cpp`（Python 绑定面）。产品和完整配套待核，保持draft、空平台。公开成员及已知接口产品范围复用[C++ NPUEvent](../../../apis/torch_npu/cpp_npuevent.md)，不从两个独立仓库的主线推定版本配套。运行、设备计时及并发验收待执行。

## 创建、状态与所有权

NPUEvent禁止复制，允许移动，转aclrtEvent调用event()。未创建时device()为空、event为nullptr、device_index为-1。通常首次record时创建并绑定流设备，后续record检查设备相同；从IPC句柄构造则先guard和LazySetDevice、打开句柄、登记IPC集合，再标记创建。显式ACL_EVENT_EXTERNAL且运行库有ValueWaitAndWrite能力时，flags构造会立即按当前流设备创建。

默认flags依AclCreateEventExWithFlag能力取ACL_EVENT_SYNC或ACL_EVENT_DEFAULT；这里DEFAULT由管理器头定义为0x0000000E。createEvent使用guard和LazySetDevice后调用AclrtCreateEventWithFlag；IPC flags还登记IPC集合。创建、打开/导出句柄、同步等路径在非BUILD_LIBTORCH构建且trace存在时调用相应回调。

recordOnce只看was_recorded_，LaunchRecordEventTask返回后将它置真；多次record仍可通过record入口。moveHelper交换flags、created、was_recorded、device_index和event句柄，所读函数没有交换is_waited_。这些是局部状态转移，调用者需保持对应所有权与外部事件协议。

## Host出队状态与设备完成

NPUEventManager的IsEventRecorded按unrecorded计数表判断：表中没有该event即返回真。它用于追踪Host侧尚未完成的record队列项，单凭该真值不足以证明ACL事件设备完成。

| 消费者 | 所读实际等待和检查 |
| --- | --- |
| query | 未创建返回true；TaskQueue开启且计数表仍有record时返回false，否则查询ACL recorded status，仅COMPLETE返回true。 |
| record(stream) | 必要时创建，检查流设备匹配，guard后LaunchRecordEventTask；外部ValueWrite路径清is_waited_，最后置was_recorded_。 |
| block(stream) | 仅已创建时工作；PerStreamQueue或IPC事件先循环等IsEventRecorded，每次sleep 10微秒，再guard目标设备并LaunchWaitEventTask。 |
| synchronize | 已创建且TaskQueue开启时忙等IsEventRecorded，此循环没有sleep或本地超时，然后aclrtSynchronizeEvent。 |

block遇到目标设备仍有capture时还调用emptyAllNPUStream。外部ValueWait路径在排入wait后检查is_waited_为假并置真，限制单次record关联多个wait；检查与排队的实际先后要一并记录。这里ACL_EVENT_EXTERNAL事件标志与外部来源NPUStream是两个不同入口条件。

主线record/block入口先调用checkNotExternalStream。该helper按NPUStream的external标记判断并用NOT_SUPPORT拒绝；所读发布Event.cpp没有这两个调用。主线NPUStreamUtils还声明裸aclrtStream及current-stream检查：裸句柄实现持锁查登记的external_streams，可限单设备或遍历设备；current-stream按流id标记，checkCurrentStreamNotExternal同样拒绝。这里只核对NPUStream.cpp指定消费者范围，其余流实现另计。

## 计时、IPC和reset

elapsed_time先要求两事件已创建，emptyAllNPUStream失败时记日志，仍继续同步两事件再调用ACL取毫秒间隔。recorded_time类似先检查创建、排空Host队列并同步事件，再取uint64时间戳；接口的微秒单位另见[recorded_time](../../../apis/torch_npu/event_recorded_time.md)。不能将这两个入口当作无等待查询或用Host调用耗时直接替代设备间隔。

ipc_handle在未创建时按当前流设备创建；TaskQueue非零时循环等record出队，每次sleep 10微秒，然后在事件设备guard下取IPC句柄。因此应先建立实际record协议，IsEventRecorded的空表真值本身不证明已经记录。reset只在不具备ValueWaitAndWrite能力且事件已创建时进入分支，要求ACL_EVENT_EXTERNAL，guard目标流设备后aclrtResetEvent；其余情况在本地直接返回。

析构在外部ValueWaitAndWrite路径直接返回。其他路径仅在已创建且NPU系统已初始化时提交lazy destroy，并按能力、PerStreamQueue或IPC条件请求管理器查询销毁；析构捕获所有异常。实际销毁和池化见[事件回收与EventPool](torch_npu_native_event_reclamation_and_pooling.md)。优化时分别记录Host排空/轮询、设备等待、记录次数及复用状态。

## Python 构造与 IPC 绑定面

增补固定主线 `torch_npu/csrc/npu/Event.cpp`（`torch_npu._C._NPUEventBase`，基类为 torch 的 THPEvent）。构造面仅收四个键：`enable_timing`/`blocking`/`interprocess`/`graph_external`（Python 端 external 键名是 graph_external）。两条硬门：`interprocess=True` 要求 `IsSupportIpcEvent(false)`，否则 NOT_SUPPORT 并提示升级 HDK(driver)/CANN；`interprocess` 与 `enable_timing`/`graph_external` 互斥（ACL_EVENT_IPC 不能与其他 flags 共用，源注释明确该 runtime 限制解除后可移除检查）。flags 选择按 `IsExistCreateEventExWithFlag` 分新旧路径：新路径 enable_timing 给 `ACL_EVENT_TIME_LINE | ACL_EVENT_SYNC`、否则 `ACL_EVENT_SYNC`；旧路径给 `ACL_EVENT_TIME_LINE`/`ACL_EVENT_DEFAULT`；interprocess 覆写为 `ACL_EVENT_IPC`，external 覆写为 `ACL_EVENT_EXTERNAL`。`blocking` 参数在绑定层不映射任何 ACL flag，只由上层语义消费。

`from_ipc_handle(Device device, str ipc_handle)` 是类方法：同样先过 `IsSupportIpcEvent(false)` 门；handle 字节数必须等于 `sizeof(aclrtIpcEventHandle)`，device 必须为 PrivateUse1，然后以 `NPUEvent(device.index(), &handle)` 打开。`ipc_handle()` 返回该结构的原始字节。计时面上 Python `elapsed_time(other)` 强制 other 是本类型（THNPEvent_Check）后委托 `npu_event.elapsed_time`——按上文计时节，这会先排空 Host 队列并同步两事件，**不是零等待查询**；`recorded_time` 同理。`record`/`wait`/`reset` 接受 torch 的 Stream 对象（unpack3 重建 NPUStream），不接受裸句柄；`wait`/`synchronize`/`reset` 释放 GIL 执行，`record`/`query` 不释放。`record`/`wait`/`synchronize`/`reset` 各带一条 ASCEND_LOGI 成功日志，可作为调用到达的最低限度证据，但不证明设备完成。`npu_event` 属性暴露裸 aclrtEvent 指针值。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUEvent.cpp)（primary），读取范围 1–311。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUEvent.h)（implementation），读取范围 1–108。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUEventManager.cpp)（implementation），读取范围 1–207。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUEvent.cpp)（implementation），读取范围 1–328。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUEvent.h)（implementation），读取范围 1–101。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUEventManager.cpp)（implementation），读取范围 1–218。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUStreamUtils.h)（implementation），读取范围 1–19。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUStream.cpp)（implementation），读取范围 153–155、879–930。
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUEventManager.h)（implementation），读取范围 1–52。
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUEventManager.h)（implementation），读取范围 1–52。
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Event.cpp)（primary），读取范围 1–317 全文。

## 发布 pin 对照（f3ecfe4a）

本节结论来自发布 pin 孪生文件的逐文件比对（比对口径：sha256 → 去空白 → 全空白折叠 token → 注释剥离 token）。

### 等价绑定（关键契约 token 一致，绑定面重排）

- `torch_npu/csrc/npu/Event.cpp`（317 → 302 行）：关键契约 token 两 pin 一致——构造 kwlist 恰四键（enable_timing/blocking/interprocess/graph_external）、`interprocess` 的 `IsSupportIpcEvent(false)` HDK/CANN 升级文案与互斥检查、`from_ipc_handle` 的句柄字节数==sizeof(aclrtIpcEventHandle) 与 PrivateUse1 设备校验。差异为绑定面 CPython API 重构（`THPEvent_dealloc_common`→`Py_TYPE/tp_free`、THNPEvent 命名等 28 个变更块），不改 aclrt 事件语义。本卡 host 提交与 IPC 结论对发布 pin 适用，行号锚按各 pin 文件核对。

### Evidence（发布 pin 补绑）

- [发布孪生 1](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/npu/Event.cpp)（release-twin-binding）：diff 级全文对照（绑定面重构，关键契约 token 一致）。


（本节静态比对，未运行/未编译；结论按文件分列，未列出的文件未比对。）
