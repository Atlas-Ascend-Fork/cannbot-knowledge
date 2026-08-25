---
type: API
title: GetArangeMaxMinTmpSize
description: 用于获取Arange Tiling参数：Arange接口能完成计算所需最大临时空间大小max和最小临时空间大小min。 由于Arange接口内部不需要用到临时空间，max和min均返回0。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.indexing]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/index_compute/GetArangeMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GetArangeMaxMinTmpSize

用于获取Arange Tiling参数：Arange接口能完成计算所需最大临时空间大小max和最小临时空间大小min。 由于Arange接口内部不需要用到临时空间，max和min均返回0。

函数原型：
void GetArangeMaxMinTmpSize(uint32_t& maxValue, uint32_t& minValue)
void GetArithProgressionMaxMinTmpSize(uint32_t& maxValue, uint32_t& minValue)

参数：
- maxValue（输出）：Arange接口能完成计算所需最大临时空间大小。 说明：maxValue仅作为参考值，有可能大于Unified Buffer剩余空间的大小，该场景下，开发者需要根据Unified Buffer剩余空间的大小来选取合适的临时空间大小。
- minValue（输出）：Arange接口能完成计算所需最小临时空间大小。

<!-- cannbot:related:start -->
## 相关

- [Arange](../../basic_api/reg_vector_compute/index_operations/arange.md)（`related`）：Reg Arange 是不依赖高阶 workspace 的寄存器路径。
- [Arange（索引计算）](arange.md)（`related`）：Arange 的 sharedTmpBuffer 必须由 Host sizing 接口按 firstValue、diff、count 和 dtype 给出合法上下界，最小值是正确性门槛。
- [GetAntiQuantizeMaxMinTmpSize](../quantization/get_anti_quantize_max_min_tmp_size.md)（`related`）：AntiQuantize 是不同算子，workspace 公式不能因返回类型相同复用。
<!-- cannbot:related:end -->
