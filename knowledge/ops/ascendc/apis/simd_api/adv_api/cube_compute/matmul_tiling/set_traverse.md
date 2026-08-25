---
type: API
title: SetTraverse
description: 设置固定的Matmul计算方向，M轴优先还是N轴优先。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetTraverse.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# SetTraverse

设置固定的Matmul计算方向，M轴优先还是N轴优先。

参数：
- traverse（输入）：设置固定的Matmul计算方向。可选值：MatrixTraverse::FIRSTM/MatrixTraverse::FIRSTN。 FIRSTM代表先往M轴方向偏移再往N轴方向偏移。 FIRSTN代表先往N轴方向偏移再往M轴方向偏移。

返回值：-1表示设置失败；0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [GetTiling](get_tiling.md)（`related`）：SetTraverse 只写入 FIRSTM/FIRSTN 遍历方向，最终由 GetTiling 消费该配置并产出 TCubeTiling。
<!-- cannbot:related:end -->
