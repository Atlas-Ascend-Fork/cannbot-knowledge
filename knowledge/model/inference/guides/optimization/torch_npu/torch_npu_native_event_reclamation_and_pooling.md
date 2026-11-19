---
type: Guide
title: TorchNPU事件延迟销毁与分设备EventPool复用
description: 解释Host记录和等待计数、FIFO回收门控、销毁线程池、IPC集合及按设备事件池的归还和清空边界。
tags:
- task.optimization
- topic.memory
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUEventManager.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUEventManager.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUEvent.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUEvent.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUEventManager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUEventManager.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUEvent.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUEvent.h
  role: implementation
created_at: '2026-11-11T03:50:38Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU事件延迟销毁与分设备EventPool复用

固定PyTorch主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf和发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b，完整读取Event和EventManager本地定义。两版Manager.cpp的完整C++ token相同，头文件主要ACL include路径不同；Event包装还存在外部流检查差异。产品、发布完整配套及并发/性能验收待核，本卡保持draft、空平台。Host提交、设备状态、IPC导出及析构入口见[原生Event](torch_npu_native_event_host_submission_and_ipc.md)。

## 两组Host计数和IPC集合

管理器是函数内static单例，构造5线程TaskThreadPool。unrecorded和unwaited使用两个独立mutex保护的event到int计数表；Increase不存在时插入1，已存在则加1。Decrease要求对应项存在，值为1时删除，否则减1。IsEventRecorded与IsEventWaited分别以对应表不存在该key为真，它们表示所追踪Host任务的计数条件，设备完成还需ACL检查。

ClearUnrecordedCount仅清record表，不能据名称扩大为同时清wait表。IPC集合另有mutex，Add要求插入成功，重复登记抛错；Remove在存在时删除，IsIpcEvent持锁查询。这些都是本地数据结构保护，未据此推导全部外层调用的并发保证。

## LazyDestroy和FIFO查询

| 路径 | 实际消费者 |
| --- | --- |
| LazyDestroy直接分支 | 运行库支持CreateEventExWithFlag、PerStreamQueue关闭且非IPC时直接aclrtDestroyEvent；失败经过特定错误检查并返回ACL错误码。 |
| LazyDestroy排队分支 | 持event_queue_mutex将事件追加到deque尾，返回ACL_ERROR_NONE；此返回不代表已经物理销毁。 |
| QueryAndDestroyEvent，PerStreamQueue或IPC | 查看队首，只有IsEventRecorded与IsEventWaited都为真才调度销毁；任一未满足即break。 |
| QueryAndDestroyEvent，其他事件 | 要求ACL recorded和wait status均COMPLETE，任一未满足即break。 |

通过门控的队首由thread_pool_->run调度到run，再从deque弹出；因此队首未就绪会挡住后续项，本函数也不等待刚调度任务全部执行完。run在非LIBTORCH且trace存在时先发删除回调，再aclrtDestroyEvent；失败记录并返回，成功后RemoveIpcEvent。调度通过、trace删除回调与ACL销毁成功是不同观察点。

ClearEvent先等线程池work完成，再逐项直接销毁deque中的事件，检查/警告错误并弹出，最后清IPC集合。它没有在本函数重走普通查询门控，也没有清两张计数表；关闭调用者须提供相应生命周期条件。未执行关闭或竞态实验。

## EventPool的设备分区与归还

EventPool按构造时device_count建立分设备池，保存固定flags。各PerDevicePool有按64字节对齐的mutex和unique_ptr向量，用于减少共享缓存行影响；注释把避免高成本重复创建作为设计动机，实际节省量待测。

get收到负数或超出池大小的设备编号时返回新NPUEvent，deleter直接delete，不池化。有效设备下先锁池，若有缓存则从向量尾pop并返回；否则创建新NPUEvent。返回NPUEventPtr的自定义deleter捕获对应pool引用，指针非空时持锁将同一对象压回池，而非立即析构。调用者必须使池对象寿命覆盖这些归还动作。

get只构造/取回事件包装，没有按device参数立即对普通flags创建底层ACL event；实际首次record绑定设备，特殊外部flags构造另有当前设备行为。所读取回和归还路径没有重置was_recorded_、is_waited_或其他Event状态，也没有显式等待事件完成。因此复用者仍应选择合适的record/等待协议，不能仅凭从池中取出就视为全新recordOnce状态。

empty_cache逐设备持锁clear缓存向量，从而析构池中已归还对象；它不枚举仍由调用者持有的NPUEventPtr，也没有在这个方法里同步所有设备。析构后续可能仍经过lazy destroy。测量时分开统计创建、Host队列、设备完成、归还、缓存清理和真实销毁，验证稳定资源占用后再比较复用收益。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUEventManager.cpp)（primary），读取范围 1–207。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUEventManager.h)（implementation），读取范围 1–52。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUEvent.cpp)（implementation），读取范围 1–311。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUEvent.h)（implementation），读取范围 1–108。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUEventManager.cpp)（implementation），读取范围 1–218。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUEventManager.h)（implementation），读取范围 1–52。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUEvent.cpp)（implementation），读取范围 1–328。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUEvent.h)（implementation），读取范围 1–101。
