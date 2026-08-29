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
updated_at: '2026-08-27T12:23:11Z'
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

- [双AIV CrossCoreFlag 的 subBlock 契约缺陷](../../../../../runbooks/compilation/aiv_crosscoreflag_subblock_507015.md)（`exemplifies`）：焦点卡说明“AIC 只 set 1 次 `8+countId` 被 V0 消费，V1 也 wait `8+countId` 但 AIC 不会再 set 第二次 → V1 永久阻塞”，候选卡说明“在核间同步场景中，CrossCoreSetFlag接口和CrossCoreWaitFlag接口配对工作，具体功能”；配对合同能直接解释全核同 PC timeout 的形成链。
- [稀疏反卷积精度误差源隔离配方](../../../../../runbooks/precision/cube_simt_fp32_precision_error_source_isolation.md)（`exemplifies`）：“CrossCoreWaitFlag<0x4>(flagId);”是被诊断代码的等待动作；“由于当Kernel类型为KERNEL_TYPE_AIC_ONLY或KERNEL_TYPE_AIV_ONLY时，硬件不会开启调度模块，也就无法正常进行核间同步”给出该等待能生效的 Kernel 类型前提，可用于核验 Cube 结果到 AIV ScatterAdd 的同步配置。
- [CrossCoreSetFlag](cross_core_set_flag_isasi.md)（`related`）：“在核间同步场景中，CrossCoreSetFlag接口和CrossCoreWaitFlag接口配对工作，具体功能”与“在核间同步场景中，CrossCoreSetFlag接口和CrossCoreWaitFlag接口配对工作，使用时需传入核间同步的标记ID（flagId），每个ID对应一个用于控制同步的计数器。”是双方正文中的具体合同。Wait 卡声明两接口必须成对，Set 卡给出共享 flagId 计数器以及上报/阻塞职责；阅读两端才能闭合核间同步的生产与等待链。
<!-- cannbot:related:end -->
