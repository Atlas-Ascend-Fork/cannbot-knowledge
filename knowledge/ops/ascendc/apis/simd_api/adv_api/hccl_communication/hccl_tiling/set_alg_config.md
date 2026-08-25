---
type: API
title: SetAlgConfig
description: uint32_t SetAlgConfig(const std::string& algConfig)
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/SetAlgConfig.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetAlgConfig

uint32_t SetAlgConfig(const std::string& algConfig)

设置通信算法。

本接口属于 HCCL 集合通信 Tiling 接口，用于配置多卡通信参数。

参数说明：algConfig：输入 通信算法配置。string类型，支持的最大长度为128字节。

返回值：-   0表示设置成功。
-   非0表示设置失败。

<!-- cannbot:related:start -->
## 相关

- [GetTiling](get_tiling.md)（`related`）：SetAlgConfig 写入的算法配置只有经 GetTiling 生成通信 tiling 数据后才传给 Kernel。
- [HCCL Tiling使用说明](hccl_tiling_usage.md)（`related`）：使用流程说明 SetAlgConfig 与通信域、算子类型等配置的调用顺序，以及最后如何取得 HCCL tiling。
- [HCCL Tiling构造函数](hccl_tiling_constructor.md)（`related`）：HCCL Tiling构造函数 与《SetAlgConfig》的衔接是：构造函数把通信域、算子类型、算法、归约类型和目的数据类型写入 HcclTilingData，这些字段随后由 GetTiling 生成 Kernel 侧通信配置。
- [HcclTilingData](tiling_data_struct.md)（`related`）：TilingData 结构承载 SetAlgConfig 等 setter 生成的固定通信参数，是 Host 配置传入 Kernel 的接口边界。
- [SetDebugMode](set_debug_mode.md)（`related`）：调试开关不改变算法配置；复现通信问题时需固定 SetAlgConfig，只切换 DebugMode 才形成有效 A/B。
- [SetOpType](set_op_type.md)（`related`）：通信算法选择依赖具体 HCCL op type；SetOpType 与 SetAlgConfig 需要保持算法和通信语义相容。
- [SetSkipLocalRankCopy](set_skip_local_rank_copy.md)（`related`）：只有算法本身不依赖本地 rank copy 时才能跳过；须与 AlgConfig 配套。
- [SetStepSize](set_step_size.md)（`same_topic`）：SetStepSize 与《SetAlgConfig》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
<!-- cannbot:related:end -->
