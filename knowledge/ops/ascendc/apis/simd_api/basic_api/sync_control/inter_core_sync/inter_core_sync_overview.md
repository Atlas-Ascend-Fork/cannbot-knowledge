---
type: API
title: 核间同步能力概述
description: 核间同步的使用场景通常是：一个核计算所依赖的数据，需要等待其他相关核的计算全部完成后才能获取。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/inter_core_sync/inter_core_sync_overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 核间同步能力概述

核间同步的使用场景通常是：一个核计算所依赖的数据，需要等待其他相关核的计算全部完成后才能获取。

在核间同步场景中，CrossCoreSetFlag接口和CrossCoreWaitFlag接口配对工作，使用时需传入核间同步的标记ID（flagId），每个ID对应一个用于控制同步的计数器。 - CrossCoreSetFlag：AI Core中的AIC/AIV在完成本核前置位的pipe流水任务后，调用该接口，向调度模块上报本核任务已完成。调度模块收集所有参与核的上报信息，作为全局完成标志。 - CrossCoreWaitFlag：用于阻塞本核后续指令的下发（已下发指令可正常执行），直至调度模块确认所有应调用CrossCoreSetFlag的核均已上报完成，随即解除阻塞，允许该核继续下发指令。 如图1所示（图中block代表AIC，sub_block代表AIV），同步控制分为以下几种模式： - 模式0：AI Core核间的同步控制。对于AIC场景，同步所有的AIC核，直到所有的AIC核都执

本接口组包含 CrossCoreSetFlag, CrossCoreWaitFlag, IBSet, IBWait, SyncAll。

本接口属于同步控制接口，用于核间或流水线同步。

约束：由于当Kernel类型为KERNEL_TYPE_AIC_ONLY或KERNEL_TYPE_AIV_ONLY时，硬件不会开启调度模块，也就无法正常进行核间同步，因此不同的同步模式配置Kernel类型或函数修饰符的情况如下：；在纯Vector/Cube场景下（模式0或模式1），建议设置Kernel类型为KERNEL_TYPE_MIX_AIV_1_0或KERNEL_TYPE_MIX_AIC_1_0，其它支持的Kernel类型请参考表3。；对于Vector和Cube混合场景（模式2和模式4），需根据AI Core中AIC和AIV的比例灵活配置Kernel类型，不同模式支持的函数修饰符和Kernel类型请参照表3。；表3 模式与支持的Kernel类型配置

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [per-core zero-out 经 grid-stride ZeroOutS](../../../../../runbooks/precision/per_core_zero_out_grid_stride_zeroout_simt_overshoot.md)（`exemplifies`）：per-core zero-out 经 grid-stride ZeroOutS 与《核间同步能力概述》的实质衔接是：该故障由 ZeroOutSimt 使用 blockIdx/gridDim 的跨核 grid-stride 导致；SIMT builtin、block 数接口与 SyncAll 共同解释索引越界和回退同步要求。
- [单 rank mock HCCL 致 AIC+AIV SyncAll 死锁](../../../../../runbooks/compilation/rank_mock_hccl_aic_aiv_syncall.md)（`exemplifies`）：单 rank mock HCCL 致 AIC+AIV SyncAll 死锁说明atcoss BlockPrologueAllGather 等 AIC+AIV 通算融合 kernel 在单 rank mock HCCL context 下执行超时，mock 不提供 SyncAll 跨核配对所需的状态标志写入流程致 ReadStatus/SyncAll 死锁；该 mock 路线 banned，分布式融合 kernel 须用真实多卡 HCCL。
- [双AIV CrossCoreFlag 的 subBlock 契约缺陷](../../../../../runbooks/compilation/aiv_crosscoreflag_subblock_507015.md)（`exemplifies`）：双AIV CrossCoreFlag未按subBlock偏移致507015死锁说明Ascend950/DAV_3510 上 __mix__(1,2)=1AIC+2AIV 双 AIV 融合算子（GroupedMatmul Blaze G-B FP8）运行报 507015=ACL_ERROR_RT_AICORE_EXCEPTION，plog 呈现所有核停在同一 PC、timeout or trap、subErrType 0x4、cube error info=0（非 MMAD 越界）。判别=取 plog grep 出 sqe_type/errorStr/subErrType/PC + 按 core id 区分 AIC/AIV + 核对 gen_data.py 的 M<E 空 group 与 curM 奇数致 V1 localRows=0 + 比对 kernel AIV 侧 CrossCoreWaitFlag 是否按 GetSubBlockIdx()*FLAG_ID_MAX 偏移区分 V0/V1。根因=AIC 每 K-block set 两个 flag(8+countId 给 V0、24+countId 给 V1)但 AIV 侧 V0/V1 都 wait 同一 8+countId，AIC 只 set 1 次被 V0 消费，V1 永久阻塞；叠加 epilogue localRows<=0 early return 不发 AIV→AIC flag，AIC 也等 V1 的 flag，互锁全核 timeout。
- [核间负载均衡](../../../../../guides/operator_practice/simd_operator_optimization/tiling_strategy/inter_core_load_balance.md)（`explains`）：核间负载均衡 与《核间同步能力概述》的实质衔接是：核间负载均衡通过调整拖尾核与 block 数减少尾部空闲，并与核间同步、DoubleBuffer/异步 Iterate 和具体 Matmul/Philox 分块约束共同决定并行度。
- [CrossCoreSetFlag](cross_core_set_flag_isasi.md)（`related`）：核间同步能力概述说明核间同步的使用场景通常是：一个核计算所依赖的数据，需要等待其他相关核的计算全部完成后才能获取。
- [CrossCoreWaitFlag](cross_core_wait_flag_isasi.md)（`related`）：CrossCoreWaitFlag：CrossCoreWaitFlag 必须与 CrossCoreSetFlag 成对，并依赖核间同步 workspace/flag 编号约定；两个 runbook分别给出方向和双 AIV subBlock 契约的可执行诊断。 目标卡《核间同步能力概述》补充：核间同步的使用场景通常是：一个核计算所依赖的数据，需要等待其他相关核的计算全部完成后才能获取。
- [IBWait](ib_wait.md)（`related`）：核间同步能力概述说明核间同步的使用场景通常是：一个核计算所依赖的数据，需要等待其他相关核的计算全部完成后才能获取。
- [同步控制](../../../c_api/sync/sync_control.md)（`related`）：同步控制 与《核间同步能力概述》的实质衔接是：该同步总览按核内、核间、任务间和 SIMT fence 划分选择，所选卡解释这些同步域的边界。
- [系统同步能力概述（同步控制）](../system_sync_overview.md)（`related`）：系统同步能力概述（同步控制） 与《核间同步能力概述》的实质衔接是：系统同步能力按核内、核间、任务间分层；这些概述提供选择同步域所需的边界，而非把所有同步 API 机械串联。
- [SyncAll](sync_all.md)（`same_topic`）：核间同步概览解释 SyncAll 的参与核、workspace 和阻塞语义，是正确放置全核屏障的机制背景。
- [关键特性说明](key_features.md)（`same_topic`）：关键特性说明 与《核间同步能力概述》的衔接是：CrossCoreSet/CrossCoreWait 是该四种跨核同步模式的实际发信与等待原语；AIV/AIC 配对 runbook 给出同一计数契约失配时的可执行排查。
<!-- cannbot:related:end -->
