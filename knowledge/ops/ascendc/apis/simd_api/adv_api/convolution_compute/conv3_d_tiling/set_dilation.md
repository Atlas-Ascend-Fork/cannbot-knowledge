---
type: API
title: SetDilation
description: 设置Dilation信息。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/SetDilation.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetDilation

设置Dilation信息。

函数原型：void SetDilation(int64_t dilationD, int64_t dilationH, int64_t dilationW)

参数：
- dilationD（输入）：D方向Dilation大小。
- dilationH（输入）：H方向Dilation大小。
- dilationW（输入）：W方向Dilation大小。

<!-- cannbot:related:start -->
## 相关

- [Conv3D Tiling使用说明](conv3_d_tiling_usage.md)（`related`）：The usage flow places SetDilation in the required Conv3D tiling initialization sequence before GetTiling.
- [SetDilation](../conv3_d_backprop_filter_tiling/set_dilation.md)（`related`）：《SetDilation》说明设置Dilation信息，即卷积核Depth/Height/Width方向的扩张大小。；《SetDilation》说明设置Dilation信息。。二者在Dilation是Conv3D反向滤波Tiling的卷积几何参数，必须在GetTiling前写入并与同语义的前向/反向输入配置区分上存在可执行的直接衔接。
<!-- cannbot:related:end -->
