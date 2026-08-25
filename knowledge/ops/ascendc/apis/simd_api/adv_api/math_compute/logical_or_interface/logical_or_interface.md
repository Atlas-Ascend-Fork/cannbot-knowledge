---
type: API
title: LogicalOr接口
description: 按元素进行逻辑或操作，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/LogicalOr_interface/LogicalOr_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# LogicalOr接口

-   **LogicalOr**

-   **GetLogicalOrMaxMinTmpSize**

-   **GetLogicalOrTmpBufferFactorSize**

<!-- cannbot:related:start -->
## 相关

- [LogicalOrs](../logical_ors_interface/logical_ors.md)（`related`）：LogicalOrs 与《LogicalOr接口》的实质衔接是：LogicalOrs 的接口页和两种临时空间查询支撑 vector-scalar 逻辑或，LogicalOr 是 vector-vector 对应形态并共享真假判定规则。
- [LogicalOrs接口](../logical_ors_interface/logical_ors_interface.md)（`related`）：《LogicalOrs接口》说明输入矢量每个元素与标量进行逻辑或操作，并提供临时空间大小获取接口。；《LogicalOr接口》说明按元素进行逻辑或操作，并提供临时空间大小获取接口。。二者在LogicalOrs是矢量与标量逻辑或，Kernel调用和两种workspace查询必须配套；LogicalOr用于区分双Tensor语义上存在可执行的直接衔接。
- [GetLogicalOrMaxMinTmpSize](get_logical_or_max_min_tmp_size.md)（`same_topic`）：GetLogicalOrMaxMinTmpSize 与《LogicalOr接口》的实质衔接是：GetLogicalOrMaxMinTmpSize 与 factor 查询共同决定 LogicalOr 的 sharedTmpBuffer，接口页和 kernel 操作说明该 tiling 结果的唯一消费方。
<!-- cannbot:related:end -->
