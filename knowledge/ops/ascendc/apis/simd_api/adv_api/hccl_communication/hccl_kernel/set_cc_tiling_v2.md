---
type: API
title: SetCcTilingV2
description: 用于设置HCCL客户端中某个通信算法配置的TilingData地址。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/SetCcTilingV2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SetCcTilingV2

用于设置HCCL客户端中某个通信算法配置的TilingData地址。

函数原型：__aicore__ inline int32_t SetCcTilingV2(uint64_t offset)

参数：
- offset（输入）：通信算法配置Mc2CcTiling参数地址相对于Mc2InitTiling起始地址的偏移。Mc2CcTiling在Host侧计算得出，具体请参考表2 Mc2CcTiling参数说明，由框架传递到Kernel函数中使用。

返回值：- HCCL_SUCCESS，表示成功。

约束：
- 若调用本接口，必须保证InitV2在本接口前被调用。
- Tiling参数相同的同一种通信算法在调用Prepare接口前，只需要调用一次本接口，请参考调用示例：类型不同、Tiling参数不同的通信。
- 对于同一种通信算法，如果Tiling参数不同，重复调用本接口会覆盖之前的Tiling参数地址，因此需要在调用Prepare接口后再调用本接口设置新的Tiling参数。请参考调用示例：类型相同、Tiling参数不同的通信。
- 若调用本接口，必须使用标准C++语法定义TilingData结构体的开发方式。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [AllGather](all_gather.md)（`related`）：AllGather 约束要求先设置通信算法 TilingData 地址，SetCcTilingV2 正是该前置配置接口。
- [AllReduce](all_reduce.md)（`related`）：AllReduce 与《SetCcTilingV2》的实质衔接是：AllReduce 必须在 InitV2/SetCcTilingV2 后下发，并通过 Commit、Query/Wait、Finalize 完成任务；模板、reduce 类型和使用说明约束通信执行链。
- [AlltoAllvWrite](allto_allv_write.md)（`related`）：AlltoAllvWrite 与《SetCcTilingV2》的实质衔接是：AlltoAllvWrite 的字节偏移、大小和 window 地址依赖 rank/window 查询，且必须在 InitV2/SetCcTilingV2 后通过 Commit、Query/Wait、Finalize 完成 HCCL 任务。
- [Finalize（HCCL集合通信）](finalize.md)（`related`）：Finalize（HCCL集合通信） 与《SetCcTilingV2》的实质衔接是：Finalize 只能在 InitV2 和 SetCcTilingV2 之后终止 HCCL 对象；普通任务需先 Commit/Wait，多个 BatchWrite 队列需逐队列 QueueBarrier，使用说明明确终止后对象不可复用。
- [HCCL使用说明](hccl_usage.md)（`related`）：HCCL使用说明说明Ascend C提供一组HCCL通信类高阶API，方便算子Kernel开发用户在AI Core侧灵活管理通算融合算子中计算与通信任务的执行顺序。
- [HcclTilingData](../hccl_tiling/tiling_data_struct.md)（`related`）：SetCcTilingV2 以 Mc2CcTiling 相对 Mc2InitTiling 的 offset 绑定通信算法配置；HcclTilingData 的连续布局和最多八组配置决定 offset 的含义。
- [Query（HCCL集合通信）](query.md)（`related`）：Query 明确依赖 SetCcTilingV2 配置通信任务的 repeat 等 tiling。
- [HCCL集合通信Wait](wait.md)（`same_topic`）：HCCL集合通信Wait：Wait消费 Prepare原语返回的 handle，必须在InitV2/SetCcTilingV2后按Commit与Prepare顺序阻塞；Query提供非阻塞完成检查，Iterate定义细粒度步数。 目标卡《SetCcTilingV2》补充：用于设置HCCL客户端中某个通信算法配置的TilingData地址。
- [InitV2](init_v2.md)（`same_topic`）：InitV2说明HCCL客户端初始化接口。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。
- [Init（废弃）](init_deprecated.md)（`same_topic`）：焦点处理废弃 HCCL Init 向 InitV2/SetCcTilingV2 迁移的生命周期；SetCcTilingV2正文说明“用于设置HCCL客户端中某个通信算法配置的TilingData地址”。候选给出旧接口的一一替代、通信配置迁移或最终资源回收步骤。
- [SetCcTiling（废弃）](set_cc_tiling_deprecated.md)（`same_topic`）：废弃接口与 V2 都向 HCCL 客户端设置通信算法 TilingData 地址；V2 是正文给出的迁移目标。
- [v2版本TilingData（废弃）](../hccl_tiling/v2_tiling_data_deprecated.md)（`same_topic`）：v2版本TilingData（废弃） 与《SetCcTilingV2》的实质衔接是：v2 废弃 TilingData 是旧 AI CPU 通信配置布局；v1、SetCcTiling/Init、当前 HcclTilingData 与 SetCcTilingV2 共同给出从旧固定顺序到现行接口的迁移链。
<!-- cannbot:related:end -->
