---
type: API
title: GetTiling
description: 获取Mc2InitTiling参数和Mc2CcTiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/GetTiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetTiling

获取Mc2InitTiling参数和Mc2CcTiling参数。

参数：
- tiling（输出）：Tiling结构体存储的Tiling信息。

返回值：- 返回值为0，则tiling计算成功，该Tiling结构体的值可以用于后续计算。

<!-- cannbot:related:start -->
## 相关

- [HCCL Tiling使用说明](hccl_tiling_usage.md)（`related`）：使用说明给出构造配置、GetTiling、workspace 与 Kernel 初始化的完整 Host→Kernel 传递流程。
- [HCCL Tiling构造函数](hccl_tiling_constructor.md)（`related`）：HCCL Tiling构造函数 与《GetTiling》的衔接是：构造函数把通信域、算子类型、算法、归约类型和目的数据类型写入 HcclTilingData，这些字段随后由 GetTiling 生成 Kernel 侧通信配置。
- [SetAlgConfig](set_alg_config.md)（`related`）：SetAlgConfig 写入的算法配置只有经 GetTiling 生成通信 tiling 数据后才传给 Kernel。
- [SetDebugMode](set_debug_mode.md)（`related`）：SetDebugMode 写入的调试配置需经 GetTiling 序列化后才能由通信 Kernel 消费。
- [SetGroupName](set_group_name.md)（`related`）：SetGroupName 与《GetTiling》的实质衔接是：SetGroupName 将通信域名称写入 HcclTilingData，再由 GetTiling 生成并通过 HcclContext 传入核侧；OpMC2Def 的 HcclGroup 是同一通信域契约的原型侧声明。
- [SetQueueNum](set_queue_num.md)（`related`）：SetQueueNum 的值经 GetTiling 序列化后才可被 Kernel GetQueueNum 读取。
- [SetSkipLocalRankCopy](set_skip_local_rank_copy.md)（`related`）：skip 决策经 GetTiling 固化后才传给通信 Kernel。
- [HCCL Tiling侧接口](hccl_tiling.md)（`same_topic`）：GetTiling说明获取Mc2InitTiling参数和Mc2CcTiling参数。
- [HcclTilingData](tiling_data_struct.md)（`same_topic`）：GetTiling 直接返回由 Mc2InitTiling 与最多 8 个 Mc2CcTiling 任务组成的 HcclTilingData。
- [SetCommBlockNum](set_comm_block_num.md)（`same_topic`）：SetCommBlockNum 与《GetTiling》的实质衔接是：SetCommBlockNum 仅为 BatchWrite 设置参与核数；SetOpType选择 BatchWrite，字段写入 HcclTilingData，再由 GetTiling 生成 Kernel 通信配置。
- [SetReduceType](set_reduce_type.md)（`same_topic`）：SetReduceType 与《GetTiling》的实质衔接是：ReduceType 写入 HcclTilingData，只对 AllReduce/ReduceScatter 等归约通信生效，并与 OpType、通信参数一起由 GetTiling 下发。
- [SetStepSize](set_step_size.md)（`same_topic`）：SetStepSize 与《GetTiling》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
- [v2版本TilingData（废弃）](v2_tiling_data_deprecated.md)（`same_topic`）：v2版本TilingData（废弃） 与《GetTiling》的实质衔接是：v2 废弃 TilingData 是旧 AI CPU 通信配置布局；v1、SetCcTiling/Init、当前 HcclTilingData 与 SetCcTilingV2 共同给出从旧固定顺序到现行接口的迁移链。
<!-- cannbot:related:end -->
