---
type: API
title: Sum接口
description: 获取最后一个维度的元素总和，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/Sum_interface/Sum_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Sum接口

提供 Sum 归约求和接口及 GetSumMaxMinTmpSize 临时空间查询接口。Sum 对最后一个维度求元素总和，向量输入则全部相加，矩阵输入则沿最后一维对每行求和。最多支持二维输入，不支持更高维度。

接口要求内轴长度 32Byte 对齐，通过 SumParams 传入 outter（外轴长度）、inner（内轴 32Byte 补齐后元素个数）和 n（内轴实际元素个数）。支持 half、float 数据类型。临时空间支持 `sharedTmpBuffer` 传入或框架申请，大小通过 GetSumMaxMinTmpSize 获取。
