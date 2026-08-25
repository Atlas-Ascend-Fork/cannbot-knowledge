---
type: API
title: SetSkipLocalRankCopy
description: 设置本卡的通信算法的计算结果是否输出到目的数据buffer地址。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/SetSkipLocalRankCopy.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetSkipLocalRankCopy

设置本卡的通信算法的计算结果是否输出到目的数据buffer地址。

参数：
- skipLocalRankCopy（输入）：本卡的通信算法的计算结果是否输出到recvBuf（目的数据buffer地址）。

返回值：- 0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [GetTiling](get_tiling.md)（`related`）：skip 决策经 GetTiling 固化后才传给通信 Kernel。
- [HCCL Tiling使用说明](hccl_tiling_usage.md)（`related`）：使用页说明 skip 开关、算法和通信引擎的调用顺序及适用场景。
- [SetAlgConfig](set_alg_config.md)（`related`）：只有算法本身不依赖本地 rank copy 时才能跳过；须与 AlgConfig 配套。
- [SetSkipBufferWindowCopy](set_skip_buffer_window_copy.md)（`related`）：两个 skip 开关分别控制本地 rank copy 和 buffer-window copy，需按算法数据路径独立配置。
<!-- cannbot:related:end -->
