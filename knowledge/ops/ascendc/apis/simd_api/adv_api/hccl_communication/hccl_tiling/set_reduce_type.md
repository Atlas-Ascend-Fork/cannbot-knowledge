---
type: API
title: SetReduceType
description: 设置Reduce操作类型，仅对有归约操作的通信任务生效。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/SetReduceType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetReduceType

设置Reduce操作类型，仅对有归约操作的通信任务生效。

参数：
- reduceType（输入）：归约操作类型，仅对有归约操作的通信任务生效。uint32_t类型，取值详见表2参数说明。
- dstDataType（输入）：通信任务中输出数据的数据类型。uint8_t类型，该参数的取值范围请参考表1。
- srcDataType（输入）：通信任务中输入数据的数据类型。uint8_t类型，该参数的取值范围请参考表1。

返回值：- 0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [AllReduce](../hccl_kernel/all_reduce.md)（`related`）：AllReduce 与《SetReduceType》的实质衔接是：AllReduce 必须在 InitV2/SetCcTilingV2 后下发，并通过 Commit、Query/Wait、Finalize 完成任务；模板、reduce 类型和使用说明约束通信执行链。
- [HCCL Tiling构造函数](hccl_tiling_constructor.md)（`related`）：HCCL Tiling构造函数 与《SetReduceType》的衔接是：构造函数把通信域、算子类型、算法、归约类型和目的数据类型写入 HcclTilingData，这些字段随后由 GetTiling 生成 Kernel 侧通信配置。
- [ReduceScatter](../hccl_kernel/reduce_scatter.md)（`related`）：SetReduceType 与《ReduceScatter》的实质衔接是：ReduceType 写入 HcclTilingData，只对 AllReduce/ReduceScatter 等归约通信生效，并与 OpType、通信参数一起由 GetTiling 下发。
- [GetTiling](get_tiling.md)（`same_topic`）：SetReduceType 与《GetTiling》的实质衔接是：ReduceType 写入 HcclTilingData，只对 AllReduce/ReduceScatter 等归约通信生效，并与 OpType、通信参数一起由 GetTiling 下发。
- [HCCL Tiling使用说明](hccl_tiling_usage.md)（`same_topic`）：SetReduceType 与《HCCL Tiling使用说明》的实质衔接是：ReduceType 写入 HcclTilingData，只对 AllReduce/ReduceScatter 等归约通信生效，并与 OpType、通信参数一起由 GetTiling 下发。
- [HCCL Tiling侧接口](hccl_tiling.md)（`same_topic`）：SetReduceType 与《HCCL Tiling侧接口》的实质衔接是：ReduceType 写入 HcclTilingData，只对 AllReduce/ReduceScatter 等归约通信生效，并与 OpType、通信参数一起由 GetTiling 下发。
- [HcclTilingData](tiling_data_struct.md)（`same_topic`）：SetReduceType 与《HcclTilingData》的实质衔接是：ReduceType 写入 HcclTilingData，只对 AllReduce/ReduceScatter 等归约通信生效，并与 OpType、通信参数一起由 GetTiling 下发。
- [SetOpType](set_op_type.md)（`same_topic`）：SetReduceType 与《SetOpType》的实质衔接是：ReduceType 写入 HcclTilingData，只对 AllReduce/ReduceScatter 等归约通信生效，并与 OpType、通信参数一起由 GetTiling 下发。
<!-- cannbot:related:end -->
