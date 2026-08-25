---
type: API
title: Broadcast（张量变换）
description: 将输入按照输出shape进行广播。 比如A的shape为\(2,1\)，广播的目标shape为\(2,16\)，则会将原来的一列扩展为相同的16列。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/tensor_transform/Broadcast.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Broadcast

将输入按照输出shape进行广播。例如将shape为(m,1)的数据广播到(m,k)，即将一列扩展为相同的k列。模板参数T支持half/float。

提供通过sharedTmpBuffer传入临时空间或由接口框架申请两种重载。临时空间大小通过GetBroadCastMaxMinTmpSize获取。接口参数：dstTensor输出广播结果；srcTensor输入数据；sharedTmpBuffer临时缓存；broadcastInfo含输入输出shape信息。TPosition支持VECIN/VECCALC/VECOUT。

约束：遵循通用地址对齐约束。
