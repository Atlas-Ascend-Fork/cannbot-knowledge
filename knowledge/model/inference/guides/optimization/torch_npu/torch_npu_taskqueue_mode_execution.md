---
type: Guide
title: TaskQueue模式执行：环境缓存、动态覆盖与宏选择
description: 追踪执行宏到OptionsManager的缓存链，区分环境初始化、主线动态模式和发布调用点缓存，避免把const差异当环境热更新；并给出EXEC宏内PTA执行计划缓存（hit_cache/hit_cache_v2）的准入、键构成与命中路径。
tags:
- task.optimization
- topic.memory
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/register/OptionsManager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/register/OptionsManager.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/ASCEND_LAUNCH_BLOCKING.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpCommand.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpCommand.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUGraph.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUQueue.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUQueue.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_kernel_check.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/_kernel_check.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/PER_STREAM_QUEUE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/TASK_QUEUE_ENABLE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUStream.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUStream.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUEvent.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUEvent.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUEventManager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUEventManager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/impl/NPUGuardImpl.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUQueue.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUQueue.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUQueue.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUQueue.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/interface/AsyncTaskQueueInterface.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/opapi/update_op_api_common.h
  role: implementation
created_at: '2026-11-10T14:37:38Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TaskQueue模式执行：环境缓存、动态覆盖与宏选择

## 所选调用链与配套边界

本卡对照OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`、发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的EXEC_NPU_CMD入口，以及TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`、发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的OptionsManager选定函数。跨仓主线仅作静态源码对照，不能当成已配套安装、ABI兼容或运行行为认证；整卡平台未知，保持draft、空平台。

[动态set/get API](../../../apis/torch_npu/task_queue_mode.md)已有公开优先级、纯推理及切换责任；[TaskQueue下发](torch_npu_taskqueue_delivery.md)已有Level0/1/2和图模式限制。本卡补准确C++缓存层和宏消费者，不重复公开支持表。未导入或执行上游，未切换队列、修改进程环境或进行设备实验。

## 环境值不是每次从进程环境重读

两版GetTaskQueueEnable首先调用CheckBlockingEnable，为真即返回0。两版CheckBlockingEnable自身使用函数内static初始化结果：经GetBoolTypeOption读取ASCEND_LAUNCH_BLOCKING，保留该布尔结果。所读GetBoolTypeOption通过get_and_log_env/std::getenv取值，再strtol并归一为0/1；不是每次getter都重新解释同步环境。

TASK_QUEUE_ENABLE的环境读取同样位于GetTaskQueueEnable内的static lambda，缺省1，解析结果须落入0/1/2集合。仅在执行到这一初始化时采集并缓存；不能从外层const变量改为非static就推导改os.environ能热更新该缓存。若getter被同步模式或动态分支提前返回，该环境lambda尚不一定初始化。

这里核对的是局部初始化/分支顺序，不把strtol调用当成严格的整字符串格式校验，也不把缓存值等同实际设备执行已完成。

## 主线动态覆盖独立于环境缓存

主线全局atomic模式初值为TASK_QUEUE_ENABLE_ENV=-1。同步判断之后，getter以relaxed load读它；不是-1时直接返回动态模式，只有仍为哨兵才进入环境路径。发布所读getter没有这一动态检查，保留同步优先、随后环境缓存的结构。

主线SetTaskQueueEnable校验mode在0/1/2，调用emptyAllNPUStream后才relaxed store新模式；所查setter没有把-1写回环境回退的分支。不能把atomic读写解释成允许任意线程并发提交期间安全切换，也不能把调用emptyAllNPUStream的名称扩大成已经核验所有Device计算完成、所有执行器/捕获图均重新配置或失败可回滚。

Python主线setter先处理str→int并检查取值，随后进入_C；Module.cpp的绑定再检查Python整数与范围，调用C++ setter。getter绑定调用同一OptionsManager getter并打包int，故同步优先仍生效。公开调用责任和潜在阻塞继续按API卡消费；本卡没有运行它们。

## EXEC_NPU_CMD的两版读取位置不同

| 宏入口 | 所选静态源码行为 |
| --- | --- |
| 主线 | 每次宏调用建立局部const auto并调用GetTaskQueueEnable；此调用可以看到上述动态atomic覆盖，但环境回退本身仍缓存。 |
| 发布 | 宏展开体使用static const auto保存首次GetTaskQueueEnable结果；缓存位于各展开调用点，不能说成所有算子共享一份宏局部static。 |

两版都只在有效值==2时转EXEC_NPU_CMD_V2，其余转V1。0和1在这个选择器都到V1，不等于二者整个runtime、线程或同步行为相同；V1/V2及其他消费者还可能继续读取模式。本卡没有将全部展开依赖、已有编译图和所有原生入口逐一审完。

因此，两个薄包装自身token相同，只能证明所比局部包装相同，不能证明宏展开、环境读取时机或完整runtime相同。主线动态API与主线宏的连接可作为静态消费者依据，不能把主线setter配到发布宏就认证动态切换有效。

## 优化与验证入口

先记录准确软件提交、调用入口、是否已经触发环境缓存、同步模式与是否调用过动态setter，再区分公开配置值、getter有效值和宏V1/V2选择。保持公开要求的无并发提交条件和模式限制；跨仓组合、捕获状态、错误路径与切换开销需要在实际配套环境另行验证。

[兼容宏指南](torch_npu_opplugin_adaptation.md)中的DO_COMPATIBILITY是另一层符号/回退选择，不能与本卡的队列模式优先级混用。本卡不提供环境热更新承诺、设备支持推断、性能数字或verified记录。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（primary）：485–493。
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）：435–443。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.cpp)（implementation）：60–77,178–187,213–217,630–659。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/register/OptionsManager.cpp)（implementation）：28–36,112–124,152–158,552–567。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.h)（implementation）：41–43,83–85。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/register/OptionsManager.h)（implementation）：81–85。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp)（implementation）：1798–1817,2354–2355。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/utils.py)（implementation）：325–362。


## ASCEND_LAUNCH_BLOCKING 文档语义与实现对照

对照主线文档页 `docs/zh/api/environment_variable/op_execution/ASCEND_LAUNCH_BLOCKING.md`（@ac0e1564）逐句核两 pin 实现，增补本卡已持有的 CheckBlockingEnable 缓存链之外的生效面。

**同步生效点与两处例外**：四个 OpCommand 执行方法（主线 `Run` :135-188、`RunOpApi` :188-233、`RunOpApiV2` :234-283、`RunOpApiV3` :284-331；发布版同型 :131-185/:185-232/:232-285/:285-331）的非 task-queue 分支里，`OpCommandImpl::RunOpApi`（或 `aclCmd->Run`）之后检查 `CheckBlockingEnable()`，为真且 `currentStreamCaptureStatusMayInitCtx() != CaptureStatus::Active` 时才执行 `Sync()`（Run 路径）或 `AclrtSynchronizeStreamWithTimeout(stream)`（三个 RunOpApi 路径）。即：同步是**逐算子逐流**的，且有两个文档未记录的例外——**图捕获 Active 期间跳过同步**；NPUGraph replay（主线 NPUGraph.cpp :405）另有 `!isExternalStream(stream)` 条件，外部流重放不同步，而**发布版 NPUGraph.cpp 无该分支**（全文件零命中 CheckBlockingEnable，发布差异）。

**取值校验是硬失败**：`CheckBlockingEnable`（主线 :178-187、发布 :112-118）经 `GetBoolTypeOption("ASCEND_LAUNCH_BLOCKING", 0)` 读取，值不在 0/1 集合时 `TORCH_CHECK(false, "ASCEND_LAUNCH_BLOCKING should be 0 or 1.")`——首次调用即抛错，与 FORCE_OVERFLOW_CHECK 的静默忽略风格相反（见 inf_nan 卡增补节）。因 static 一次性求值，非法值进程内首查即终止，合法值此后不再读进程环境。

**队列关闭链的两级效果**：本卡已记 GetTaskQueueEnable 首查 CheckBlockingEnable 返回 0；`GetPerStreamQueue`（主线 :660-673、发布 :568-580）同样首查 `CheckBlockingEnable() || GetTaskQueueEnable() == 0` 即返回 0——**ASCEND_LAUNCH_BLOCKING=1 同时强制 PER_STREAM_QUEUE=0**，文档只声明 TASK_QUEUE_ENABLE 失效，未记 PER_STREAM_QUEUE 一并失效。

**文档「0 会增加内存消耗、有 OOM 风险」**：静态窗口无法证实该机制（task queue 两级流水与分配器交互全链不在本卡来源范围），只记为文档侧运行时断言；与两级流水/异步释放模型方向一致但本卡不据此下结论。

**Python 侧写入者的顺序依赖**：`torch_npu/npu/_kernel_check.py:34` 的 `KernelPathManager.__init__` 无条件 `os.environ["ASCEND_LAUNCH_BLOCKING"] = "1"`（两 pin 同文件同行，字节一致）——发生在进程启动后；若 C++ 侧 static 已被此前任一算子求值，该写入不影响本进程 getter，文档未记录该时序边界。另：NPUQueue.cpp 内部错误信息（主线 :320-324/:588-591、发布同型）主动建议设置该变量并警告性能退化——文档调试理由在错误文案中的回声；profiler 侧 `_utils.py:15` 仅把该环境值记入分析元数据，不消费。

## ASCEND_LAUNCH_BLOCKING 相关来源

- [ASCEND_LAUNCH_BLOCKING 文档页 @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/ASCEND_LAUNCH_BLOCKING.md)（primary；:1-41 全文）
- [主线 OpCommand.cpp @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpCommand.cpp)（implementation；:160-180、:213-223、:263-273、:305-331 同步插桩窗）
- [发布版 OpCommand.cpp @f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpCommand.cpp)（implementation；:164-178、:211-221、:264-274、:306-331 同步插桩窗）
- [主线 NPUGraph.cpp @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUGraph.cpp)（implementation；:398-410 replay 同步窗）
- [主线 NPUQueue.cpp @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUQueue.cpp)（implementation；:315-326、:585-595 错误文案窗）
- [发布版 NPUQueue.cpp @f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUQueue.cpp)（implementation；:318-330、:551-560 错误文案窗）
- [主线 _kernel_check.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_kernel_check.py)（implementation；:25-40 初始化窗）
- [发布版 _kernel_check.py @f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/_kernel_check.py)（implementation；:25-40，两 pin 字节一致）
- [主线 profiler _utils.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_utils.py)（implementation；:15 元数据记录锚）

## PER_STREAM_QUEUE 与 TASK_QUEUE_ENABLE 文档语义与实现对照

对照主线文档页 `docs/zh/api/environment_variable/op_execution/PER_STREAM_QUEUE.md`（44 行全文）与 `TASK_QUEUE_ENABLE.md`（63 行全文）逐句核两 pin 实现，补本卡已有缓存链之外的生效面。未另注的行号均为主线 ac0e1564，发布 f3ecfe4a 另标。

**PER_STREAM_QUEUE 取值无集合校验**：`GetPerStreamQueue`（主线 :661-673、发布 :569-580）经 `strtol` 裸读、缺省 0——文档「0 关/1 开、默认 0」与默认一致，但**没有 0/1 集合校验**：非数字串解析为 0 静默关闭，任何非零数字（如 "2"）按开启处理。与 TASK_QUEUE_ENABLE 的 {0,1,2} `TORCH_CHECK`、ASCEND_LAUNCH_BLOCKING 的 `GetBoolTypeOption` 硬失败相比，这是同族三个环境变量里唯一的无校验入口。文档约束「当 TASK_QUEUE_ENABLE 配置为 1/2 时此环境变量才能生效」对应实现首查 `CheckBlockingEnable() || GetTaskQueueEnable() == 0` 即返回 0（task queue 为 1 或 2 都放行）；但 PER_STREAM_QUEUE 页未记 ASCEND_LAUNCH_BLOCKING=1 的连带强制 0（上节已从 blocking 页角度记录，此处是该页侧缺项）。「试验性功能」提示为页面自declare，无实现面对应。

**文档未记的 per-stream 生效面副作用**（主线实现；发布另标）：

- `NPUStream::stream()`（:469-486）per-stream 分支：**拒绝外部流**（TORCH_CHECK "External NPU stream is not supported in NPUStream::stream() with per-stream task queue."），且流 repo 已初始化且非同步 launch 流时先 `MakeSureQueueEmpty` 排空本流队列再交出裸流——开启后每次取裸流都可能等待队列排空。**发布版同函数（:366-378）无该 TORCH_CHECK**，只有排空分支（发布差异）。
- `emptyAllNPUStream`（:638-663）：默认流逐 device 排空后，per-stream 分支再对 secondary 流逐 device 排空。
- `enCurrentNPUStream`（:772-800）：入队按 task_stream 选择每流 repo；task_stream 与当前流为外部流均被拒（"External NPU stream is not supported by task queue enqueue."）。
- 事件面：NPUEvent 析构（NPUEvent.cpp :50-58）per-stream 下强制 `QueryAndDestroyEvent`；`NPUEvent::block`（:125-131）在（per-stream 或 IPC 事件）下以 10us 自旋等 `IsEventRecorded` 为真才 launch wait；`NPUEventManager::QueryAndDestroyEvent`（:38-47）per-stream/IPC 分支改用 recorded+waited 状态轮询（不再走 AclQueryEventRecordedStatus/WaitStatus），`LazyDestroy`（:68-75）仅 `IsExistCreateEventExWithFlag() && !per-stream && !IPC` 才立即销毁；NPUGuardImpl 的 record-wait 忙等（:185-190）、queryEvent 先查 recorded（:204-207）、synchronizeEvent 忙等（:230-236）同型。发布同型消费者锚：NPUEvent.cpp :61/:137、NPUEventManager.cpp :41/:70、NPUGuardImpl.cpp :126/:169（rg 行锚）。

**TASK_QUEUE_ENABLE 页逐句**：默认 1、{0,1,2} 硬校验、ASCEND_LAUNCH_BLOCKING=1 关闭——均与前文缓存链一致。Level 1 两级流水对应四个 OpCommand 入口（:153/:193/:239/:289 的 `!stream.isSyncLaunchStream() && GetTaskQueueEnable()` 门）与 AsyncTaskQueueInterface 的 copy/event 任务同型门（:94/:138/:203）；同步 launch 流不进入队。0 与 1 都使能队列、宏走 V1，「0 和 1 不等于行为相同」沿用宏表边界。

**「Level 2 将 workspace 相关任务迁移至二级流水」的静态对应**：op-plugin `EXEC_NPU_CMD_V2`（主线 d84e9b1d op_api_common.h :425-495）入队线程只做 CopyTypesV2、AIC/AIV 核数快照与 deterministic 快照；`workspace_size` 查询（getWorkspaceSizeFunc 调用）与 `unsafe_empty_workspace(workspace_size, acl_stream)` 分配都发生在**延迟 acl_call lambda 内**，由二级流水线程执行。V1（:343-395）在宏展开线程先查 workspace size、先分配（:366-388），lambda 只带现成 `workspace_addr/size/executor` 调 opApiFunc。发布版同型（dedc3167 ：415 lambda 内分配、:341 宏展开线程分配）。

**「仅在二进制场景生效」的静态映射**：`==2` 才触发的重路由只存在于 op-plugin `EXEC_NPU_CMD` 选择宏（主线 :490-499；发布 :435-443，见宏表）——即 aclnn 二进制算子宏族调用点。torch_npu 内 `RunOpApiV2`（OpCommand.cpp :234-283：`GetTaskQueueEnable()` 真值即入队 EXECUTE_OPAPI_V2，enqueue 锚 :248）由 inductor static_launcher/runtime.cpp、inductor/dvm/pybind_api.cpp、npu/Module.cpp 的 reselect_static_kernel 调用，**1/2 都走 V2 型入队**，不因 ==2 改变。因此「Level 2 语义」静态上等于「EXEC_NPU_CMD 宏重路由 + 读队列空轮询」，覆盖面以该宏调用点为限，不外推为所有下发路径在 ==2 有独立行为。

**读队列空轮询**：`Repository::ReadQueue`（主线 NPUQueue.cpp :426-440）在 `task_queue_enable == 2` 且队列空时，读线程至多 `READ_QUEUE_POLL_MAX_LOOP`（=200000，NPUQueue.h :56）次忙轮询（源注释称约 1ms）等待新任务；1/0 队列空直接返回。发布同型（NPUQueue.cpp :429-431、NPUQueue.h :38）。

**文档侧运行时断言（本卡不证实）**：TASK_QUEUE_ENABLE=2「由于内存并发可能导致 NPU 内存峰值上升」——方向与 V2 的 workspace 在二级线程并发申请、主线程继续提交的结构一致，但不静态证明；「默认一个 device 对应一个 task_queue，多线程多流经同一 queue 串行下发，依赖倒置可形成死锁」——per-device 单队列与 per-stream 队列的形状在 enCurrentNPUStream 与 PER_STREAM_QUEUE 机制中静态可见，死锁场景是运行时次序指导，记为文档侧声明。两页的型号支持矩阵（含 950DT）为文档侧产品声明，不据此外推实现行为。

## PER_STREAM_QUEUE 相关来源

- [op_execution/PER_STREAM_QUEUE.md @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/PER_STREAM_QUEUE.md)（primary；:1-44 全文）
- [op_execution/TASK_QUEUE_ENABLE.md @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/TASK_QUEUE_ENABLE.md)（primary；:1-63 全文）
- [主线 NPUStream.cpp @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUStream.cpp)（implementation；:455-495、:636-668、:770-800 连续窗；rg 锚 :469/:638/:772/:867）
- [发布版 NPUStream.cpp @f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUStream.cpp)（implementation；:355-380 连续窗，per-stream 分支无外部流检查的差异窗）
- [主线 NPUEvent.cpp @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUEvent.cpp)（implementation；:45-90、:120-145 连续窗）
- [发布版 NPUEvent.cpp @f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUEvent.cpp)（implementation；:130-142 连续窗同型 block 忙等）
- [主线 NPUEventManager.cpp @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUEventManager.cpp)（implementation；:30-75 连续窗）
- [发布版 NPUEventManager.cpp @f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUEventManager.cpp)（implementation；:38-46、:68-74 连续窗同型）
- [主线 NPUGuardImpl.cpp @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/impl/NPUGuardImpl.cpp)（implementation；:125-140、:185-240 连续窗）
- [主线 NPUQueue.cpp @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUQueue.cpp)（implementation；:415-470 ReadQueue 连续窗，==2 空轮询）
- [发布版 NPUQueue.cpp @f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUQueue.cpp)（implementation；:429-431 rg+同型确认）
- [主线 NPUQueue.h @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUQueue.h)（implementation；:56 READ_QUEUE_POLL_MAX_LOOP=200000 锚）
- [发布版 NPUQueue.h @f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUQueue.h)（implementation；:38 同值锚）
- [主线 AsyncTaskQueueInterface.cpp @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/interface/AsyncTaskQueueInterface.cpp)（implementation；:85-145、:195-235 连续窗，copy/event 任务入队门 + ExecuteParasOpApiV2）

已列来源的扩展阅读窗（不新增条目）：主线 OpCommand.cpp 增读 :228-262（RunOpApiV2 体与 EXECUTE_OPAPI_V2 入队）；op-plugin 主线 op_api_common.h 增读 :343-400（V1：宏展开线程 workspace 查询/分配）、:425-500（V2：lambda 内 workspace + EXEC_NPU_CMD 选择宏）；op-plugin 发布版 op_api_common.h 增读 :388-398（V2 lambda 内 workspace 分配）并以 rg 确认 :341/:415 分工同主线。

## PTA 执行计划缓存：EXEC 宏内的命中层

EXEC_NPU_CMD_V1/V2 在两阶段下发之前还各有一层 PTA 执行计划缓存查找。该层不属于 [兼容宏指南](torch_npu_opplugin_adaptation.md) 的 DO_COMPATIBILITY 符号回退，也不受 TASK_QUEUE_ENABLE 的 V1/V2 重路由影响——两版宏各自先试缓存、未命中才落回本卡前文的两阶段流水：

| 调用点 | 静态位置与线程 |
| --- | --- |
| V1 `hit_cache` | 主线 op_api_common.h :373（宏展开线程，`CaptureDeterministicSnapshot` 之后）；发布 :327。函数体主线 :172-230、发布 :145 起 |
| V2 `hit_cache_v2` | 主线 :452（延迟 `acl_call` lambda 内，二级流水线程上，消费 `CopyTypesV2` 副本）；发布 :399。函数体主线 :233-291、发布 :201 起 |

两 pin 的 v2 签名不同：主线携带 `DeterministicSnapshot` 并用 `SetPTACacheHashKey`；发布携带 `bool deterministic_status` 并用 `SetPTAHashKey`，不能把任一侧的符号名混同到另一 pin。

**准入与未命中边界**：命中层要求 `PTAGetExecCache/PTAFindExecCache`、`InitPTACacheThreadLocal` 与 `SetPTAHashKey/SetPTACacheHashKey` 符号齐备，且 libopapi 侧 `CanUsePTACache(aclnn_api)` 为真；任一不满足直接返回 false 落回完整两阶段（GetWorkspaceSize→workspace 分配→执行），既不是报错也不是 acl_op 回退。`CanUsePTACache` 的白名单完全在 libopapi.so 内部，本卡只读 op-plugin 宏层，不据此断言任何具体算子已启用缓存，也不给出命中率的性能承诺。

**键构成（宏层可静态核对的部分）**：先 `InitPTACacheThreadLocal` 并把 `g_hash_offset` 归零，再依次序列化 deterministic 级别、核心控制开启时的 AIC/AIV 线程资源数、算子名、全部实参、device 与流指针。V1 经 `calc_hash_id()`（主线 op_api_common.cpp :749、发布 :765）把缓冲折成单键交给 `SetPTAHashKey(hashId)`；V2 把整个哈希缓冲交给 `SetPTACacheHashKey(buf, len)`/`PTAFindExecCache(buf, len, &workspace_size)`，缓冲写满（`g_hash_offset == g_hash_buf_max_size`）时改交空键。张量实参进入键的是 sizes/dtype/strides/storage_offset/storage 形状与 NPU format（`add_param_to_buf(const at::Tensor&)`，主线 .cpp :233-275、发布 :241 起），存储数据指针不写入键，而是经 `AddTensorAddrToCachedList` 交给 libopapi 侧存活跟踪；scalar 包成张量的实参直接把 `g_hash_offset` 顶满、当次放弃键。未定义张量只写分隔符。哈希内核为 `gen_hash`（主线 .cpp :613、发布 :643）。

**命中后的执行形态**：executor 与 workspace 大小都来自缓存，跳过 `GetWorkspaceSize` 与 `ConvertTypes` 参数派生；V1 在 `RunOpApiV2` 包装的 acl_call 里直接 `opApiFunc(workspace_addr, workspace_size, executor, acl_stream)`，V2 在延迟 lambda 内同样直发，命中路径不再重建 acl 参数。两者结尾 `UnInitCacheThreadLocal()` 恢复线程本地状态。.cpp 侧另有同族执行上下文辅助（`InitExecCommonCtx`、`GetCacheExecutor/GetCacheExecutorV2`、`ExecuteCachedOp/ExecuteCachedOpV2`，主线 .cpp :1584/:1768/:1753/:1782/:1808、发布 :1799/:1841 附近）供非宏调用面复用；本节只列位置，未逐一展开其调用者，不把宏路径的结论外推给这些入口。

**与更新类宏的关系**：主线独有的 `EXEC_UPDATE_NPU_NO_FORMAT_CHECK_CMD_V1`（op_plugin/utils/custom_functions/opapi/update_op_api_common.h）只做 `InitPTACacheThreadLocal` 并 `SetPTAHashKey(0)` 重置键后走完整两阶段，不做缓存查找；不能把更新路径当成同样的命中复用，也不能由它推论缓存层对 in-place 更新算子失效。

**验证与边界**：分析命中行为时记录算子名、实参（含张量 sizes/strides/offset/format 与 storage 形状）、deterministic 级别、核心控制状态、device、流指针与 V1/V2 归属；V2 的跨线程副本与键缓冲写满是两类独立的失效源。命中只省去 host 侧派生步骤，不改变算子语义；设备侧数值、缓存淘汰与真实收益需要实测，本卡不新增 verified。

## 补充来源

- [主线 op_api_common.cpp @d84e9b1d](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp)（implementation；:233-275 张量键序列化、:613 gen_hash、:749 calc_hash_id、:1584/:1753/:1768/:1782/:1808 执行上下文与缓存执行辅助）
- [发布版 op_api_common.cpp @dedc3167](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.cpp)（implementation；:241 起张量键序列化、:643 gen_hash、:765 calc_hash_id、:1799/:1841 缓存执行辅助）
- [主线 update_op_api_common.h @d84e9b1d](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/opapi/update_op_api_common.h)（implementation；:23-88 V1 更新宏的 PTA 键重置窗）
