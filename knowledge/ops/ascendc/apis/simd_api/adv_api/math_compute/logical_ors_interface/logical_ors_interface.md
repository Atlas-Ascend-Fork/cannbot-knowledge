---
type: API
title: LogicalOrs接口
description: 输入矢量每个元素与标量进行逻辑或操作，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/LogicalOrs_interface/LogicalOrs_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# LogicalOrs接口

-   **LogicalOrs**

-   **GetLogicalOrsMaxMinTmpSize**

-   **GetLogicalOrsTmpBufferFactorSize**

<!-- cannbot:related:start -->
## 相关

- [LogicalOr](../logical_or_interface/logical_or.md)（`related`）：《LogicalOrs接口》说明输入矢量每个元素与标量进行逻辑或操作，并提供临时空间大小获取接口。；《LogicalOr》说明按元素进行或操作。当输入的数据类型不是bool时，零被视为False，非零数据被视为True。。二者在LogicalOrs是矢量与标量逻辑或，Kernel调用和两种workspace查询必须配套；LogicalOr用于区分双Tensor语义上存在可执行的直接衔接。
- [LogicalOr接口](../logical_or_interface/logical_or_interface.md)（`related`）：《LogicalOrs接口》说明输入矢量每个元素与标量进行逻辑或操作，并提供临时空间大小获取接口。；《LogicalOr接口》说明按元素进行逻辑或操作，并提供临时空间大小获取接口。。二者在LogicalOrs是矢量与标量逻辑或，Kernel调用和两种workspace查询必须配套；LogicalOr用于区分双Tensor语义上存在可执行的直接衔接。
- [GetLogicalOrsMaxMinTmpSize](get_logical_ors_max_min_tmp_size.md)（`same_topic`）：《LogicalOrs接口》说明输入矢量每个元素与标量进行逻辑或操作，并提供临时空间大小获取接口。；《GetLogicalOrsMaxMinTmpSize》说明在host侧获取LogicalOrs接口预留或申请临时空间的最大和最小值，用于Tiling参数传递。二者在LogicalOrs是矢量与标量逻辑或，Kernel调用和两种workspace查询必须配套；LogicalOr用于区分双Tensor语义上存在可执行的直接衔接。
- [GetLogicalOrsTmpBufferFactorSize](get_logical_ors_tmp_buffer_factor_size.md)（`same_topic`）：《LogicalOrs接口》说明输入矢量每个元素与标量进行逻辑或操作，并提供临时空间大小获取接口。；《GetLogicalOrsTmpBufferFactorSize》说明获取LogicalOrs接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量。二者在LogicalOrs是矢量与标量逻辑或，Kernel调用和两种workspace查询必须配套；LogicalOr用于区分双Tensor语义上存在可执行的直接衔接。
- [LogicalOrs](logical_ors.md)（`same_topic`）：《LogicalOrs接口》说明输入矢量每个元素与标量进行逻辑或操作，并提供临时空间大小获取接口。；《LogicalOrs》说明输入矢量每个元素与标量进行或操作，非零视为真。二者在LogicalOrs是矢量与标量逻辑或，Kernel调用和两种workspace查询必须配套；LogicalOr用于区分双Tensor语义上存在可执行的直接衔接。
<!-- cannbot:related:end -->
