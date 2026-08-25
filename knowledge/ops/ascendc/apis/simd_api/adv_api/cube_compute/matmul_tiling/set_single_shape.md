---
type: API
title: SetSingleShape
description: 设置Matmul单核计算的形状singleMIn，singleNIn，singleKIn，单位为元素。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetSingleShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SetSingleShape

设置Matmul单核计算的形状singleMIn，singleNIn，singleKIn，单位为元素。

参数：
- singleMIn（输入）：设置的singleMIn大小，单位为元素，默认值为-1。-1表示不设置指定的singleMIn，该值由tiling函数自行计算。
- singleNIn（输入）：设置的singleNIn大小，单位为元素，默认值为-1。-1表示不设置指定的singleNIn，该值由tiling函数自行计算。
- singleKIn（输入）：设置的singleKIn大小，单位为元素，默认值为-1。-1表示不设置指定的singleKIn，该值由tiling函数自行计算。

返回值：-1表示设置失败；0表示设置成功。

约束：
- 在MxMatmul场景中，如果A与B矩阵的位置同时为GM，对singleKIn没有特殊限制，在这种情况下，若scaleA和scaleB的K方向大小（即Ceil(singleKIn, 32)）为奇数，用户需自行在scaleA和scaleB的K方向补0至偶数。
- 在MxMatmul场景中，当输入数据类型为fp4x2_e2m1_t、fp4x2_e1m2_t时，内轴必须为偶数。

<!-- cannbot:related:start -->
## 相关

- [Matmul workspace 预偏移 totalN 回读 banned](../../../../../runbooks/precision/matmul_workspace_totaln_banned.md)（`exemplifies`）：该 Runbook 说明工作区步长必须依据 singleCoreM×singleCoreN 的紧凑输出，不能把全局 totalN 当作 SetSingleShape 后的单核 N。
- [MxMatmul场景](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/mx_matmul_scenario.md)（`explains`）：MxMatmul场景 与《SetSingleShape》的实质衔接是：MxMatmul 需要 MmadMx/AscMmadMx、scaleA/scaleB 及类型/Mad 配置共同实现 C=(scaleA*A)*(scaleB*B)+Bias，量化输出材料补充缩放矩阵契约。
- [SetShape](set_shape.md)（`related`）：SetShape 提供完整 M/N/K，SetSingleShape 再约束单核 M/N/K；多核 Matmul Tiling 必须区分完整问题规模与单核切分规模。
- [SetSingleRange](set_single_range.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《SetSingleShape》明确“设置Matmul单核计算的形状singleMIn，singleNIn，singleKIn，单位为元素。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
- [SetSingleShape](../matmul_kernel/set_single_shape.md)（`related`）：Host tiling 的 SetSingleShape 固化 singleCoreM/N/K，而 Kernel 侧同名接口在复用 Matmul 对象或尾块时运行时修改实际单核 shape；两端共同约束单核计算区域。
- [GetSingleShape](get_single_shape.md)（`same_topic`）：GetSingleShape 与《SetSingleShape》的实质衔接是：GetSingleShape 返回 GetTiling 计算出的单核 M/N/K，必须与 SetSingleShape/Range、baseM/N/K、coreNum 和 TCubeTiling 字段保持一致。
<!-- cannbot:related:end -->
