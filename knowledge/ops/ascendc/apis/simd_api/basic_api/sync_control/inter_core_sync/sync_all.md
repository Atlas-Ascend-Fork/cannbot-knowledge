---
type: API
title: SyncAll
description: 核间同步控制接口，支持硬件同步（全核同步）和软件同步（通过全局内存轮询指定核数同步）两种模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/inter_core_sync/SyncAll.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# SyncAll

头文件路径为："basic_api/kernel_operator_block_sync_intf.h"。

SyncAll是核间同步控制接口，根据不同的函数原型介绍其功能
- 硬件同步接口
    用于多个核之间的同步控制，支持以下同步场景
    - 纯Vector算子的全核同步，可参考CrossCoreSetFlag的模式0。
    - 融合算子的全核同步，一次性实现三个核间同步能力（参考CrossCoreSetFlag的关键特性说明）：首先完成单个AI Core内，AIC与所有AIV同步（AIC等AIV）；接着完成多个AI Core间，所有AIC的同步；最后完成单个AI Core内，所有AIV与AIC同步（AIV等AIC）。

- 软件同步接口
    仅支持纯Vector算子的多核（参与同步的核数可通过入参指定）同步。每一个AIV都向全局内存对应位置写入信号值1，接着每一个AIV都持续轮询全局内存中所有AIV对应的信号值，直到所有AIV核对应的信号值都变为1。

参数：isAIVOnly: 控制SyncAll作用于纯Vector算子或Mix（包含Cube和Vector计算）算子。可选值： • true（默认值）：纯Vector算子的全核同步，仅执行Vector核的全核同步。 • false：Mix（包含Cube和Vector计算）算子的全核同步，先分别完成Vector核和Cube核的全核同步，再执行两者之间的同步（软同步接口不支持此功能）。；config: 该配置仅当isAIVOnly=True时有效。 struct SyncAllConfig { pipe_t triggerPipe; pipe_t waitPipe; }; // 默认使用全部流水来进行触发和等待行为。 constexpr SyncAllConfig DEFAULT_SYNC_ALL_CONFIG = {PIPE_ALL, PIPE_ALL}; 控制SyncAll函数的行为，在多个AI Core之间进行流水同步时，指定哪些流水（pipe）用于触发和等待。 • triggerPipe：指定哪个流水用于“发送触发信号”。仅支持MTE2、MTE3、PIPE_ALL。 • waitPipe：指定哪个流水用于“接收等待信号”。仅支持MTE2、MTE3、PIPE_ALL。 // 多个AIV进行计算 Compute(); // 多个AIV将计算结果搬出到GM CopyToGM(); // 等待所有数据拷贝到GM后，进行累加 constexpr AscendC::SyncAllConfig CustomConfig = {PIPE_MTE3, PIPE_ALL}; AscendC::SyncAll (); for (int i = 0; i < blockNum; i++) { if (i != blockIdx) { CopyFromGm(); Accumulate(); } } // 累加后的数据写回 CopyToGm();；gmWorkspace(输入): gmWorkspace为用户定义的全局空间，作为所有核共用的缓存，用于保存每个核的状态标记，类型为GlobalTensor，支持的数据类型为int32_t。GlobalTensor数据结构的定义请参考GlobalTensor。 所需空间大小和使用注意项参见约束说明。 硬同步接口不支持该参数。；ubWorkspace(输入): ubWorkspace为用户定义的局部空间，每个核单独自用，用于标记当前核的状态。 类型为LocalTensor，支持的TPosition为VECIN、VECCALC、VECOUT，支持的数据类型为int32_t。 所需空间大小参见约束说明。 硬同步接口不支持该参数。；usedCores(输入): 指定多少个核之间的同步，传入数值不能超过算子调用时指定的逻辑numBlocks。此参数为默认参数，不传此参数表示全核软同步。 仅在软同步接口中支持，硬同步接口不支持该参数。

约束：SyncAll硬件同步和软件同步接口的内部实现不同，约束条件也有所区别。

- 软件同步接口约束
    - gmWorkspace缓存申请的空间大小要求大于等于GetBlockNum()*32Bytes，并且缓存的值需要初始化为0。目前常见的有两种初始化方式
        - 通过在host侧进行初始化操作，确保传入该接口时，gmWorkspace缓存已经初始化为0；
        - 在kernel侧初始化的时候对gmWorkspace缓存初始化，需要注意的是，每个核上都需要初始化全部的gmWorkspace缓存空间。
    - ubWorkspace申请的空间大小要求大于等于GetBlockNum()*32Bytes。

平台差异：软同步以及不支持config指定流水的硬同步原型支持Ascend 950PR/950DT、Atlas A3和Atlas A2；支持config指定流水的硬同步原型仅支持Ascend 950PR/950DT。

<!-- cannbot:related:start -->
## 相关

- [per-core zero-out 经 grid-stride ZeroOutS](../../../../../runbooks/precision/per_core_zero_out_grid_stride_zeroout_simt_overshoot.md)（`exemplifies`）：per-core zero-out 经 grid-stride ZeroOutS 与《SyncAll》的实质衔接是：该故障由 ZeroOutSimt 使用 blockIdx/gridDim 的跨核 grid-stride 导致；SIMT builtin、block 数接口与 SyncAll 共同解释索引越界和回退同步要求。
- [单 rank mock HCCL 致 AIC+AIV SyncAll 死锁](../../../../../runbooks/compilation/rank_mock_hccl_aic_aiv_syncall.md)（`exemplifies`）：单 rank mock HCCL 致 AIC+AIV SyncAll 死锁 与《SyncAll》的实质衔接是：单 rank mock 未提供真实 HCCL 参与者，SyncAll 无法闭合；HCCL context/commit/wait 和核间同步共同支持判别。
- [核间同步](inter_core_sync.md)（`same_topic`）：核间同步接口页汇总 SyncAll 及信号式替代方案，便于按全局屏障或点对点依赖选型。
- [核间同步能力概述](inter_core_sync_overview.md)（`same_topic`）：核间同步概览解释 SyncAll 的参与核、workspace 和阻塞语义，是正确放置全核屏障的机制背景。
<!-- cannbot:related:end -->
