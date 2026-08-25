---
type: API
title: CrossCoreSetFlag
description: 核间同步场景中向调度模块上报本核前置pipe流水任务已完成，与CrossCoreWaitFlag配对使用，通过flagId控制核间同步。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/inter_core_sync/CrossCoreSetFlag_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# CrossCoreSetFlag

头文件路径为："basic_api/kernel_operator_block_sync_intf.h"。

在核间同步场景中，CrossCoreSetFlag接口和CrossCoreWaitFlag接口配对工作，使用时需传入核间同步的标记ID（flagId），每个ID对应一个用于控制同步的计数器。

- CrossCoreSetFlag：AI Core中的AIC/AIV在完成本核前置位的pipe流水任务后，调用该接口，向调度模块上报本核任务已完成。调度模块收集所有参与核的上报信息，作为全局完成标志。
- CrossCoreWaitFlag：用于阻塞本核后续指令的下发（已下发指令可正常执行），直至调度模块确认所有应调用CrossCoreSetFlag的核均已上报完成，随即解除阻塞，允许该核继续下发指令。

如图1所示（图中block代表AIC，sub_block代表AIV），同步控制分为以下几种模式

参数：modeId: 核间同步的模式，不同产品对同步模式的支持情况请参见modeId支持的取值说明。 各个模式支持的对应Kernel类型请参照表3。；pipe: 设置这条指令所在的流水类型。支持的流水类型为PIPE_V、PIPE_M、PIPE_MTE1、PIPE_MTE2、PIPE_MTE3、PIPE_FIX，不支持PIPE_S和PIPE_ALL。不同产品对流水类型的支持情况请参见pipe支持的流水类型说明。；flagId(输入): 核间同步的标记。不同产品对flagId的取值范围说明请参见flagId取值范围说明。

约束：- 由于当Kernel类型为KERNEL_TYPE_AIC_ONLY或KERNEL_TYPE_AIV_ONLY时，硬件不会开启调度模块，也就无法正常进行核间同步，因此不同的同步模式配置Kernel类型或函数修饰符的情况
    - 在纯Vector/Cube场景下（模式0或模式1），建议设置Kernel类型为KERNEL_TYPE_MIX_AIV_1_0或KERNEL_TYPE_MIX_AIC_1_0，其它支持的Kernel类型
    - 对于Vector和Cube混合场景（模式2和模式4），需根据AI Core中AIC和AIV的比例灵活配置Kernel类型，不同模式支持的函数修饰符和Kernel类型请参照表3。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [A5 mix(1,2) mode=2 漏 AIV1 flag 致全零](../../../../../runbooks/precision/a5_mix_1_2_mode_2_aiv1_flag.md)（`exemplifies`）：A5 mix(1,2) mode=2 漏 AIV1 flag 致全零说明DAV_3510 (Ascend 950) 上 __mix__(1,2) 双 AIV kernel 若沿用 A2/A3 的 CrossCoreSetFlag mode=2，AIC 发出的 flag 只路由到 AIV0，AIV1 永不收到，AIC↔AIV1 同步链断裂致输出全零。判别要点是查 mode 模板参数与 AIV1 flagId+16 偏移。
- [CrossCore 反压 flag 方向错致通算流水死锁](../../../../../runbooks/compilation/crosscore_flag.md)（`exemplifies`）：CrossCore 反压 flag 方向错致通算流水死锁 与《CrossCoreSetFlag》的实质衔接是：该死锁来自 CrossCoreSet/Wait 的 t↔t-buffer 循环依赖；同 MC2 流水、subBlock、UDMA/ReduceScatter 及核间 flag 材料共同支撑依赖图和去反压验证。
- [双AIV CrossCoreFlag 的 subBlock 契约缺陷](../../../../../runbooks/compilation/aiv_crosscoreflag_subblock_507015.md)（`exemplifies`）：故障卡的 AIC 向 V0/V1 分段发 flag 正是 CrossCoreSetFlag 上报完成契约；接口文档补充 mode、Kernel 类型、pipe 与 flagId 的合法范围。
- [算子适配说明](../../../../../guides/programming_guide/advanced_programming/super_kernel/operator_adaptation.md)（`explains`）：算子适配说明 与《CrossCoreSetFlag》的实质衔接是：SuperKernel 适配要求算子 block 数、SK_BIND、核间 flag 与缓存可见性匹配；原理、流程和 mix-mode 失败案例给出可执行约束。
- [DataSyncBarrier](../intra_core_sync/data_sync_barrier_isasi.md)（`related`）：CrossCore flag 作用于不同核，不是 DataSyncBarrier 的核内替代；同步域需严格区分。
- [SetFlag/WaitFlag](../intra_core_sync/set_flag_wait_flag_isasi.md)（`related`）：CrossCore 作用于不同核，不能替代核内流水 event。
- [SetNextTaskStart](../inter_task_sync/set_next_task_start.md)（`related`）：CrossCoreSetFlag 是核间信号而非 task 间依赖；需要跨核时应切换到对应 wait flag 机制。
- [核间同步能力概述](inter_core_sync_overview.md)（`related`）：核间同步能力概述说明核间同步的使用场景通常是：一个核计算所依赖的数据，需要等待其他相关核的计算全部完成后才能获取。
- [CrossCoreWaitFlag](cross_core_wait_flag_isasi.md)（`same_topic`）：CrossCoreWaitFlag：CrossCoreWaitFlag 必须与 CrossCoreSetFlag 成对，并依赖核间同步 workspace/flag 编号约定；两个 runbook分别给出方向和双 AIV subBlock 契约的可执行诊断。 目标卡《CrossCoreSetFlag》补充：核间同步场景中向调度模块上报本核前置pipe流水任务已完成，与CrossCoreWaitFlag配对使用，通过flagId控制核间同步。
- [关键特性说明](key_features.md)（`same_topic`）：关键特性说明 与《CrossCoreSetFlag》的衔接是：CrossCoreSet/CrossCoreWait 是该四种跨核同步模式的实际发信与等待原语；AIV/AIC 配对 runbook 给出同一计数契约失配时的可执行排查。
<!-- cannbot:related:end -->
