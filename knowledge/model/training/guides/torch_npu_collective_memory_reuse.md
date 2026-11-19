---
type: Guide
title: TorchNPU 训练通信内存复用：Work.wait 与引用寿命
description: 说明 MULTI_STREAM_MEMORY_REUSE 各模式、主线默认2与发布默认1的差异及解析行为，模式2下异步集合通信必须 Work.wait；核对 Work.wait 的当前流等待语义、非阻塞返回含义、引用保护与标记擦除的释放时机，并区分引用保护与业务同步。
tags:
- task.optimization
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/MULTI_STREAM_MEMORY_REUSE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/memory_management/multistream_memory_reuse.md
  role: supporting
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/MULTI_STREAM_MEMORY_REUSE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/memory_management/multistream_memory_reuse.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/disabling_multi_stream_memory_reuse.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/disabling_multi_stream_memory_reuse.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/enabling_multi_stream_memory_reuse.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/enabling_multi_stream_memory_reuse.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/ProcessGroupHCCL.hpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/register/OptionsManager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUEvent.cpp
  role: implementation
created_at: '2026-11-08T11:58:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# 训练集合通信中的跨流内存复用

## 问题与机制

异步通信使用 Tensor 后，跨流保护可能让内存池延迟回收。来源解释了在 Work.wait 下发设备等待后，后续计算已处于正确顺序，此时优化保护标记可提高内存复用。该机制与业务数据依赖相关，不能简单提前释放所有通信内存。

本卡固定 PyTorch/TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 与发布版 `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 的 `WorkHCCL::wait/synchronizeInternal`、所列普通 collective 的内存保护分支及复用配置解析；主线另核对 TensorShelf、部分后台清理和 NPUEvent 等待，不把这些局部读数推广成全部 P2P、图捕获和 allocator 的完整核对。未加载通信库、创建进程组、故障注入或测量性能；源码级结论不扩大文档承诺的平台范围。Host 阻塞开关的文档契约见 [Watchdog 与超时](torch_npu_hccl_watchdog_timeout.md)。

## 环境配置

MULTI_STREAM_MEMORY_REUSE 的固定主线默认值是 2。0 关闭优化；1 通过 eraseStream 配合弱引用；2 持有强引用并避免部分 recordStream 标记，可能延长 Tensor 寿命；3 在模式 1 基础上覆盖提前释放情形。

未设置环境变量时两版默认值不同，不能把主线文档的默认 2 自动用于发布快照：

| 固定版本 | 未配置默认值 | 实现枚举 |
| --- | --- | --- |
| 主线 ac0e1564… | 2 | AVOID_RECORD_STREAM |
| 发布版 f3ecfe4a… | 1 | ERASE_RECORD_STREAM |

首次调用后解析结果被函数内 static 永久缓存，同一进程第一次读取之后再修改环境变量不保证生效；显式 0、1、2、3 的枚举分支分别保留，整数解析落到这些值之外时抛错，非数字串的处理见解析层小节。版本升级后的显存寿命和等待行为评估，应记录真正生效的模式，而不是只记录环境变量为空；默认差异本身不证明哪种模式对所有模型更快或更省内存。

模式 2 下，返回 Work 的异步集合通信必须调用其 wait()；点对点通信的内存保护退回 recordStream 路线。不得把模式 2 的默认值理解为可以省略 wait，也不能把 Work.wait、Event 等待和 Tensor 生命周期保护互相替代。

## MULTI_STREAM_MEMORY_REUSE 解析层与 HCCL 消费面

对照本卡所持文档页核对解析与消费面行级锚。解析层 `GetMultiStreamMemoryReuse` 为函数内 static 一次性求值（主线 OptionsManager.cpp :130-154）：`get_and_log_env`+`strtol`(base10) 后按整数映射 ReuseMode{0:CLOSE, 1:ERASE_RECORD_STREAM, 2:AVOID_RECORD_STREAM, 3:ERASE_RECORD_STREAM_WITH_OPTIMIZE}（枚举主线 OptionsManager.h :27-33），越界整数 `TORCH_CHECK` "should be 0, 1, 2 or 3"。strtol 无 end 校验：非数字串静默取 0 即 CLOSE、"2x"/"02" 取 2——文档页未声明取值约束，排查时不能用「配置过即生效」推断。未配置默认主线 2（AVOID，:133）、发布 1（ERASE，发布 :59-84）。

集合通信下发/回收三态（主线 ProcessGroupHCCL.cpp，读窗 :1085-1125、:4585-4670、:6015-6075）：模式 1/3 对输入 `recordStream` 并记录弱引用 `recorded_inputs_`（:4608-4617）；模式 3 额外登记 `getBlockPtr`+`recordHcclWorkForBlock`（:4612-4616）。模式 2 对常规集合**不** recordStream，改由 `stashed_for_allocator_safety_->stash` 持强引用（输入 :4594-4604、输出 :4634-4636）——文档「持有强引用、可能延长 Tensor 寿命」的行级锚定；`TensorShelf` 内部保存 `std::vector<at::Tensor>`，因此这里是保留对象引用、避免底层存储过早被 allocator 复用，而非复制一份 Tensor 数据。`opType==UNKNOWN`（batch_isend_irecv 点对点）即使是模式 2 也回退 recordStream+弱引用记录，注释原文给出理由：该 API 不要求调用方 wait，无从得知何时可安全归还（:4597-4603）——文档「模式 2 点对点回退 recordStream」逐句锚定；独立 `pointToPoint` 的说明同样指出无法依赖 isend 调用者一定等待，不能从集合通信的 stash 行为推导全部 P2P 具有相同回收时机。输入和输出的保护分支并不完全对称，不把输入侧条件直接补到所有输出或所有通信变体。

Work 结束路径（barrier 之后）按弱引用存活与否处置：storage 存活→`eraseStream`；已死且模式 3→`eraseStreamWithBlockPtr(block_ptr, stream, work)`——文档「模式 3 在 1 基础上覆盖 Tensor 提前释放场景」的实现锚定（:1092-1104）；随后模式 1 `lazy_destroy_tensors_.clear()`、模式 2 `unstash`（:1112-1116）。展平 allgather 输出在模式 2 同样跳过 recordStream 改 stash、等待后拷回（:6024-6027、:6058-6066）。其余消费窗 rg 锚（未逐行核对）：:4827-4860、:5077-5090（coalescing 守卫 `!coalescing_state_ && mode != CLOSE`）、:5353-5365。模式 2 的「必须 wait()」条款是跨流正确性要求；Work 强引用 stash 只是分配器安全面，等待语义见下文 Work.wait 小节。

## Work.wait 首先建立调用时当前流的顺序

`WorkHCCL::wait(timeout)` 调用 `synchronizeInternal(timeout)`。后者对每个设备取**调用时的当前 NPU 流**，将本 Work 的 HCCL 结束事件 block 到该流，再做后面的内存保护清理。它不是固定只等待发起通信的那个 Python 流，也不对所有设备流自动建立统一屏障。

因此后续结果在另一条未建立依赖的流消费时，不能依赖某个别处的 wait 自动覆盖它；应按真实生产、等待和消费所在流核对。保留 Tensor 强引用只能防止存储过早复用，不能代替消费前的数据依赖。

主线 `NPUEvent::block()` 将事件等待任务下发到指定流；部分队列/IPC 情形先等事件已被记录，捕获期间还有额外处理，所以这里也不承诺调用没有任何 Host 开销。

## 非阻塞等待不保证 Host 已等通信完成

`blockingWait_` 为真时，`synchronizeInternal` 才循环检查 `isCompleted()`，处理 timeout 和异常。两版普通 wait 都在完成该函数后返回 `true`；**`true` 不是“Host 已确认设备通信成功完成”的独立证据。** 在非阻塞路径中，它可主要表示当前流已安排等待，不能直接用包围这个调用的 CPU 时钟当作完整设备通信时延。

barrier 是该函数中的例外：`barrierTensors_` 非空时执行设备同步。它不能被当成所有普通 all-reduce 都隐含设备同步的证据。`timeout` 在这里的 Host 轮询检查位于 blocking 分支；设备事件、Watchdog 和域超时仍是不同机制，不因传入一个 wait 参数就合并为同一层。

## 依赖下发后才释放保护引用或擦除标记

当前流的结束事件等待安排之后，`synchronizeInternal` 才处理 `recorded_inputs_/outputs_` 的 eraseStream，或在模式 2 对 shelf 执行 `unstash()`。模式 3 的额外 block 指针在弱引用失效时有专门路径；不能用手工提前清空引用或擦标记模拟这里的完整协议。

主线还存在后台完成 Work 把非空 shelf 交给 `shelvesToUnstash_`、后续用户调用处清理的路径。这是已完成通信的内存保护清理机制，不能替代调用方消费结果前应安排的 wait，也不保证省略 wait 时所有 Tensor 会在期望的业务边界立即回收。队列是否走到这条清理路径还受实际异步错误处理和捕获条件约束。

定位显存或重叠问题时，分别记录实际模式、Work 保留情况、wait 所在流、下游消费流、Host 阻塞配置和设备时间线。模式、异步调用或对象析构单独成立，都不能证明完成依赖、数值和稳态显存已正确。

## 图示减少的是延迟回收标记，不是业务等待

开发页的两语言PNG逐字节相同。关闭复用图在free tensor1之后另发Event3 record并等待后续查询完成，因此malloc tensor2无法及时复用；开启图移去这一步延迟回收标记，仍保留计算与HCCL之间的事件顺序。它不是允许通信尚在消费时直接把底层内存交给任意流。

图中回算流wait与通信流record的Event编号并不一致，是示意标签的边界；不能据图上编号拼出可执行等待关系，应按实际记录的事件对象和Work.wait下发依赖核对。强/弱引用、tensor析构和设备顺序分别成立，删除recordStream标记不等于删除数据依赖。本卡只查看图与两语言文字，未运行多流或多卡实验。

## 验证与回退

以真实分布式步数检查通信结果、对象释放、峰值显存及重叠。固定 shape 与并行配置，只改变复用模式，保留各 rank 的调用证据。无改善或出现错误时恢复原模式，并在安全同步下复测。来源明确支持的产品中，本卡聚焦 A2/A3 训练；版本说明来自固定主线，没有多卡运行结果。

## 版本入口

- [软件栈来源与适用性](../../inference/concepts/frameworks/ascend_software_stack_baselines.md)：来源快照、部署配套和实际运行验证分别核对。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/MULTI_STREAM_MEMORY_REUSE.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/memory_management/multistream_memory_reuse.md)（supporting）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/MULTI_STREAM_MEMORY_REUSE.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/memory_management/multistream_memory_reuse.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/disabling_multi_stream_memory_reuse.png)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/disabling_multi_stream_memory_reuse.png)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/enabling_multi_stream_memory_reuse.png)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/enabling_multi_stream_memory_reuse.png)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.cpp)（implementation；:120-154）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.h)（implementation；:27-33 ReuseMode 枚举）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp)（implementation；:1085-1125、:4585-4670、:6015-6075；rg 锚 :4827-4860/:5077-5090/:5353-5365）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/ProcessGroupHCCL.hpp)（implementation；TensorShelf 与 WorkHCCL 成员）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/register/OptionsManager.cpp)（implementation；:59-84）
- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUEvent.cpp)（implementation；NPUEvent::block）
