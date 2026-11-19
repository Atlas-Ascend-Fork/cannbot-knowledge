---
type: Guide
title: TorchNPU异步Copy与Event的队列选择和参数所有权
description: 解释Copy与record/wait的直调和入队分支、批量元数据捕获、OPAPI V2参数移动及Host事件计数的准确含义。
tags:
- task.optimization
- topic.memory
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/interface/AsyncTaskQueueInterface.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/interface/AsyncTaskQueueInterface.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/interface/AsyncTaskQueueInterface.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/interface/AsyncTaskQueueInterface.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpParamMaker.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpParamMaker.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/NPUDefine.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/NPUDefine.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/NPUDefine.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/NPUDefine.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUMemorySwap.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUMemorySwap.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUMemorySwap.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUMemorySwap.h
  role: implementation
created_at: '2026-11-11T04:15:27Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU异步Copy与Event的队列选择和参数所有权

固定PyTorch主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf与发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b，完整读取两版AsyncTaskQueueInterface.cpp/h，定向读取OpParamMaker和NPUDefine的完整相关函数。产品与配套待核，保持draft、空平台，未导入、执行copy、创建事件或测试设备。Repository和流选择分别见[队列本体](torch_npu_native_repository_ring_and_host_drain.md)、[原生流队列](torch_npu_native_stream_queue_drain_and_synchronization.md)。

## 公共参数与分派

QueueParas保存paramStream、paramType、paramLen、paramVal和correlation_id，后者的全局atomic从0开始，真正入队时由流层赋值。类型1..10依次包含编译执行、async memcpy、record/wait/lazy destroy/reset、OPAPI/V2、write/wait value。枚举有值不表示这里的funcMap为每个值都提供消费者。

CopyParas只复制src/dst地址、长度和kind；EventParas复制event与allocator类型（HOST=1、NPU=2、默认RESERVED=-1）。这些复制不自动持有来源Tensor/Storage。record_function使用copy-kind/event名字映射，Profiler入队前后mark0/1与correlation记录也不独立证明设备完成。

## 单次与批量Copy

LaunchCopyTask仅在当前流非sync-launch且TaskQueue开启时构造ASYNC_MEMCPY并enCurrentNPUStream；否则直接调用ACL。D2H且运行库支持时走AclrtMemcpyAsyncWithCondition，其余走aclrtMemcpyAsync。MemcopyAsyncFunc 出队消费者采用相同条件，失败可用thread-level PeekAtLastError替换错误码，再返回给队列错误处理。

批量入口按相同门控选择EXECUTE_OPAPI_V2 lambda或直接AclrtMemcpyBatchAsync。入队分支将src/dst地址、长度、attrs和attrsIndexes复制到vector并按值捕获，连同numBatches、numAttrs和显式stream传入lambda。该代码对所有这些数组都复制numBatches项，未在本地另按numAttrs验证实际数组长度；指向的数据缓冲仍由调用者维持。

lambda在执行时重建数组，使用局部failIdx=SIZE_MAX并将其地址交ACL；本地没有把failIdx作为输出返回给调用者。批量分支门控看当前流，实际调用使用传入stream，这两个流来源要分别记录。两个公共LaunchCopy包装正常返回ACL_ERROR_NONE；排队完成或这一返回值不意味着设备copy已完成，异常检查另走对应分支。

## 栈参数怎样进入持有回调的槽

LaunchBatchCopyTaskEnQueue创建栈上ExecuteParasOpApiV2，保存op_name和acl_call指针，接着同步调用enCurrentNPUStream。WriteQueue在返回前调用CopyFunc，将目标paramVal定位到slot头之后，析构上次含非平凡字段的对应对象，再placement-new本次参数。

CopyFunc将V2类型归一为EXECUTE_OPAPI，复制流/长度/correlation，调用ExecuteParasOpApi::Copy(V2)。NPUDefine的该重载把名称复制到100字节opType范围，并从*customHandler执行std::move，因此捕获的vector随std::function进入槽；普通Copy同样move handler。Release将handler置nullptr。此处持有的是lambda捕获的元数据，不能额外推导所有裸指针背后的存储已被强引用。

funcMap按paramType和paramStream分派，包含普通OPAPI而没有单独V2条目，与上述归一过程对应；RESET_EVENT也没有出现在所读map中。ReleaseParamFunc只为OPAPI和编译执行调用具体Release，其他参数类型不在该函数做相同析构动作。参数回收线程见[ReleaseQueue](torch_npu_native_release_queue_worker_lifecycle.md)。

## Record、Wait与Value协议

EventTask按传入npuStream而非随意使用当前流判断sync-launch。需要入队时先NPUStreamGuard切换到该流，普通record/wait分别构造RECORD_EVENT/WAIT_EVENT；ACL_EVENT_EXTERNAL且ValueWaitAndWrite可用时改为WRITE_VALUE/WAIT_VALUE。入队之前分别IncreaseUnrecordedCount/IncreaseUnwaitedCount，之后记录correlation。主线公共LaunchRecordEventTask/LaunchWaitEventTask先拒绝external来源流，发布这两个调用点没有相同检查。

直调record使用ValueWrite(event,1)或aclrtRecordEvent；直调wait使用ValueWait再ValueWrite(event,0)，或aclrtStreamWaitEvent。事件flags的EXTERNAL与外部来源stream并不等价，见[原生Event](torch_npu_native_event_host_submission_and_ipc.md)。

所读队列RecordEventFunc和WaitEventFunc在ACL调用及错误码提取后仍各自减Host计数，ValueWriteFunc也减unrecorded。因此计数变为零表示对应Host消费者处理完毕，不能单凭IsEventRecorded/Waited判定ACL成功或设备完成。ValueWaitResetFunc先wait后write0并返回后一次ret，所读该函数没有DecreaseUnwaitedCount；这里保留真实局部表达式，未据此声明已复现故障。

LazyDestroy门控看当前流；排队时enCurrentNPUStream另传事件device_index，直调时调用EventManager::LazyDestroy。公共包装在调用任务前就可能发删除trace，真实ACL销毁仍沿管理器路径；回调、Host出队和物理销毁是不同观察点。采用时同时记录stream/device、队列开关、事件能力、Host计数与存储寿命，再检查设备完成和数值。

## memory_swap只是带方向编码的裸指针Copy入口

本卡完整覆盖两版NPUMemorySwap.cpp/h。at_npu::native::memory_swap声明返回void，参数为dst/dst_len/src/src_len/type；先要求两地址非空、两个size_t长度都大于0、type在闭区间[0,3]。即使某一调用方想表示空搬运，这个本地入口也不会把零长度当无动作成功。

| type | 交给LaunchAsyncCopyTask的aclrtMemcpyKind |
| --- | --- |
| 0 | HOST_TO_HOST |
| 1 | HOST_TO_DEVICE |
| 2 | DEVICE_TO_HOST |
| 3 | DEVICE_TO_DEVICE |

随后只把这些地址、容量/长度和方向交c10_npu::queue::LaunchAsyncCopyTask，并NPU_CHECK_ERROR其返回值。switch的default不放宽前面的type校验。这里没有新建Storage、分配/换出策略、Tensor dtype/shape/stride验证、按地址自动识别设备、额外device guard或目标容量不少于源长度的独立检查；不能仅据函数名把它当作完整自动显存交换管理器。

队列选择和ACL消费者仍是前文的AsyncTaskQueueInterface；返回检查不代表设备copy已经完成，裸指针包装也没有额外持有来源Tensor/Storage。调用方要保存正确设备/流、地址容量、源和目标的存储寿命及设备完成协议，不能把memory_swap返回void解释为数据已可立即重用或底层一定没有异步错误。两版局部校验/四方向映射分别全文核对，未执行任何搬运或性能实验。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/interface/AsyncTaskQueueInterface.cpp)（primary），读取范围 1–342。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/interface/AsyncTaskQueueInterface.h)（implementation），读取范围 1–79。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/interface/AsyncTaskQueueInterface.cpp)（implementation），读取范围 1–322。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/interface/AsyncTaskQueueInterface.h)（implementation），读取范围 1–72。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpParamMaker.cpp)（implementation），读取范围 586–854。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpParamMaker.cpp)（implementation），读取范围 468–742。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/NPUDefine.h)（implementation），读取范围 77–93。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/NPUDefine.h)（implementation），读取范围 71–87。
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/NPUDefine.cpp)（implementation），读取范围 39–58。
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/NPUDefine.cpp)（implementation），读取范围 42–60。

- [完整原生入口声明/定义](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUMemorySwap.cpp)（implementation）：全文1–51。

- [完整原生入口声明/定义](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUMemorySwap.h)（implementation）：全文1–26。

- [完整原生入口声明/定义](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUMemorySwap.cpp)（implementation）：全文1–52。

- [完整原生入口声明/定义](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUMemorySwap.h)（implementation）：全文1–26。
