---
type: API
title: SetDebugMode
description: uint32_t SetDebugMode(uint8_t debugMode)
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/SetDebugMode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SetDebugMode

设置调测模式。

参数：
- debugMode（输入）：表示选择的调测模式，uint8_t类型。参数支持的取值如下：1：关闭HCCL高阶API通信功能。/2：打印消息队列和Prepare消息执行次数等信息。/3：打印Prepare消息源数据buffer和目的数据buffer中的数据。

返回值：- 0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [GetTiling](get_tiling.md)（`related`）：SetDebugMode 写入的调试配置需经 GetTiling 序列化后才能由通信 Kernel 消费。
- [HCCL Tiling使用说明](hccl_tiling_usage.md)（`related`）：使用页说明 debug mode 在完整 HCCL tiling 配置中的调用位置及最终 GetTiling 流程。
- [HcclTilingData](tiling_data_struct.md)（`related`）：TilingData 结构是 debug mode 等通信配置跨 Host/Kernel 的承载契约。
- [SetAlgConfig](set_alg_config.md)（`related`）：调试开关不改变算法配置；复现通信问题时需固定 SetAlgConfig，只切换 DebugMode 才形成有效 A/B。
<!-- cannbot:related:end -->
