---
type: API
title: SetOrgShape
description: 设置Matmul计算时的原始完整的形状M、N、K或Ka/Kb，单位均为元素个数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetOrgShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetOrgShape

设置Matmul计算时的原始完整的形状M、N、K或Ka/Kb，单位均为元素个数。

参数：
- orgMIn（输入）：设置原始完整的形状M大小，单位为元素。
- orgNIn（输入）：设置原始完整的形状N大小，单位为元素。
- orgKIn（输入）：设置原始完整的形状K大小，单位为元素。原始完整形状Ka=Kb时可设置。
- orgKaIn（输入）：设置矩阵A原始完整的形状Ka大小，单位为元素。
- orgKbIn（输入）：设置矩阵B原始完整的形状Kb大小，单位为元素。

返回值：-1表示设置失败； 0表示设置成功。
