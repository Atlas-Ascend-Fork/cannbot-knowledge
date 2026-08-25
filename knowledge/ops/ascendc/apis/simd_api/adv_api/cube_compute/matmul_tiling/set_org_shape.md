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

<!-- cannbot:related:start -->
## 相关

- [Matmul Tiling类使用说明](matmul_tiling_usage.md)（`related`）：使用说明把 SetOrgShape 放进创建 tiling 对象、设置类型/形状并调用 GetTiling 的完整流程，可直接确认调用顺序和单核/多核/Batch 场景。
- [SetShape](set_shape.md)（`related`）：SetShape 的 -1 取值需要回落到原始 M/N/K，而 SetOrgShape 正是提供原始完整 shape 的契约；未设置原始 shape 会使 -1 语义缺少来源。
- [SetOrgShape](../matmul_kernel/set_org_shape.md)（`same_topic`）：“SetOrgShape”定义：设置Matmul计算原始完整的形状M、N、K，单位为元素个数。用于运行时修改shape，比如复用同一个Matmul对象，从不同的矩阵块取数据计算。；“SetOrgShape”定义：设置Matmul计算时的原始完整的形状M、N、K或Ka/Kb，单位均为元素个数。。实质衔接：Host tiling 与 Kernel 对象必须对原始 M/N/K 一致；复用对象处理矩阵块时还需区分完整 org shape 与当前 single shape。
<!-- cannbot:related:end -->
