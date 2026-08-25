---
type: API
title: 废弃接口
description: 废弃接口索引页，汇总矢量计算asc_abs_sync与原子操作asc_set_atomic_add_int等已废弃接口。
tags: [task.lookup, topic.quality.compatibility.deprecation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/deprecated_interface/deprecated_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# 废弃接口（C API）

SIMD C API已废弃接口集合，不建议在新算子开发中使用。包含两类：矢量计算类废弃接口asc_abs_sync（同步模式的绝对值计算，已被异步接口asc_abs替代，使用异步接口可避免不必要的同步等待）和原子操作类废弃接口asc_set_atomic_add_int（原子加设置接口，已被新的原子操作机制替代）。使用废弃接口可能导致兼容性问题，开发者应查阅对应替代接口的文档。

<!-- cannbot:related:start -->
## 相关

- [asc_float2e5m2 (废弃)](../reg/data_type_convert/asc_float2e5m2_deprecated.md)（`related`）：《asc_float2e5m2 (废弃)》的任务是“将float类型数据转换为fp8_e5m2类型，支持RINT舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式。”。《废弃接口》具体提供“废弃接口索引页，汇总矢量计算asc_abs_sync与原子操作asc_set_atomic_add_int等已废弃接口。”，它直接用于废弃 float→e5m2 转换的反向转换、舍入饱和和迁移入口。
- [asc_int4x22bfloat16 (废弃)](../reg/data_type_convert/asc_int4x22bfloat16_deprecated.md)（`related`）：asc_int4x22bfloat16 (废弃) 与《废弃接口》的实质衔接是：该废弃 int4x2→bfloat16 接口没有等价现行候选；废弃接口清单说明迁移状态，AscInt4ToHalf 仅提供仍可用的 int4 输入转换方向而非等价替换。
- [asc_int82int32 (废弃)](../reg/data_type_convert/asc_int82int32_deprecated.md)（`related`）：《asc_int82int32 (废弃)》说明将int8_t类型转化为int32_t类型。 由于源操作数与目的操作数类型位宽比为1:4，读取数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3。；《废弃接口》说明废弃接口索引页，汇总矢量计算asc_abs_sync与原子操作asc_set_atomic_add_int等已废弃接口。。二者在废弃int8到int32接口可由int8到int16再扩宽到int32表达，废弃索引和uint8对应项用于迁移确认上存在可执行的直接衔接。
- [asc_int4x22half (废弃)](../reg/data_type_convert/asc_int4x22half_deprecated.md)（`same_topic`）：asc_int4x22half (废弃) 与《废弃接口》的实质衔接是：该废弃接口把 packed int4x2 转 half；同源 bfloat16/int16、逆向转换、废弃接口表及当前 AscInt4ToHalf 用于迁移并核对 packed lane。
- [废弃接口](../../../appendix/deprecated_interface.md)（`same_topic`）：两张卡都是 C API 废弃清单：右卡列出 SIMD C API 的局部废弃项，左卡覆盖更完整的跨模块清单并给出推荐替代；迁移旧调用时可在同一废弃契约下补齐替代入口。
<!-- cannbot:related:end -->
