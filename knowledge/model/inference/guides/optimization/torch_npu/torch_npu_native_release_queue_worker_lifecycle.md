---
type: Guide
title: TorchNPU ReleaseQueue的按需线程与参数回收
description: 对照发布的立即启动与主线aclop触发，解释释放环形缓冲、失败同步回退和主队列退出后的资源阶段。
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
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpParamMaker.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpParamMaker.cpp
  role: implementation
created_at: '2026-11-11T04:15:27Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU ReleaseQueue的按需线程与参数回收

固定PyTorch主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf和发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b，完整读取两版NPUQueue.cpp/h并定向核对OpParamMaker释放回调。产品与完整配套待核，保持draft、空平台，线程启动、故障与性能实验待执行。主任务环形队列见[Repository](torch_npu_native_repository_ring_and_host_drain.md)，具体参数移动见[异步回调所有权](torch_npu_native_async_copy_event_and_callback_ownership.md)。

## 释放的是Host任务参数

ReleaseQueue有独立8192槽缓冲、read/write索引和atomic RepoStatus，full采用下一write模8192等于read，保留一槽，最多8191个待读位置。releaseManager按slot调用CopyReleaseParam和ReleaseParam；这不是每条任务设备kernel完成的事件队列。

CopyReleaseParamFunc对OPAPI将handler等转到释放槽并Release原槽；编译执行走CopyEx，再清原hostMemory。ReleaseParamFunc随后调用对应参数Release。CopyParas/EventParas不在这两个回调中被推广成Tensor所有权容器。它们释放的实际资源由对应参数方法定义，不能直接等同于全部NPU内存已可复用。

## 两版启动行为

| 版本与入口 | 所读状态转移 |
| --- | --- |
| 发布InitReleaseQueue | 必要时分配缓冲，initialized=true、状态INIT，立即创建releaser并赋给成员，随后保存device_idx。ReleaseFunc总是PushToReleaseQueue。 |
| 主线InitReleaseQueue | 已初始化直接返回；必要时分配缓冲，先保存device_idx、buffer_initialized=true、状态INIT，只准备资源，不在此启动线程。 |
| 主线ReleaseFunc，线程已RUNNING | 所有后续任务继续Push，保留原异步释放行为。 |
| 主线ReleaseFunc，尚未RUNNING | 只有COMPILE_AND_EXECUTE尝试StartReleaseThreadIfNeeded且成功才Push；其余或启动失败直接ReleaseParamFunc同步释放。 |

因此OpAPI-only路径在这个主线消费者中可以只做同步参数释放，不会仅因InitRepo就建立releaser；这是一条源码路径，不是实测线程数、内存或吞吐收益。

主线worker状态初始NOT_STARTED，另有RUNNING、DISABLED、STOPPING、STOPPED。StartReleaseThreadIfNeeded未初始化返回false；RUNNING返回true，其余非NOT_STARTED返回false。对可启动状态持mutex二次检查，再创建线程；成功store RUNNING。std::system_error使状态DISABLED并返回false，当前函数没有把该状态自动重置为可重试，调用方转同步释放。不要将catch日志当成所有异常类别均可无损恢复的保证。

## Push、Pop与关闭

主线Push要求buffer已初始化且线程RUNNING，否则日志后返回；发布只检查initialized。正常Push在队列满时持续重试WriteToReleaseQueue，没有本地sleep、超时或状态取消分支；Write复制释放参数并在屏障后推进write。队列深度可能影响Host阻塞，实际成本需在负载下测量。

Pop在有项时调用ReleaseParam并推进read；无项且NEED_EXIT时转CAN_EXIT，否则通过select请求1微秒间隔后继续检查。StartRelease设RELEASE_THREAD与CPU affinity后循环Pop直到CAN_EXIT；它没有像consumer那样在本函数SetDevice。select请求时长及header对poll的估算都不代表硬实时保证。

主线析构仅在worker RUNNING且线程可join时置STOPPING、RepoStatus NEED_EXIT、join，再置STOPPED，最后释放缓冲；发布在initialized且joinable时走NEED_EXIT/join，再释放缓冲。Repository析构先停止并join consumer，释放其普通缓冲和eventfd，随后成员ReleaseQueue继续自身析构。未join的在外任务与设备实际完成需要调用方生命周期协议，不能从Host缓冲释放推导设备已同步。

GetStatus在未初始化时只记日志后读atomic；SetStatus/ChangeStatus在该条件下记日志并返回，后者用compare_exchange_strong。GetDeviceID返回保存设备。新旧启动时序、同步/异步参数释放和当前worker状态要一并记录，再比较Host开销、资源占用和长时间运行的稳定性。本卡仅有源码证据。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUQueue.cpp)（primary），读取范围 1–1074。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUQueue.h)（implementation），读取范围 1–218。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUQueue.cpp)（implementation），读取范围 1–982。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUQueue.h)（implementation），读取范围 1–169。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpParamMaker.cpp)（implementation），读取范围 586–854。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpParamMaker.cpp)（implementation），读取范围 468–742。
