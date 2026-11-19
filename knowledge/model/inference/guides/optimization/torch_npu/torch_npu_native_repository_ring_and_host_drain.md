---
type: Guide
title: TorchNPU原生Repository的环形队列、Host排空与错误状态
description: 核对环形缓冲、eventfd生产消费协议、poll循环、GIL与DVM边界，区分Host提交结束和设备运行完成。
tags:
- task.optimization
- topic.memory
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUQueue.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUQueue.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUQueue.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUQueue.h
  role: implementation
created_at: '2026-11-11T04:15:27Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU原生Repository的环形队列、Host排空与错误状态

固定PyTorch主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf和发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b，完整静态审读两版NPUQueue.cpp/h。产品与完整配套待核，保持draft、空平台；没有运行线程、设备或故障注入。流层选择repo和同步范围见[原生流队列](torch_npu_native_stream_queue_drain_and_synchronization.md)，故障定位入口复用[TaskQueue诊断](torch_npu_taskqueue_error_and_flush.md)。

## 缓冲、回调和初始化

Repository实现NPUQueueBase的状态、入队、出队、排空、初始化和诊断虚接口；FactoryBase只声明create入口，本地头没有为所有外部queue backend提供实现。sring_idx保存working和volatile unsigned idx，状态为atomic<RepoStatus>。不要把volatile索引当作已验证的任意多生产者并发保证。

普通环形缓冲固定4096槽，full判断为(write+1)&4095==read，保留一个槽区分空/满，最多4095个待读位置。WriteQueue持mu_enqueue，检查状态和是否满，通过注册Copy回调复制参数，在内存屏障后推进write索引。容量注释说明设备资源占用和并发之间的设计取舍，没有实测收益或固定最优深度。

两个CallBackManager分别服务普通任务和释放参数，保存exec/copy/release/new/delete/copyReleaseParam/releaseParam函数。注册器将相应回调接到两者，slot地址按new回调给定sizePerParams计算；调用缺失回调会TORCH_CHECK。实际参数构造、移动和释放由对应回调定义，见[异步任务与参数所有权](torch_npu_native_async_copy_event_and_callback_ownership.md)。

InitRepo必要时分配缓冲，创建read/write/empty三个eventfd，将initialized置真、状态INIT、保存device，再启动consumer。主线先InitReleaseQueue再启动consumer；发布顺序是先启动consumer再InitReleaseQueue。StartConsume设置ACL_THREAD、CPU affinity和设备；SetDevice失败记录错误后仍进入出队循环，未从该分支直接退出。

## 入队与出队协议

Enqueue未初始化时日志后返回，只有RUN/INIT进入写循环。队列满时清write-working，屏障后重查，仍满则eventfd_read(efd_write)等consumer；成功写入后在read-working为假时发efd_read通知。EINTR重试，其它eventfd错误日志后返回，接口本身返回void。

Dequeue设置read-working；空时清标志、屏障及重查后等待efd_read。成功读取并推进索引后，need_empty且队列已空时通知efd_empty；producer不在工作时通知efd_write。working标志、二次检查和屏障是同一套本地协议，不能只取“索引相等”替代所有调用条件。

ReadQueue在队列为空且GetTaskQueueEnable()==2时最多执行200000次空检查，仍空才返回false；其它mode直接返回false。源码注释把该循环估作1ms，实际代码没有按墙钟截止。发布将mode缓存在函数内static，主线每次ReadQueue重新读取。忙轮询次数不是所有设备/负载下固定1ms的性能保证。

非LIBTORCH路径在执行回调前后发Profiler mark2/3，然后Release参数并推进读索引。回调返回只说明该Host任务调用完成；它可以只是向ACL异步提交，不证明设备kernel已经结束。

## MakeSureQueueEmpty、GIL和融合提交

未初始化返回NPU_STATUS_FAILED。consumer可join时，循环检查空队列，持mu_empty设置need_empty并再次检查；仍非空就等efd_empty，EINTR重试，其它read错误恢复已释放GIL后返回INTERNAL_ERROR。正常结束会复查状态和错误消息，最后返回SUCCESS或按check_error抛错。

主线排空前在lazy_fusion::IsEnabled时调用LazyFusionFlush；Enqueue在融合开启时也先Flush，唯独LAZY_DESTROY_EVENT类型跳过，因为该任务可来自并行析构线程。这里证明当前PyTorch引用这两个符号，不将独立OpPlugin主线自动视为已配套构建。

主线仅g_used_aclop时取得PythonGilHooks并调用release_if_held，结束/指定eventfd错误路径按返回state调用restore；满队列等待类似经PythonGilCallback包装。发布非LIBTORCH构建直接检查PyGILState_Check与g_used_aclop，使用Save/RestoreThread或BEGIN/END_ALLOW_THREADS。注释讨论TE编译与allocator锁交互；不把“等待时无条件释放GIL”当作通用优化规则。

## 错误传播和关闭

ReadQueue回调非零时记录当前任务信息，逐项Release并忽略剩余任务，再按返回码/错误文本分类，ClearQueue并清EventManager的unrecorded表。分类包括UCE、HBM多bit ECC、suspect memory、HCCS link、HCCL retry、suspect remote；MEM_ERROR或内存错误文本命中首分支时，只有checkUceErrAndRepair(false,err_msg)为true才置UCE_EXIT；返回false在本函数没有另改状态。未命中上述if/elseif且当前非STOP_EXIT的分支才置ERROR_EXIT。STOP_EXIT相关路径还调用设备同步处理abort与已取得任务交错，不能据清Host队列宣布设备已经恢复。

ThrowDeviceError在这些设备状态下通常抛错，但LAZY_DESTROY_EVENT与RECORD_EVENT例外。ERROR_EXIT在Enqueue/MakeSureQueueEmpty中转CAN_EXIT后报告异步错误；CANN OOM文本可触发受选项控制的snapshot observer并抛OutOfMemoryError。check_error=False会跳过这里的runtime_error抛出，返回SUCCESS也不独立证明没有设备错误；CAN_EXIT另有诊断消息。repo_error和acl_error是该CPP的静态字符串，不是每个Repository自有诊断字段。

ClearQueue直接令read=write，屏障后通知empty和write；它没有在该方法逐项执行参数释放，不能代替前述错误分支的Release循环。析构令consumer NEED_EXIT、通知read并join，再通知empty、释放缓冲及fd；ReleaseResource只关闭值大于0的fd。GetPara在空时返回EmptyQueue，否则读取当前槽错误描述；Get/SetQueueErrMsg处理本对象错误字符串。主线部分日志走dispatch和ASCEND双宏，发布部分DEBUG构造有显式级别分支，日志实际成本仍需测量。

评估时分开统计排队等待、poll、ACL提交、设备执行、参数释放及错误观察点；完整本地代码覆盖不等于已验证所有故障恢复或并发调度。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUQueue.cpp)（primary），读取范围 1–1074。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUQueue.h)（implementation），读取范围 1–218。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUQueue.cpp)（implementation），读取范围 1–982。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUQueue.h)（implementation），读取范围 1–169。
