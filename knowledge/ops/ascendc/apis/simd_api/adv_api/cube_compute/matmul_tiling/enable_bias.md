---
type: API
title: EnableBias
description: 设置Bias是否参与运算，设置的信息必须与Kernel侧保持一致。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/EnableBias.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# EnableBias

设置Bias是否参与运算，设置的信息必须与Kernel侧保持一致。

参数：
- isBiasIn（输入）：设置是否有Bias参与运算。 true：有Bias参与运算。 false：无Bias参与运算。

返回值：-1表示设置失败；0表示设置成功。
