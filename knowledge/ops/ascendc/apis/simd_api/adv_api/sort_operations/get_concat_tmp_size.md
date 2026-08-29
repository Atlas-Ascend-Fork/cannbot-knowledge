---
type: API
title: GetConcatTmpSize
description: 获取Concat接口所需的临时空间大小，单位为字节。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.ordering]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/sort_operations/GetConcatTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetConcatTmpSize

获取Concat接口所需的临时空间大小。

函数原型：void GetConcatTmpSize(const int32_t repeatTime, uint32_t& maxValue)

参数：repeatTime为重复次数；maxValue输出所需临时空间大小。约束：无。

<!-- cannbot:related:start -->
## 相关

- [Concat（排序操作）](concat.md)（`related`）：获取Concat接口所需的临时空间大小。；对数据进行预处理，将要排序的源操作数src一一对应合入目标数据concat中，预处理完成后可进行Sort操作。。GetConcatTmpSize 给 Concat 排序预处理接口计算所需临时空间，形成 Host 资源准备到 kernel 预处理的直接合同。
<!-- cannbot:related:end -->
