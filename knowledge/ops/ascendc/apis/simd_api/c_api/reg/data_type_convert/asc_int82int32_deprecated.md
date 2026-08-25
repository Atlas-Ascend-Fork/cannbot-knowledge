---
type: API
title: asc_int82int32 (废弃)
description: 将int8_t类型转化为int32_t类型。 由于源操作数与目的操作数类型位宽比为1:4，读取数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_int82int32_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# asc_int82int32 (废弃)

将int8_t类型转化为int32_t类型。

由于源操作数与目的操作数类型位宽比为1:4，读取数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：int32_t、int8_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscInt162Int32](asc_int162int32.md)（`related`）：《asc_int82int32 (废弃)》说明将int8_t类型转化为int32_t类型。 由于源操作数与目的操作数类型位宽比为1:4，读取数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3。；《AscInt162Int32》说明将src中int16_t类型的元素转换为int32_t类型，并将结果写入dst。 由于源操作数与目的操作数类型位宽比为1:2，读取数据时需要将一个VL大小的数据分为两部分，根据不同接口选择输入数据索引为奇数的位置或偶数的位置。。二者在废弃int8到int32接口可由int8到int16再扩宽到int32表达，废弃索引和uint8对应项用于迁移确认上存在可执行的直接衔接。
- [AscInt82int16](asc_int82int16.md)（`related`）：《asc_int82int32 (废弃)》说明将int8_t类型转化为int32_t类型。 由于源操作数与目的操作数类型位宽比为1:4，读取数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3。；《AscInt82int16》说明将int8类型数据转换为int16类型。。二者在废弃int8到int32接口可由int8到int16再扩宽到int32表达，废弃索引和uint8对应项用于迁移确认上存在可执行的直接衔接。
- [asc_uint82uint32 (废弃)](asc_uint82uint32_deprecated.md)（`related`）：《asc_int82int32 (废弃)》说明将int8_t类型转化为int32_t类型。 由于源操作数与目的操作数类型位宽比为1:4，读取数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3。；《asc_uint82uint32 (废弃)》说明将uint8_t类型转化为uint32_t类型。 由于源操作数与目的操作数类型位宽比为1:4，读取数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3。。二者在废弃int8到int32接口可由int8到int16再扩宽到int32表达，废弃索引和uint8对应项用于迁移确认上存在可执行的直接衔接。
- [废弃接口](../../deprecated_interface/deprecated_interface.md)（`related`）：《asc_int82int32 (废弃)》说明将int8_t类型转化为int32_t类型。 由于源操作数与目的操作数类型位宽比为1:4，读取数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3。；《废弃接口》说明废弃接口索引页，汇总矢量计算asc_abs_sync与原子操作asc_set_atomic_add_int等已废弃接口。。二者在废弃int8到int32接口可由int8到int16再扩宽到int32表达，废弃索引和uint8对应项用于迁移确认上存在可执行的直接衔接。
<!-- cannbot:related:end -->
