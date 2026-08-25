---
type: API
title: AscLoad3dV2Config
description: 用于设置Load3Dv2接口的repeat参数，包括迭代步长、次数和方向。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/struct/asc_load3d_v2_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# AscLoad3dV2Config

asc_load3d_v2_config用于设置Load3Dv2接口的repeat参数。

字段：rpt_stride：height/width方向上的前一个迭代与后一个迭代起始地址的距离，取值范围：[0, 65535]，默认值为0。；rpt_time：height/width方向上的迭代次数，取值范围：[0, 255]，默认值为1。；rpt_mode：控制repeat迭代的方向，取值范围：[0, 1]，默认值为0。 0：迭代沿height方向； 1：迭代沿width方向。

<!-- cannbot:related:start -->
## 相关

- [AscSetL13dRpt](../cube_data_move/asc_set_l13d_rpt.md)（`related`）：《AscSetL13dRpt》处理“设置Load3Dv2接口的repeat参数。”。《AscLoad3dV2Config》明确提供“用于设置Load3Dv2接口的repeat参数，包括迭代步长、次数和方向。”，其参数、调用或验证步骤直接接入3D L1 到 L0 搬运的 Fmatrix、尺寸、padding、repeat 和配置接口。
<!-- cannbot:related:end -->
