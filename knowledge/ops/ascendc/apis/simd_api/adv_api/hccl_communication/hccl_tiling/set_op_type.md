---
type: API
title: SetOpType
description: uint32_t SetOpType(uint32_t opType)
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/SetOpType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetOpType

设置通信任务类型。

参数：
- opType（输入）：表示通信任务类型。uint32_t类型。HCCL API提供HcclCMDType枚举定义作为该参数的取值。

返回值：- 0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [HCCL Tiling构造函数](hccl_tiling_constructor.md)（`related`）：HCCL Tiling构造函数 与《SetOpType》的衔接是：构造函数把通信域、算子类型、算法、归约类型和目的数据类型写入 HcclTilingData，这些字段随后由 GetTiling 生成 Kernel 侧通信配置。
- [SetAlgConfig](set_alg_config.md)（`related`）：通信算法选择依赖具体 HCCL op type；SetOpType 与 SetAlgConfig 需要保持算法和通信语义相容。
- [SetCommBlockNum](set_comm_block_num.md)（`same_topic`）：SetCommBlockNum 与《SetOpType》的实质衔接是：SetCommBlockNum 仅为 BatchWrite 设置参与核数；SetOpType选择 BatchWrite，字段写入 HcclTilingData，再由 GetTiling 生成 Kernel 通信配置。
- [SetReduceType](set_reduce_type.md)（`same_topic`）：SetReduceType 与《SetOpType》的实质衔接是：ReduceType 写入 HcclTilingData，只对 AllReduce/ReduceScatter 等归约通信生效，并与 OpType、通信参数一起由 GetTiling 下发。
- [SetStepSize](set_step_size.md)（`same_topic`）：SetStepSize 与《SetOpType》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
<!-- cannbot:related:end -->
