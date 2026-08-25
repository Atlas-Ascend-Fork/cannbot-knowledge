---
type: API
title: HCCL Kernel侧接口
description: 提供HCCL集合通信的Kernel侧接口，包含InitV2、SetCcTilingV2、AllReduce、AllGather、ReduceScatter、BatchWrite等方法。
tags: [task.lookup, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/HCCL_Kernel.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# HCCL Kernel侧接口

提供 Ascend C HCCL 集合通信的 Kernel 侧接口，通过模板参数配置通信数据类型与编排模式。
核心通信算子包括 AllReduce、AllGather、ReduceScatter、AlltoAll、AlltoAllV，以及 AlltoAllvWrite 和 BatchWrite 等数据写入接口。
执行流程为 InitV2 初始化并 SetCcTilingV2 设置 Tiling 后，调用 Commit 提交通信任务，再通过 Wait/Query/Iterate 管理执行状态，最终 Finalize 释放资源。
Init/SetCcTiling 为废弃接口，新代码应使用 V2 版本。

<!-- cannbot:related:start -->
## 相关

- [单 rank mock HCCL 致 AIC+AIV SyncAll 死锁](../../../../../runbooks/compilation/rank_mock_hccl_aic_aiv_syncall.md)（`exemplifies`）：焦点处理HCCL Kernel 的初始化、任务提交查询等待和资源回收；单 rank mock HCCL 致 AIC+AIV SyncAll 死锁正文界定“atcoss BlockPrologueAllGather 等 AIC+AIV 通算融合 kernel 在单 rank mock HCCL context 下执行超时，mock 不提供 SyncAll 跨核配对所需的状态标志写入流程致 Re”。候选承担 HCCL 使用正文中的 Init、Iterate、Commit/Query/Wait、Finalize 或 context 设置，runbook 则复现同一 HCCL 同步失效。
- [AlltoAll](allto_all.md)（`related`）：《AlltoAll》说明集合通信AlltoAll的任务下发接口，返回该任务的标识handleId给用户。AlltoAll的功能为：每张卡向通信域内所有卡发送相同数据量的数据，并从所有卡接收相同数据量的数据。结合原型中的参数，描述接口功能，具体为，第j张卡接收到来自第i张卡的sendBuf中第j块数据，并将该数据存放到本卡recvBuf中第i块的位置。；《HCCL Kernel侧接口》说明提供HCCL集合通信的Kernel侧接口，包含InitV2、SetCcTilingV2、AllReduce、AllGather、ReduceScatter、BatchWrite等方法。。二者在AlltoAll任务下发返回的handle必须进入HCCL的Commit、Query/Wait和Finalize执行链，且通信域rank布局决定收发分块上存在可执行的直接衔接。
- [BatchWrite](batch_write.md)（`related`）：《BatchWrite》说明集合通信BatchWrite任务下发接口，实现点对点批量数据传输，可同时将多份数据发送到不同Global Memory地址。；《HCCL Kernel侧接口》说明提供HCCL集合通信的Kernel侧接口，包含InitV2、SetCcTilingV2、AllReduce、AllGather、ReduceScatter、BatchWrite等方法。。二者在BatchWrite的多目标点对点任务依赖通信队列数量，进入Commit、Query/Wait和Finalize的HCCL任务生命周期上存在可执行的直接衔接。
- [GetQueueNum](get_queue_num.md)（`related`）：《GetQueueNum》说明获取BatchWrite通信任务的通信队列数量。；《HCCL Kernel侧接口》说明提供HCCL集合通信的Kernel侧接口，包含InitV2、SetCcTilingV2、AllReduce、AllGather、ReduceScatter、BatchWrite等方法。。二者在通信队列数量的查询与设置、BatchWrite/AlltoallvWrite发任务、Commit/Wait及Finalize构成同一HCCL任务生命周期上存在可执行的直接衔接。
- [GetWindowsInAddr](get_windows_in_addr.md)（`related`）：Hccl Kernel 总览说明通信对象生命周期和窗口资源，给出 GetWindowsInAddr 的宿主对象上下文。
- [GetWindowsOutAddr](get_windows_out_addr.md)（`related`）：HCCL Kernel 接口页给出初始化、提交、等待和集合通信流程，是直接使用 WindowsOut 地址时所属的通信客户端生命周期。
- [HCCL Context简介](../hccl_context/hccl_context_intro.md)（`related`）：HCCL Context简介 与《HCCL Kernel侧接口》的实质衔接是：HCCL context 需要 host HcclGroup 先声明通信域，再由 kernel Get/SetHcclContext 使用；通信类、kernel/tiling 与使用说明共同闭合地址配置到集合通信执行。
- [HCCL通信类](../hccl_communication.md)（`related`）：HCCL通信类 与《HCCL Kernel侧接口》的实质衔接是：HCCL 通信类的上下文、kernel/host tiling、使用流程与 mock 死锁诊断共同界定通信对象从配置到执行的契约。
- [AllReduce](all_reduce.md)（`same_topic`）：AllReduce 与《HCCL Kernel侧接口》的实质衔接是：AllReduce 必须在 InitV2/SetCcTilingV2 后下发，并通过 Commit、Query/Wait、Finalize 完成任务；模板、reduce 类型和使用说明约束通信执行链。
- [AlltoAllvWrite](allto_allv_write.md)（`same_topic`）：AlltoAllvWrite 与《HCCL Kernel侧接口》的实质衔接是：AlltoAllvWrite 的字节偏移、大小和 window 地址依赖 rank/window 查询，且必须在 InitV2/SetCcTilingV2 后通过 Commit、Query/Wait、Finalize 完成 HCCL 任务。
- [Commit（HCCL集合通信）](commit.md)（`same_topic`）：焦点处理HCCL Kernel 的初始化、任务提交查询等待和资源回收；Commit（HCCL集合通信）正文界定“非细粒度通信时，每调用一次本接口，则通知服务端可以执行handleId对应的任务一次。细粒度通信时，每调用一次本接口，则通知服务端可以执行handleId对应的步长长度的子通信任务”。候选承担 HCCL 使用正文中的 Init、Iterate、Commit/Query/Wait、Finalize 或 context 设置，runbook 则复现同一 HCCL 同步失效。
- [Finalize（HCCL集合通信）](finalize.md)（`same_topic`）：焦点处理HCCL Kernel 的初始化、任务提交查询等待和资源回收；Finalize（HCCL集合通信）正文界定“通知服务端后续无通信任务，执行结束后退出”。候选承担 HCCL 使用正文中的 Init、Iterate、Commit/Query/Wait、Finalize 或 context 设置，runbook 则复现同一 HCCL 同步失效。
- [GetHcclContext](../hccl_context/get_hccl_context.md)（`same_topic`）：焦点处理HCCL Kernel 的初始化、任务提交查询等待和资源回收；GetHcclContext正文界定“获取指定Index通信域的context（消息区）地址”。候选承担 HCCL 使用正文中的 Init、Iterate、Commit/Query/Wait、Finalize 或 context 设置，runbook 则复现同一 HCCL 同步失效。
- [HCCL Tiling使用说明](../hccl_tiling/hccl_tiling_usage.md)（`same_topic`）：焦点处理HCCL Kernel 的初始化、任务提交查询等待和资源回收；HCCL Tiling使用说明正文界定“说明 HCCL 通信任务的 TilingData、Mc2InitTiling、Mc2CcTiling 及临时空间配置方式”。候选承担 HCCL 使用正文中的 Init、Iterate、Commit/Query/Wait、Finalize 或 context 设置，runbook 则复现同一 HCCL 同步失效。
- [HCCL Tiling侧接口](../hccl_tiling/hccl_tiling.md)（`same_topic`）：HCCL Kernel侧接口说明提供HCCL集合通信的Kernel侧接口，包含InitV2、SetCcTilingV2、AllReduce、AllGather、ReduceScatter、BatchWrite等方法。
- [HCCL使用说明](hccl_usage.md)（`same_topic`）：焦点处理HCCL Kernel 的初始化、任务提交查询等待和资源回收；HCCL使用说明正文界定“Ascend C提供一组HCCL通信类高阶API，方便算子Kernel开发用户在AI Core侧灵活管理通算融合算子中计算与通信任务的执行顺序”。候选承担 HCCL 使用正文中的 Init、Iterate、Commit/Query/Wait、Finalize 或 context 设置，runbook 则复现同一 HCCL 同步失效。
- [HCCL集合通信Wait](wait.md)（`same_topic`）：焦点处理HCCL Kernel 的初始化、任务提交查询等待和资源回收；HCCL集合通信Wait正文界定“阻塞AI Core，非细粒度通信时，等待handleId对应的通信任务完成，细粒度通信时，等待handleId对应的步长长度的子通信任务完成。handleId调用Wait接口的顺序，须和Prepare接口一致。该接口默认在所有核上工作，用户”。候选承担 HCCL 使用正文中的 Init、Iterate、Commit/Query/Wait、Finalize 或 context 设置，runbook 则复现同一 HCCL 同步失效。
- [InitV2](init_v2.md)（`same_topic`）：焦点处理HCCL Kernel 的初始化、任务提交查询等待和资源回收；InitV2正文界定“HCCL客户端初始化接口。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行”。候选承担 HCCL 使用正文中的 Init、Iterate、Commit/Query/Wait、Finalize 或 context 设置，runbook 则复现同一 HCCL 同步失效。
- [Iterate](iterate.md)（`same_topic`）：焦点处理HCCL Kernel 的初始化、任务提交查询等待和资源回收；Iterate正文界定“细粒度通信接口，获取集合通信算法每一步的输入或输出，实现计算与通信的精细粒度流水排布”。候选承担 HCCL 使用正文中的 Init、Iterate、Commit/Query/Wait、Finalize 或 context 设置，runbook 则复现同一 HCCL 同步失效。
- [Query（HCCL集合通信）](query.md)（`same_topic`）：焦点处理HCCL Kernel 的初始化、任务提交查询等待和资源回收；Query（HCCL集合通信）正文界定“查询handleId对应的通信任务已经完成的轮次，最多返回repeat轮。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行”。候选承担 HCCL 使用正文中的 Init、Iterate、Commit/Query/Wait、Finalize 或 context 设置，runbook 则复现同一 HCCL 同步失效。
- [SetHcclContext](../hccl_context/set_hccl_context.md)（`same_topic`）：焦点处理HCCL Kernel 的初始化、任务提交查询等待和资源回收；SetHcclContext正文界定“设置通算融合算子每个通信域对应的context（消息区）地址”。候选承担 HCCL 使用正文中的 Init、Iterate、Commit/Query/Wait、Finalize 或 context 设置，runbook 则复现同一 HCCL 同步失效。
- [SetStepSize](../hccl_tiling/set_step_size.md)（`same_topic`）：SetStepSize 与《HCCL Kernel侧接口》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
<!-- cannbot:related:end -->
