---
type: API
title: Laneid
description: 获取线程在其所在Warp内的索引。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/Warp_functions/lane_id_functions/laneid.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# laneid

获取线程在其所在Warp内的索引。

函数原型：int32_t laneid()

返回值：线程在其Warp内的索引，当前一个Warp中的线程数量为固定值32，故Lane ID的取值范围为[0,31]。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。
需包含头文件 "simt_api/device_functions.h"。
支持 SIMT 与 SIMD/SIMT 混合编程场景。
