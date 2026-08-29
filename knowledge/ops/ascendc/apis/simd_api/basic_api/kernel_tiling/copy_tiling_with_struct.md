---
type: API
title: COPY_TILING_WITH_STRUCT
description: 拷贝Tiling结构体，并返回指向拷贝后的Tiling结构体的指针。该宏适用于嵌套结构体场景，可拷贝结构体的子结构体成员变量。该宏将指定结构体拷贝至栈上，适用于频繁访问Tiling数据的场景，能够加快数据访问速度。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.tiling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/COPY_TILING_WITH_STRUCT.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# COPY_TILING_WITH_STRUCT

以结构体方式拷贝 Tiling 数据。通过宏展开从 GM 搬运 Tiling 数据到 Local Memory 并填充到结构体。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [COPY_TILING_WITH_ARRAY](copy_tiling_with_array.md)（`same_topic`）：适用于拷贝一个结构体的数组成员变量的场景。；以结构体方式拷贝 Tiling 数据。通过宏展开从 GM 搬运 Tiling 数据到 Local Memory 并填充到结构体。支持 950/a2/a3。。两者是同一 Tiling 数据搬运链的互补宏：一个定位结构体数组成员，另一个填充结构体整体，选择取决于目标字段形态。
<!-- cannbot:related:end -->
