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
updated_at: '2026-08-27T12:23:11Z'
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

- [950 mix(1,2) mode=2 漏 AIV1 flag 致全零](../../../../../runbooks/precision/950_mix_1_2_mode_2_aiv1_flag.md)（`exemplifies`）：950 `__mix__(1,2)` 双 AIV CrossCore 同步必须用 mode=4；不同产品对同步模式的支持情况请参见modeId支持的取值说明。Runbook 实测 mode=2 只路由到 AIV0 并要求 950 双 AIV 改用 mode=4 加 AIV1 偏移，API 卡明确 modeId 与 Kernel 类型按产品选择，是该故障直接依赖的接口边界。
- [CrossCore 反压 flag 方向错致通算流水死锁](../../../../../runbooks/compilation/crosscore_flag.md)（`exemplifies`）：“- CrossCoreSetFlag：AI Core中的AIC/AIV在完成本核前置位的pipe流水任务后，调用该接口，向调度模块上报本核任务已完成。调度模块收集所有参与核的上报信息，作为全局完成标志。”与“为 matmul_reducescatter（MC2 通算融合，4P SHMEM ReduceScatter，Pattern B 先计后通）实现通算流水时，按改造指令给 `MatmulProcess`（AIC）和 `ReduceScatterProcess`（AIV）各加 mLoop 循环，并用 ping-pong 反压：AIC 在 `t >= bufferSize` 后 `CrossCoreWaitFlag<0x2, PIPE_FIX>(t - bufferSize)` 等 AIV 释放旧 buffer，AIV 在 reduce 后 `CrossCoreSetFlag<0x2, PIPE_MTE3>(t - bufferSize)` 通知 AIC。”提供双方正文证据。API 卡给出 SetFlag 向调度模块上报完成的正向语义；runbook 展示反压方向放错后形成循环等待的具体故障，因此后者是前者同步合同的可复现反例与排障实例。
- [双AIV CrossCoreFlag 的 subBlock 契约缺陷](../../../../../runbooks/compilation/aiv_crosscoreflag_subblock_507015.md)（`exemplifies`）：焦点卡定位到“epilogue `localRows<=0` 时仍发 `CrossCoreSetFlag` 再 return”，候选卡规定 SetFlag 会“向调度模块上报本核任务已完成”；该语义解释空分支为何也必须上报，才能解除对端等待。
- [稀疏反卷积精度误差源隔离配方](../../../../../runbooks/precision/cube_simt_fp32_precision_error_source_isolation.md)（`exemplifies`）：“CrossCoreSetFlag<0x4, PIPE_MTE3>(flagId);”是被诊断的 Cube/AIV 混合代码中的上报动作；“CrossCoreSetFlag：AI Core中的AIC/AIV在完成本核前置位的pipe流水任务后，调用该接口，向调度模块上报本核任务已完成。调度模块收集所有参与核的上报信息，作为全局完成标志。”给出其完成语义，可核对 dump 前的数据可见性和同步边界。
- [CrossCoreWaitFlag](cross_core_wait_flag_isasi.md)（`related`）：“在核间同步场景中，CrossCoreSetFlag接口和CrossCoreWaitFlag接口配对工作，具体功能”与“在核间同步场景中，CrossCoreSetFlag接口和CrossCoreWaitFlag接口配对工作，使用时需传入核间同步的标记ID（flagId），每个ID对应一个用于控制同步的计数器。”是双方正文中的具体合同。Wait 卡声明两接口必须成对，Set 卡给出共享 flagId 计数器以及上报/阻塞职责；阅读两端才能闭合核间同步的生产与等待链。
<!-- cannbot:related:end -->
