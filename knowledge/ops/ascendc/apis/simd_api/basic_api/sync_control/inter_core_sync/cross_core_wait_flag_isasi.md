---
type: API
title: CrossCoreWaitFlag
description: 核间同步场景中阻塞本核后续指令下发，直到所有参与同步的核均调用CrossCoreSetFlag上报完成后解除阻塞。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/inter_core_sync/CrossCoreWaitFlag_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# CrossCoreWaitFlag

头文件路径为："basic_api/kernel_operator_block_sync_intf.h"。

在核间同步场景中，CrossCoreSetFlag接口和CrossCoreWaitFlag接口配对工作，具体功能

参数：modeId: 核间同步的模式。不同产品对同步模式的支持情况请参见modeId支持的取值说明。 各个模式支持的对应Kernel类型请参照表3。；pipe: 设置这条指令所在的流水类型。支持的流水类型为PIPE_V、PIPE_M、PIPE_MTE1、PIPE_MTE2、PIPE_MTE3、PIPE_FIX，不支持PIPE_S和PIPE_ALL。不同产品对流水类型的支持情况请参见pipe支持的流水类型说明。；flagId(输入): 核间同步的标记。不同产品对flagId的取值范围说明请参见flagId取值范围说明。

约束：- 由于当Kernel类型为KERNEL_TYPE_AIC_ONLY或KERNEL_TYPE_AIV_ONLY时，硬件不会开启调度模块，也就无法正常进行核间同步，因此不同的同步模式配置Kernel类型或函数修饰符的情况
    - 在纯Vector/Cube场景下（模式0或模式1），建议设置Kernel类型为KERNEL_TYPE_MIX_AIV_1_0或KERNEL_TYPE_MIX_AIC_1_0，其它支持的Kernel类型
    - 对于Vector和Cube混合场景（模式2和模式4），需根据AI Core中AIC和AIV的比例灵活配置Kernel类型，不同模式支持的函数修饰符和Kernel类型请参照表3。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [A5 mix(1,2) mode=2 漏 AIV1 flag 致全零](../../../../../runbooks/precision/a5_mix_1_2_mode_2_aiv1_flag.md)（`exemplifies`）：A5 mix(1,2) mode=2 漏 AIV1 flag 致全零 与《CrossCoreWaitFlag》的实质衔接是：mix(1,2) 的 AIC/AIV flag 路由依赖 CrossCoreSet/Wait、kernel type 与组间同步契约；所选卡覆盖同一断链和死锁机制。
- [CrossCore 反压 flag 方向错致通算流水死锁](../../../../../runbooks/compilation/crosscore_flag.md)（`exemplifies`）：CrossCoreWaitFlag：CrossCoreWaitFlag 必须与 CrossCoreSetFlag 成对，并依赖核间同步 workspace/flag 编号约定；两个 runbook分别给出方向和双 AIV subBlock 契约的可执行诊断。 目标卡《CrossCore 反压 flag 方向错致通算流水死锁》补充：MC2 通算融合算子（Pattern B 先计后通、AIC 写大容量 GM、AIV 读）从数据流反向的基底工程照搬 AIC WaitFlag(t-buf)+AIV SetFlag(t-buf) 反压，在 tileCnt>bufferSize 时形成 AIC t↔AIV t 循环等待死锁。判别=画出 t 与 t-bufferSize 的 flag 依赖图，出现 AIC t↔AIV t 互等即循环依赖。根因是反压方向与数据流不匹配，且 cG
- [双AIV CrossCoreFlag 的 subBlock 契约缺陷](../../../../../runbooks/compilation/aiv_crosscoreflag_subblock_507015.md)（`exemplifies`）：CrossCoreWaitFlag：CrossCoreWaitFlag 必须与 CrossCoreSetFlag 成对，并依赖核间同步 workspace/flag 编号约定；两个 runbook分别给出方向和双 AIV subBlock 契约的可执行诊断。 目标卡《双AIV CrossCoreFlag 的 subBlock 契约缺陷》补充：Ascend950 双 AIV 融合 kernel 中，AIC 为 V0/V1 设置不同 flag 段，而 AIV wait 未按 subBlock 偏移，且空分支可能不回传 flag；源码依赖图可确认同步缺陷，但单独修正后 507015 仍存在，不能把整起异常只归因于该缺陷。
- [算子适配说明](../../../../../guides/programming_guide/advanced_programming/super_kernel/operator_adaptation.md)（`explains`）：算子适配说明 与《CrossCoreWaitFlag》的实质衔接是：SuperKernel 适配要求算子 block 数、SK_BIND、核间 flag 与缓存可见性匹配；原理、流程和 mix-mode 失败案例给出可执行约束。
- [InitDetermineComputeWorkspace](init_determine_compute_workspace.md)（`related`）：CrossCoreWaitFlag：CrossCoreWaitFlag 必须与 CrossCoreSetFlag 成对，并依赖核间同步 workspace/flag 编号约定；两个 runbook分别给出方向和双 AIV subBlock 契约的可执行诊断。 目标卡《InitDetermineComputeWorkspace》补充：基于核间顺序执行的确定性计算初始化接口，初始化GM共享内存后才能调用WaitPreBlock和NotifyNextBlock完成核间顺序执行。
- [核间同步](inter_core_sync.md)（`related`）：CrossCoreWaitFlag：CrossCoreWaitFlag 必须与 CrossCoreSetFlag 成对，并依赖核间同步 workspace/flag 编号约定；两个 runbook分别给出方向和双 AIV subBlock 契约的可执行诊断。 目标卡《核间同步》补充：核间同步接口索引页，汇总IBSet、IBWait、SyncAll、CrossCoreSetFlag/WaitFlag(ISASI)及NotifyNextBlock/WaitPreBlock。
- [核间同步能力概述](inter_core_sync_overview.md)（`related`）：CrossCoreWaitFlag：CrossCoreWaitFlag 必须与 CrossCoreSetFlag 成对，并依赖核间同步 workspace/flag 编号约定；两个 runbook分别给出方向和双 AIV subBlock 契约的可执行诊断。 目标卡《核间同步能力概述》补充：核间同步的使用场景通常是：一个核计算所依赖的数据，需要等待其他相关核的计算全部完成后才能获取。
- [CrossCoreSetFlag](cross_core_set_flag_isasi.md)（`same_topic`）：CrossCoreWaitFlag：CrossCoreWaitFlag 必须与 CrossCoreSetFlag 成对，并依赖核间同步 workspace/flag 编号约定；两个 runbook分别给出方向和双 AIV subBlock 契约的可执行诊断。 目标卡《CrossCoreSetFlag》补充：核间同步场景中向调度模块上报本核前置pipe流水任务已完成，与CrossCoreWaitFlag配对使用，通过flagId控制核间同步。
- [关键特性说明](key_features.md)（`same_topic`）：关键特性说明 与《CrossCoreWaitFlag》的衔接是：CrossCoreSet/CrossCoreWait 是该四种跨核同步模式的实际发信与等待原语；AIV/AIC 配对 runbook 给出同一计数契约失配时的可执行排查。
<!-- cannbot:related:end -->
