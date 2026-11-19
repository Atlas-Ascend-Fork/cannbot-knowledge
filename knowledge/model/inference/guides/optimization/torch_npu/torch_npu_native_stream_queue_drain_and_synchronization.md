---
type: Guide
title: TorchNPU原生流的队列选择、排空与设备同步
description: 解释stream取柄的排队副作用、按流和默认Repository的入队选择，以及设备同步、恢复与控核状态边界。
tags:
- task.optimization
- topic.memory
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUStream.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUStream.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUStream.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUStream.h
  role: implementation
created_at: '2026-11-11T03:59:42Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU原生流的队列选择、排空与设备同步

固定PyTorch主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf与发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b，完整读取两版NPUStream.cpp/h。产品、完整配套及运行验收待核，保持draft、空平台；本卡只证明本地流层消费者，Repository和ACL内部实现各有独立范围。池轮转、外部流和包装身份见[流池与身份](torch_npu_native_stream_pools_and_external_identity.md)。

## 取ACL句柄时实际排空哪条Host队列

| 入口或条件 | 所读本地动作 |
| --- | --- |
| NPUStream::stream()，PerStreamQueue开启 | 取该流internals；主线先拒绝external；非sync-launch且本流repo已初始化时MakeSureQueueEmpty。失败记日志并返回nullptr。 |
| NPUStream::stream()，PerStreamQueue关闭 | 取当前设备default repo；非sync-launch且该repo已初始化时MakeSureQueueEmpty，失败返回nullptr；最后返回接收者流的ACL句柄。 |
| stream(false) | 直接从接收者internals取ACL句柄，没有本地队列排空。stream(true)转stream()。 |
| getCurrentNPUStreamNoWait | 直接取得当前流句柄，没有本地MakeSureQueueEmpty。 |

转换运算符aclrtStream也调用stream()，因此不是固定的纯字段读取。主线一进入stream()就解析接收者internals；发布非按流分支在default排空之后才取得用于最终返回的cur_ptr，但排空条件中的isSyncLaunchStream本身也会先访问接收者internals，最终cur_ptr的位置不等于第一次访问接收者。非按流模式中，接收者流的设备与当前设备default选择需分别核对。sync-launch会绕开这项排空；绕开Host队列的句柄本身不证明前置任务已向设备提交。

query在guard所属设备后通过stream()取得句柄，再AclrtStreamQuery判断COMPLETE；synchronize同样先取可能排空的stream()，再调用AclrtSynchronizeStreamWithTimeout。主线两者拒绝external；调用者负责外部流同步。实际扩展launch应保持排队及资源寿命，复用[TaskQueue适配指南](torch_npu_custom_op_taskqueue_adaptation.md)。

## 入队、当前流和状态

enCurrentNPUStream初始化并检查设备，将QueueParas的correlation_id设为全局计数递增值，paramStream总是取该设备线程本地current_streams句柄。PerStreamQueue开启时，task_stream可另行指定要使用的repo；这不会在本函数重写前述paramStream，调用者应保持任务实际流与队列选择一致。

主线在解引用显式task_stream和所选内部对象前后分别拒绝external；已登记external对象repo为空，因此这些检查有具体资源边界。普通repo首次入队时在全局init_repo_mutex下延迟InitRepo(device)。随后Enqueue；若repo状态为INIT，则MakeSureQueueEmpty再把INIT改RUN。非按流模式始终进default repo并采用同样INIT处理，源码此分支没有主线按流分支那组external检查。

setCurrentNPUStream只改对应线程本地指针，必要时记流交换日志。setDefaultStreamsStatus按STOP_EXIT设置default的is_repo_stop标志，repo已初始化才SetStatus。setDataPreprocessStream/isDataPreprocessStream/getRepoStopFlag这些成员实际查询当前流，而非直接沿接收者*this；记录调用时当前流，避免由对象名字误判目标。isSyncLaunchStream则沿接收者内部对象。

## 排空与设备同步的不同范围

emptyAllNPUStream先遍历已创建default且repo已初始化者；PerStreamQueue开启时再处理secondary和两个普通优先级池。遇到MakeSureQueueEmpty失败立即返回；全部通过返回SUCCESS。它没有遍历external或sync-launch池，也没有在本函数调用设备同步，名字中的All不能替代完整设备完成协议。

getRepoInfo与setRepoErrMsg只遍历已创建且repo已初始化的default，分别收集GetPara或设置错误信息。IsTaskQueueEmpty也只取当前设备default repo的IsEmptyRepo，没有聚合secondary/其它普通池。

npuSynchronizeDevice在TaskQueue开启时先emptyAllNPUStream，排空失败记日志但仍调用AclrtSynchronizeDeviceWithTimeout；ACL失败先经特定错误检查，再按check_error选ERROR或WARN，返回ACL结果是否成功。非LIBTORCH构建且成功时可触发设备同步trace。npuSynchronizeUsedDevices同样先排空，然后调用SynchronizeUsedDevices并按check_error检查/警告；它的实际设备集合由该下游函数定义，本卡不从函数名推导所有可见设备。

## 恢复与控核辅助状态

recovery_all_npu_streams在设备未初始化时返回；否则guard设备，将default与secondary句柄置空后重新创建，再对已有普通池句柄调用创建。这里没有重建sync-launch/external，也没有在本函数重置全部队列、计数和call_once状态，恢复完整性需结合调用方协议。

StreamInitFlag读取指定设备初始化标志。控核开关为初始false的atomic<bool> enable_core_control，所读load采用memory_order_relaxed；开关关闭时check_enqueue_need_use和check_dequeue_need_use均返回false。开启时enqueue比较并更新thread_local tls_prev_stream，dequeue比较并更新当前设备default内部对象的prev_stream；流变化返回true，不变返回false。is_core_control_enabled读取该开关；这些helper只报告转换条件，本函数没有执行实际控核。

优化评估应分别记录所选repo、实际paramStream、Host排空次数、ACL同步和恢复路径，并检查跨流依赖与对象寿命。静态分支、trace回调和错误日志都不替代实际吞吐、延迟或数值验收。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUStream.cpp)（primary），读取范围 1–1037。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUStream.h)（implementation），读取范围 1–166。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUStream.cpp)（implementation），读取范围 1–817。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUStream.h)（implementation），读取范围 1–172。
