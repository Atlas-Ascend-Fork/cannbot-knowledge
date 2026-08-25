---
type: API
title: HCCL Tiling构造函数
description: 用于创建一个Mc2CcTilingConfig对象。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/HCCL_Tiling_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# HCCL Tiling构造函数

用于创建一个Mc2CcTilingConfig对象。

参数：
- groupName（输入）：当前通信任务所在的通信域。string类型，支持的最大长度为128字节。
- opType（输入）：表示通信任务类型。uint32_t类型。HCCL API提供HcclCMDType枚举定义作为该参数的取值，具体支持的通信任务类型及取值请参考表2。
- algConfig（输入）：通信算法配置。string类型，支持的最大长度为128字节。
- reduceType（输入）：归约操作类型，仅对有归约操作的通信任务生效。uint32_t类型，取值详见表2。
- dstDataType（输入）：通信任务中输出数据的数据类型。uint8_t类型，该参数的取值范围请参考表1。

<!-- cannbot:related:start -->
## 相关

- [GetTiling](get_tiling.md)（`related`）：HCCL Tiling构造函数 与《GetTiling》的衔接是：构造函数把通信域、算子类型、算法、归约类型和目的数据类型写入 HcclTilingData，这些字段随后由 GetTiling 生成 Kernel 侧通信配置。
- [HCCL Tiling使用说明](hccl_tiling_usage.md)（`related`）：HCCL Tiling构造函数 与《HCCL Tiling使用说明》的衔接是：构造函数把通信域、算子类型、算法、归约类型和目的数据类型写入 HcclTilingData，这些字段随后由 GetTiling 生成 Kernel 侧通信配置。
- [HcclTilingData](tiling_data_struct.md)（`related`）：HCCL Tiling构造函数 与《HcclTilingData》的衔接是：构造函数把通信域、算子类型、算法、归约类型和目的数据类型写入 HcclTilingData，这些字段随后由 GetTiling 生成 Kernel 侧通信配置。
- [SetAlgConfig](set_alg_config.md)（`related`）：HCCL Tiling构造函数 与《SetAlgConfig》的衔接是：构造函数把通信域、算子类型、算法、归约类型和目的数据类型写入 HcclTilingData，这些字段随后由 GetTiling 生成 Kernel 侧通信配置。
- [SetGroupName](set_group_name.md)（`related`）：SetGroupName 与《HCCL Tiling构造函数》的实质衔接是：SetGroupName 将通信域名称写入 HcclTilingData，再由 GetTiling 生成并通过 HcclContext 传入核侧；OpMC2Def 的 HcclGroup 是同一通信域契约的原型侧声明。
- [SetOpType](set_op_type.md)（`related`）：HCCL Tiling构造函数 与《SetOpType》的衔接是：构造函数把通信域、算子类型、算法、归约类型和目的数据类型写入 HcclTilingData，这些字段随后由 GetTiling 生成 Kernel 侧通信配置。
- [SetReduceType](set_reduce_type.md)（`related`）：HCCL Tiling构造函数 与《SetReduceType》的衔接是：构造函数把通信域、算子类型、算法、归约类型和目的数据类型写入 HcclTilingData，这些字段随后由 GetTiling 生成 Kernel 侧通信配置。
- [SetStepSize](set_step_size.md)（`same_topic`）：SetStepSize 与《HCCL Tiling构造函数》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
- [v2版本TilingData（废弃）](v2_tiling_data_deprecated.md)（`same_topic`）：v2版本TilingData（废弃） 与《HCCL Tiling构造函数》的实质衔接是：v2 废弃 TilingData 是旧 AI CPU 通信配置布局；v1、SetCcTiling/Init、当前 HcclTilingData 与 SetCcTilingV2 共同给出从旧固定顺序到现行接口的迁移链。
<!-- cannbot:related:end -->
