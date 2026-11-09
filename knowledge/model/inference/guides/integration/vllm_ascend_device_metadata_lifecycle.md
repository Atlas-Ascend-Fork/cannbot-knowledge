---
type: Guide
title: vLLM Ascend 设备元数据生命周期：TargetDeviceMetadata、阶段等待与捕获收尾
description: 沿 TargetDeviceMetadata、DeviceMetadataExecutor 和 wait_for_device_metadata 核对设备生产任务、阶段与分组等待、缓冲复用、目标与草稿隔离，以及 eager、FULL 捕获和重放的收尾责任。
aliases:
- TargetDeviceMetadata
- DeviceMetadataExecutor
- DeviceMetadataTask
- DeviceMetadataStage
- DeviceMetadataTaskProvider
- wait_for_device_metadata
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.attention
- topic.graph_execution
- topic.performance.analysis
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/device_metadata.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/aclgraph_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_device_metadata.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_graph_device_metadata.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_states/default.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_runner.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
created_at: '2026-11-02T06:28:05Z'
updated_at: '2026-11-02T06:28:05Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 设备元数据生命周期：TargetDeviceMetadata、阶段等待与捕获收尾

## 接入任务与版本范围

新模型把 Attention、Compressor 或 Indexer 的元数据生产移到设备辅助流时，需要同时建立输入就绪、消费者等待和下一步缓冲复用三种依赖。元数据对象已经返回、地址没有变化，以及 Python forward 已经返回，都不能单独证明设备任务已完成。本卡沿框架任务生命周期核对这些依赖；具体字段和缓存地址仍由各模型 builder 与消费者定义。

Main 固定 ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2：全文阅读 device_metadata.py 252 行、MRv2 aclgraph_utils.py 322 行、两个 UT 文件 500/92 行、DefaultModelState 579 行和一行版本 pin；regular ModelRunner 只读 502–555、650–693 行。Main 配对 Native pin 为 544f182d9f0c9bfe8bd7645525951d5e3692a542，独立 Native 快照 5df63a7203cdb9328d824a27b682e77c7b9928be 不是该配对提交。这里没有闭合父类图管理器、所有 builder、设备算子或完整硬件支持表，保持 draft、空平台和 framework=vllm 的部分 Scope。

抽象模型状态入口复用 [ModelState 协议](../../concepts/frameworks/vllm_model_state_protocol.md)，通用图 dispatch 与参数更新复用 [ACLGraph 生命周期](../../concepts/frameworks/vllm_ascend_aclgraph_replay_lifecycle.md)。本卡新增的是设备元数据生产与消费的执行边界，不将已有模型字段或通用图机制重新定义一遍。

## 任务、阶段和对象身份

DeviceMetadataStage 的顺序是 COMPRESSOR=0、ATTENTION=1、INDEXER=2。DeviceMetadataTask 是 frozen/slotted dataclass，携带 stage、无参 run callable 和 group_id。Executor 以 `(stage, group_id)` 标识一个消费者等待前沿；同一整数出现在不同 stage 时仍是两个键。

DeviceMetadataTaskProvider 声明 enable_device_metadata 与 take_device_metadata_tasks，但 TargetDeviceMetadata.build 的实际选择条件是 builder 有 defer_device_metadata 属性，并按 builder 对象 id 去重；它不是逐个做该 Protocol 的运行时校验。builder 取自每个 AttentionGroup 的 get_metadata_builder(0)，不能据此推导所有下标或额外 builder 都被遍历。

group_id 的生成要与实际消费者一致。已有压缩器等待自己的 compressor_metadata_group_id，Indexer 按 QLI metadata 对象身份等待；它们并非可互换的全局层号。字段、shape 和组间关系分别见[压缩器接线](vllm_ascend_compressor_state_cache_contract.md)、[V4 Indexer](vllm_ascend_v4_indexer_contract.md)与[SFA 地址视图](vllm_ascend_sfa_replicated_cache_views.md)。

## submit：输入就绪、阶段顺序与缓冲复用

每个 DeviceMetadataExecutor 拥有独立 NPU stream、输入就绪事件、普通阶段事件、按 batch descriptor 区分的 ExternalEvent、缓冲复用事件，以及当前提交和已等待前沿的状态。默认 capture_producers=False；TargetDeviceMetadata 则明确创建 capture_producers=True 的实例。

submit 拒绝未 release 的前次提交和空任务集，也拒绝 capture_producers=True 同时传入 batch_descriptor。任务先按 stage 排序；ATTENTION 任务再按已学习的首次消费顺序排序，未知组放在已知组之后并保持稳定次序。其他 stage 内保持输入次序。这种排序意图降低生产与消费顺序错位，不能据源码给出重叠收益数值。

ExternalEvent 路径首次记录该 descriptor 的 `(stage, group_id)` 集合；再次提交时要求集合完全一致，否则在新事件分配和提交前报错。这个检查比较的是集合，不验证任务数量、重复项、callable 身份或完整执行顺序均相同。不同 descriptor 有独立事件键，不能用同一桶的事件绑定任意新增分组。

事件按键按需创建后，Executor 标记 submission_in_flight，清空本次已等待集合，在当前主流 record 输入就绪事件；生产流先等它。普通生产路径若已有复用 fence，再等前次 release 记录的缓冲可复用事件，然后按阶段调用 task.run，每项调用之后记录其就绪事件。

capture_producers=True 路径不等待旧的缓冲复用 fence；来源依靠生产、消费和 join 都进入同一捕获图，以及下一次主流输入就绪节点建立顺序。不能把普通路径的 fence 删除后假定得到同样语义，也不能将图中有事件理解为 host 已同步完成。

调用方仍需提供合法 stage 与 group 键。这里没有完整输入 schema，也不自动验证每个自定义 callable 的输出布局、持久缓冲或 stream 行为。task.run 中途抛异常时，直接调用 Executor 的一方可能看到部分提交和 in-flight 状态；底层 submit 本身不负责全部恢复。

## wait 与 release：消费就绪和复用是两项责任

wait 必须有正在执行的提交。普通路径让当前 stream 等待 `(stage,group_id)` 的事件；ExternalEvent 路径执行 wait 后 reset。每个前沿本次只等待一次，ATTENTION 的首次消费顺序还会跨 batch shape 保留下来，用于后续生产排序。错误或缺失的 group 键不能由别的组“代等”。

release 同样要求有 in-flight 提交。普通路径在当前主流 record 缓冲复用事件并标记 fence 存在；捕获生产路径跳过该 fence；随后清除 in-flight 和本次 descriptor。release 不自动逐项等待所有 producer，也不等价于全设备同步。裸 Executor 调用方必须先保证其消费者与剩余任务已经接回主流。

TargetDeviceMetadata.finish 提供补齐责任：如果仍在执行，对本次每项任务调用 wait，再 release，最后清空任务。已经消费的前沿因去重不会重复插入等待；dummy 路径中尚无消费者的 producer 也会被 join。只等待最后一次实际 Attention，而忽略未消费的 Compressor/Indexer 任务，会破坏下一步复用输入的条件。

## forward context 与目标、草稿隔离

wait_for_device_metadata 在没有 forward context 时直接返回；有 context 时先取 context.device_metadata_executor。该属性不存在或为 None 时，若 attn_metadata 是 dict，只查看第一个 metadata resource 的 device_metadata_executor。它没有扫描全部 resource，也没有全局 Executor 缓存。

TargetDeviceMetadata.run_build 在实际 build 返回后，把本次 Executor 附到每个返回的 metadata resource。调用方因此必须返回预期 mapping，且这些对象允许赋该属性；实现没有针对任意返回对象建立完整 schema 或原子回滚。混入别的执行域资源，或在 context 显式放入过期 Executor，都不能靠 fallback 自动修复。

隔离来自当前 forward 的明确 context 和 metadata 所有权。草稿应使用自己的 metadata/context，不继承目标生产作用域；仅给对象换一个类名或复用一个容器不足以证明隔离。若第一个 resource 没有 Executor，helper 不会继续寻找后面的 resource，这也是诊断“对象存在但未等待”的入口。

## build、eager 与 FULL 的提交位置

TargetDeviceMetadata.build 先拒绝 failed 状态、仍在执行的提交或未退休任务。它按对象身份去重 provider，用 ExitStack 进入 defer_device_metadata(in_graph=full_graph)，在构建完成后收集各 provider.take_device_metadata_tasks，再退出 defer context。

构建主体抛异常时会取走各 provider 的待办任务并重新抛出。该分支不构成任意 provider 进入/退出、任意属性赋值与所有资源状态都可原子回滚的保证。重试前仍需根据实际失败位置确认旧资源是否已退休。

run_build 将 full_graph_mode 或 for_cudagraph_capture 任一为真视为 full_graph。eager 路径在准备完成后调用 begin_forward；FULL 路径先保存任务，由模型捕获/预热 wrapper 在图内部调用 begin_forward。不要在 FULL host prepare 阶段另行调用 submit，否则 producer 可能落在图外而消费者在图内。

begin_forward 在无任务或已有提交时返回。提交抛出 Python 异常时，Target 标记 failed；若已处于 in-flight，当前主流 wait_stream 生产流并 release；随后清空任务、保留异常。failed 对象后续 build 明确要求重新创建目标模型状态。这个恢复只是特定生产流的 join，不是全设备或 host 同步，也未证明异步设备故障均能安全恢复。

## MRv2 wrapper 的收尾位置与接入门控

ModelWithContext.forward 设置捕获和草稿标志后，在 try 内调用 device metadata 的 begin_forward，再执行原模型，finally 调用 finish。FULL warmup/capture 因而把 producer、消费者等待与最终 join 一起纳入该路径，而不是在 forward 入口把所有 producer 全部阻塞完。

ModelAclGraphManager.capture 用该 wrapper 执行父类捕获，并在外层 finally 再次 finish，覆盖输入准备在进入 wrapper 前失败的情况。run_fullgraph 的实际 replay try/finally 使用 finish_replay：重放执行已捕获节点，host 仅清空本次待办任务，不重新提交 Python producer。finish_replay 若发现 host 侧仍有 in-flight 提交会报错，而不会静默当作已捕获路径完成。

这些 finally 需要按实际代码区间判断。run_fullgraph 在进入 replay try 前的 backend 选择和 update_stream 检查，并未被后面的 finally 全部包住；不能概括为所有准备和捕获失败都由同一分支清理。图参数更新、微批和其他资源仍需其各自协议。

regular ModelRunner 的已读 KV 初始化选段仅在 uses_a5_packed_cache() 且 architecture 精确为 DeepseekV41ForCausalLM 时，为 model_state 建立新的 TargetDeviceMetadata；其他情况设置 None。该窄门控不能扩展为全部模型或整个 A5 系列都已启用。DefaultModelState 的可选 finish_execution 负责调用其 device metadata 收尾，regular execute 用 try/finally 把 forward_failed 传给该钩子。父类 ModelState 的抽象协议与这个 Ascend 可选扩展仍是不同层次。

## Agent 的接入、诊断与验证顺序

1. 固定 Main、配对 Native、torch_npu/CANN、模型 architecture 和实际 Runner；确认对象确实在窄门控内创建，记录当前是 eager、warmup、capture 还是 replay。
2. 列出每个 provider、任务 stage/group、输入输出持久缓冲及消费者。先验证键、对象身份、metadata 顺序和上下文隔离，再检查事件；不要用共享全局 Executor 掩盖分组错误。
3. 覆盖输入尚未就绪、同组多消费者、未消费 dummy producer、跨 shape 的 Attention 次序、同 descriptor 前沿改变、不同 descriptor、前次未 release、空任务和下一步复用。
4. 分别验证 build 异常、部分 submit 失败、wrapper 前准备失败、原 forward 失败与 replay 的 host 误提交；确认应重建的 failed 目标状态得到重建，不通过清标志假装完成恢复。
5. 将多步、跨桶、target/draft 交替和混合请求结果与受控 eager 对照；数值和生命周期通过后，再比较辅助流、消费者等待、join、峰值内存与稳态时延。

两个 UT 文件使用假 Stream/Event、mock executor 和替代 callable，定义了阶段顺序、等待去重、复用 fence、ExternalEvent 前沿、跨 shape 的消费顺序、部分失败、context fallback、目标/草稿隔离、FULL 延迟提交及 capture 准备失败收尾等断言。它们不是实际 NPU 图捕获、并发流、数值或性能证明，本次也没有执行这些 UT。

如果事件挂起或结果随异步步数漂移，保留 stage/group、descriptor、provider/Executor 身份、任务次序、in-flight/failed 状态及缓冲地址/复用时间线，恢复已确认的配对和执行配置。GDN 的专有字段与图重放问题仍见[元数据接入](vllm_ascend_gdn_metadata_builder_contract.md)和[图元数据诊断](../../runbooks/precision/vllm_ascend_gdn_graph_metadata_lifecycle.md)，不能用本卡的通用任务表替代。

本次仅完成固定源码和测试定义的静态阅读，没有导入上游代码、执行 UT、编译/JIT、模型、NPU、图重放、精度、性能或 Agent A/B；未登记 verified 事件。性能收益和全硬件/全模型支持继续作为待验证边界。
