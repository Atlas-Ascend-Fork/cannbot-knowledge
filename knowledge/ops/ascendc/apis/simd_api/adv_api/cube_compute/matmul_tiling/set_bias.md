---
type: API
title: SetBias
description: EnableBias接口功能与该接口相同，建议使用EnableBias。 设置Bias是否参与运算。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetBias.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetBias

EnableBias接口功能与该接口相同，建议使用EnableBias。 设置Bias是否参与运算。

参数：
- isBiasIn（输入）：设置是否有Bias参与运算

返回值：-1表示设置失败； 0表示设置成功。
