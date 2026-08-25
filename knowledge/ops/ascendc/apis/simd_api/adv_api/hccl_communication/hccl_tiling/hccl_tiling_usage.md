---
type: API
title: HCCL Tiling使用说明
description: 说明 HCCL 通信任务的 TilingData、Mc2InitTiling、Mc2CcTiling 及临时空间配置方式。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/HCCL_Tiling_usage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# HCCL Tiling使用说明

在算子实现中，由Tiling组装通信配置项，核函数实现时将Tiling配置项通过入参传递给Kernel侧通信API做通信计算。本节TilingData结构体包括Mc2InitTiling和Mc2CcTiling，这两个结构体均通过调用GetTiling接口返回。其中，Mc2CcTiling为具体每个通信任务的参数配置，当算子中有多个通信任务时，可定义多个Mc2CcTiling参数（最多支持定义8个）。

本接口组包含 TilingData结构体, v1版本TilingData（废弃）, v2版本TilingData（废弃）, TilingData结构体。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [GetTiling](get_tiling.md)（`related`）：使用说明给出构造配置、GetTiling、workspace 与 Kernel 初始化的完整 Host→Kernel 传递流程。
- [HCCL Tiling构造函数](hccl_tiling_constructor.md)（`related`）：HCCL Tiling构造函数 与《HCCL Tiling使用说明》的衔接是：构造函数把通信域、算子类型、算法、归约类型和目的数据类型写入 HcclTilingData，这些字段随后由 GetTiling 生成 Kernel 侧通信配置。
- [HCCL使用说明](../hccl_kernel/hccl_usage.md)（`related`）：Tiling 使用说明负责组装并传递通信配置，Kernel 使用说明负责用 Prepare/Commit 消费配置并调度通信任务，二者构成明确的 Host Tiling 到 AI Core 通信执行链。
- [HCCL通信类](../hccl_communication.md)（`related`）：HCCL通信类 与《HCCL Tiling使用说明》的实质衔接是：HCCL 通信类的上下文、kernel/host tiling、使用流程与 mock 死锁诊断共同界定通信对象从配置到执行的契约。
- [SetAlgConfig](set_alg_config.md)（`related`）：使用流程说明 SetAlgConfig 与通信域、算子类型等配置的调用顺序，以及最后如何取得 HCCL tiling。
- [SetDebugMode](set_debug_mode.md)（`related`）：使用页说明 debug mode 在完整 HCCL tiling 配置中的调用位置及最终 GetTiling 流程。
- [SetGroupName](set_group_name.md)（`related`）：SetGroupName 与《HCCL Tiling使用说明》的实质衔接是：SetGroupName 将通信域名称写入 HcclTilingData，再由 GetTiling 生成并通过 HcclContext 传入核侧；OpMC2Def 的 HcclGroup 是同一通信域契约的原型侧声明。
- [SetQueueNum](set_queue_num.md)（`related`）：使用页说明 QueueNum 与算法、通信引擎等字段的调用顺序及缺省行为。
- [SetSkipLocalRankCopy](set_skip_local_rank_copy.md)（`related`）：使用页说明 skip 开关、算法和通信引擎的调用顺序及适用场景。
- [v1版本TilingData（废弃）](v1_tiling_data_deprecated.md)（`related`）：当前用法页给出新 HcclTiling builder 与 GetTiling 流程。
- [HCCL Kernel侧接口](../hccl_kernel/hccl_kernel.md)（`same_topic`）：焦点处理HCCL Kernel 的初始化、任务提交查询等待和资源回收；HCCL Tiling使用说明正文界定“说明 HCCL 通信任务的 TilingData、Mc2InitTiling、Mc2CcTiling 及临时空间配置方式”。候选承担 HCCL 使用正文中的 Init、Iterate、Commit/Query/Wait、Finalize 或 context 设置，runbook 则复现同一 HCCL 同步失效。
- [HCCL Tiling侧接口](hccl_tiling.md)（`same_topic`）：HCCL Tiling使用说明说明说明 HCCL 通信任务的 TilingData、Mc2InitTiling、Mc2CcTiling 及临时空间配置方式。
- [HcclTilingData](tiling_data_struct.md)（`same_topic`）：两卡描述同一 HcclTilingData 契约：Mc2InitTiling 加最多八个 Mc2CcTiling 任务，并由 GetTiling 生成后传给 Kernel。
- [SetCommBlockNum](set_comm_block_num.md)（`same_topic`）：SetCommBlockNum 与《HCCL Tiling使用说明》的实质衔接是：SetCommBlockNum 仅为 BatchWrite 设置参与核数；SetOpType选择 BatchWrite，字段写入 HcclTilingData，再由 GetTiling 生成 Kernel 通信配置。
- [SetReduceType](set_reduce_type.md)（`same_topic`）：SetReduceType 与《HCCL Tiling使用说明》的实质衔接是：ReduceType 写入 HcclTilingData，只对 AllReduce/ReduceScatter 等归约通信生效，并与 OpType、通信参数一起由 GetTiling 下发。
- [SetStepSize](set_step_size.md)（`same_topic`）：SetStepSize 与《HCCL Tiling使用说明》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
- [v2版本TilingData（废弃）](v2_tiling_data_deprecated.md)（`same_topic`）：v2版本TilingData（废弃） 与《HCCL Tiling使用说明》的实质衔接是：v2 废弃 TilingData 是旧 AI CPU 通信配置布局；v1、SetCcTiling/Init、当前 HcclTilingData 与 SetCcTilingV2 共同给出从旧固定顺序到现行接口的迁移链。
<!-- cannbot:related:end -->
