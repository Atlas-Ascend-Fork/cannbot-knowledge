---
type: API
title: DataCacheCleanAndInvalid
description: 解决Data Cache与GM一致性问题，将脏数据写回GM并将指定Cache Line标记为无效，确保下次访问从GM重新加载。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cache_control/DataCacheCleanAndInvalid.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# DataCacheCleanAndInvalid

清除并失效Data Cache，确保Scalar单元通过Data Cache读取的GM数据与DMA单元直接写入GM的数据保持一致。当DMA向GM写入数据后，若Scalar需要读取该数据，需先调用本接口清除Data Cache中的旧缓存，否则可能读到过期数据。

函数原型提供基于GM地址和长度的清除方式。参数包含GM地址指针和数据长度。约束：仅在Scalar单元访问GM时需要；DMA搬运不涉及Cache一致性问题。头文件：basic_api/kernel_operator_cache_intf.h。
