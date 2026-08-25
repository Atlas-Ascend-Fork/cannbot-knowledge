---
type: API
title: HCCL使用说明
description: Ascend C提供一组HCCL通信类高阶API，方便算子Kernel开发用户在AI Core侧灵活管理通算融合算子中计算与通信任务的执行顺序。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/HCCL_usage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# HCCL使用说明

Ascend C提供一组HCCL通信类高阶API，方便算子Kernel开发用户在AI Core侧灵活管理通算融合算子中计算与通信任务的执行顺序。 HCCL为集合通信任务客户端，主要对外提供了集合通信原语接口（以下统称为Prepare接口），对标集合通信C++接口，当前支持AllReduce、AllGather、ReduceScatter、AlltoAll、AlltoAllV、AlltoAllvWrite、BatchWrite接口。本章的所有接口运行在AI Core上，且不执行通信任务，而是由用户调用Prepare接口将对应类型的通信任务信息发送给AI CPU或CCU服务端，并在合适的时机通过Commit接口通知AI CPU或CCU上的服务端执行对应的通信任务。

<!-- cannbot:related:start -->
## 相关

- [单 rank mock HCCL 致 AIC+AIV SyncAll 死锁](../../../../../runbooks/compilation/rank_mock_hccl_aic_aiv_syncall.md)（`exemplifies`）：单 rank mock HCCL 致 AIC+AIV SyncAll 死锁 与《HCCL使用说明》的实质衔接是：单 rank mock 未提供真实 HCCL 参与者，SyncAll 无法闭合；HCCL context/commit/wait 和核间同步共同支持判别。
- [AllReduce](all_reduce.md)（`related`）：AllReduce 与《HCCL使用说明》的实质衔接是：AllReduce 必须在 InitV2/SetCcTilingV2 后下发，并通过 Commit、Query/Wait、Finalize 完成任务；模板、reduce 类型和使用说明约束通信执行链。
- [AlltoAll](allto_all.md)（`related`）：《AlltoAll》说明集合通信AlltoAll的任务下发接口，返回该任务的标识handleId给用户。AlltoAll的功能为：每张卡向通信域内所有卡发送相同数据量的数据，并从所有卡接收相同数据量的数据。结合原型中的参数，描述接口功能，具体为，第j张卡接收到来自第i张卡的sendBuf中第j块数据，并将该数据存放到本卡recvBuf中第i块的位置。；《HCCL使用说明》说明Ascend C提供一组HCCL通信类高阶API，方便算子Kernel开发用户在AI Core侧灵活管理通算融合算子中计算与通信任务的执行顺序。。二者在AlltoAll任务下发返回的handle必须进入HCCL的Commit、Query/Wait和Finalize执行链，且通信域rank布局决定收发分块上存在可执行的直接衔接。
- [BatchWrite](batch_write.md)（`related`）：《BatchWrite》说明集合通信BatchWrite任务下发接口，实现点对点批量数据传输，可同时将多份数据发送到不同Global Memory地址。；《HCCL使用说明》说明Ascend C提供一组HCCL通信类高阶API，方便算子Kernel开发用户在AI Core侧灵活管理通算融合算子中计算与通信任务的执行顺序。。二者在BatchWrite的多目标点对点任务依赖通信队列数量，进入Commit、Query/Wait和Finalize的HCCL任务生命周期上存在可执行的直接衔接。
- [Commit（HCCL集合通信）](commit.md)（`related`）：Commit（HCCL集合通信）说明非细粒度通信时，每调用一次本接口，则通知服务端可以执行handleId对应的任务一次。细粒度通信时，每调用一次本接口，则通知服务端可以执行handleId对应的步长长度的子通信任务；对HCCL使用说明而言，HCCL 的 TilingData 先配置通信任务，非细粒度任务再通过 Commit 下发并用 Wait 按 Prepare 顺序等待完成。
- [GetQueueNum](get_queue_num.md)（`related`）：《GetQueueNum》说明获取BatchWrite通信任务的通信队列数量。；《HCCL使用说明》说明Ascend C提供一组HCCL通信类高阶API，方便算子Kernel开发用户在AI Core侧灵活管理通算融合算子中计算与通信任务的执行顺序。。二者在通信队列数量的查询与设置、BatchWrite/AlltoallvWrite发任务、Commit/Wait及Finalize构成同一HCCL任务生命周期上存在可执行的直接衔接。
- [GetWindowsInAddr](get_windows_in_addr.md)（`related`）：HCCL 使用流程解释 Prepare/Commit 的服务模型和窗口地址使用时机，使窗口输入地址进入完整通信任务链。
- [GetWindowsOutAddr](get_windows_out_addr.md)（`related`）：HCCL 使用说明解释 AI Core 仅准备通信任务、由 AI CPU/CCU 服务端执行的模型，补足 WindowsOut 作为计算输入输出地址以减少拷贝的使用目的。
- [HCCL Context简介](../hccl_context/hccl_context_intro.md)（`related`）：HCCL Context简介 与《HCCL使用说明》的实质衔接是：HCCL context 需要 host HcclGroup 先声明通信域，再由 kernel Get/SetHcclContext 使用；通信类、kernel/tiling 与使用说明共同闭合地址配置到集合通信执行。
- [HCCL Tiling使用说明](../hccl_tiling/hccl_tiling_usage.md)（`related`）：Tiling 使用说明负责组装并传递通信配置，Kernel 使用说明负责用 Prepare/Commit 消费配置并调度通信任务，二者构成明确的 Host Tiling 到 AI Core 通信执行链。
- [HCCL模板参数](hccl_template_params.md)（`related`）：使用说明给出模板配置、InitV2、Commit/Wait/Finalize 的配套时序，可验证模板选择是否落到正确服务端。
- [HCCL通信类](../hccl_communication.md)（`related`）：HCCL通信类 与《HCCL使用说明》的实质衔接是：HCCL 通信类的上下文、kernel/host tiling、使用流程与 mock 死锁诊断共同界定通信对象从配置到执行的契约。
- [HCCL集合通信Wait](wait.md)（`related`）：HCCL集合通信Wait说明阻塞AI Core，非细粒度通信时，等待handleId对应的通信任务完成，细粒度通信时，等待handleId对应的步长长度的子通信任务完成。handleId调用Wait接口的顺序，须和Prepare接口一致。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行；对HCCL使用说明而言，HCCL 的 TilingData 先配置通信任务，非细粒度任务再通过 Commit 下发并用 Wait 按 Prepare 顺序等待完成。
- [InterHcclGroupSync](inter_hccl_group_sync.md)（`related`）：HCCL使用说明说明Ascend C提供一组HCCL通信类高阶API，方便算子Kernel开发用户在AI Core侧灵活管理通算融合算子中计算与通信任务的执行顺序。
- [Iterate](iterate.md)（`related`）：“Iterate”定义：细粒度通信接口，获取集合通信算法每一步的输入或输出，实现计算与通信的精细粒度流水排布。；“HCCL使用说明”定义：Ascend C提供一组HCCL通信类高阶API，方便算子Kernel开发用户在AI Core侧灵活管理通算融合算子中计算与通信任务的执行顺序。。实质衔接：细粒度 Iterate 取得每一步输入/输出后，Commit 推进一步通信，Query/Wait 观测或阻塞对应轮次，构成计算通信流水的可执行闭环。
- [QueueBarrier](queue_barrier.md)（`related`）：HCCL使用说明说明Ascend C提供一组HCCL通信类高阶API，方便算子Kernel开发用户在AI Core侧灵活管理通算融合算子中计算与通信任务的执行顺序。
- [ReduceScatter](reduce_scatter.md)（`related`）：ReduceScatter：ReduceScatter 的通信语义可分解为归约后分散，其 handle 必须进入 HCCL 的 Init/Commit/Query/Wait 生命周期；AllReduce/AllGather用于精确区分其数据分布语义。 目标卡《HCCL使用说明》补充：Ascend C提供一组HCCL通信类高阶API，方便算子Kernel开发用户在AI Core侧灵活管理通算融合算子中计算与通信任务的执行顺序。
- [SetCcTilingV2](set_cc_tiling_v2.md)（`related`）：HCCL使用说明说明Ascend C提供一组HCCL通信类高阶API，方便算子Kernel开发用户在AI Core侧灵活管理通算融合算子中计算与通信任务的执行顺序。
- [AllGather](all_gather.md)（`same_topic`）：使用说明串联 Init、SetCcTiling、AllGather、Commit 与 Wait，可据 commit 模板参数选择完整执行序列。
- [AlltoAllvWrite](allto_allv_write.md)（`same_topic`）：AlltoAllvWrite 与《HCCL使用说明》的实质衔接是：AlltoAllvWrite 的字节偏移、大小和 window 地址依赖 rank/window 查询，且必须在 InitV2/SetCcTilingV2 后通过 Commit、Query/Wait、Finalize 完成 HCCL 任务。
- [Finalize（HCCL集合通信）](finalize.md)（`same_topic`）：Finalize（HCCL集合通信） 与《HCCL使用说明》的实质衔接是：Finalize 只能在 InitV2 和 SetCcTilingV2 之后终止 HCCL 对象；普通任务需先 Commit/Wait，多个 BatchWrite 队列需逐队列 QueueBarrier，使用说明明确终止后对象不可复用。
- [GetHcclContext](../hccl_context/get_hccl_context.md)（`same_topic`）：GetHcclContext 与《HCCL使用说明》的实质衔接是：GetHcclContext 取得指定通信域消息区，SetHcclContext 配置同一地址；HCCL Context/Kernel 使用说明和 InitV2 说明该地址如何绑定到集合通信对象。
- [HCCL Kernel侧接口](hccl_kernel.md)（`same_topic`）：焦点处理HCCL Kernel 的初始化、任务提交查询等待和资源回收；HCCL使用说明正文界定“Ascend C提供一组HCCL通信类高阶API，方便算子Kernel开发用户在AI Core侧灵活管理通算融合算子中计算与通信任务的执行顺序”。候选承担 HCCL 使用正文中的 Init、Iterate、Commit/Query/Wait、Finalize 或 context 设置，runbook 则复现同一 HCCL 同步失效。
- [HCCL Tiling侧接口](../hccl_tiling/hccl_tiling.md)（`same_topic`）：HCCL使用说明说明Ascend C提供一组HCCL通信类高阶API，方便算子Kernel开发用户在AI Core侧灵活管理通算融合算子中计算与通信任务的执行顺序。
- [Init（废弃）](init_deprecated.md)（`same_topic`）：焦点处理废弃 HCCL Init 向 InitV2/SetCcTilingV2 迁移的生命周期；HCCL使用说明正文说明“Ascend C提供一组HCCL通信类高阶API，方便算子Kernel开发用户在AI Core侧灵活管理通算融合算子中计算与通信任务的执行顺序”。候选给出旧接口的一一替代、通信配置迁移或最终资源回收步骤。
- [SetHcclContext](../hccl_context/set_hccl_context.md)（`same_topic`）：SetHcclContext 与《HCCL使用说明》的实质衔接是：SetHcclContext 把指定通信域消息区地址绑定给 HCCL 对象；GetHcclContext、Context/Kernel 使用说明与 InitV2 构成配置和消费两端。
- [SetStepSize](../hccl_tiling/set_step_size.md)（`same_topic`）：SetStepSize 与《HCCL使用说明》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
<!-- cannbot:related:end -->
