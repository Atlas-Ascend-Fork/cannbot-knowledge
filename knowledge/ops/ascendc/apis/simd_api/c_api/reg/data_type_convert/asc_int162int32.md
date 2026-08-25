---
type: API
title: AscInt162Int32
description: 将src中int16_t类型的元素转换为int32_t类型，并将结果写入dst。 由于源操作数与目的操作数类型位宽比为1:2，读取数据时需要将一个VL大小的数据分为两部分，根据不同接口选择输入数据索引为奇数的位置或偶数的位置。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_int162int32.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscInt162Int32

将src中int16_t类型的元素转换为int32_t类型，并将结果写入dst。

由于源操作数与目的操作数类型位宽比为1:2，读取数据时需要将一个VL大小的数据分为两部分，根据不同接口选择输入数据索引为奇数的位置或偶数的位置。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：int16_t、int32_t。

约束：mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscInt162Uint32](asc_int162uint32.md)（`related`）：AscInt162Int32 与本接口共享 16→32 位扩宽及奇/偶半 VL 选择，差别只在目的有符号性。
- [AscInt322Int16](asc_int322int16.md)（`related`）：Int32→Int16 是该提升转换的反向通路，可核对 1:2 位宽转换的奇偶 lane 和掩码布局。
- [AscInt322int16](../../vector_compute/asc_int322int16.md)（`related`）：该接口提供相反的 int16→int32 扩宽并按奇偶输入半段读取；与 focal 的 2:1 窄化一起说明往返转换的 lane 数和数据布局变化。
- [asc_int82int32 (废弃)](asc_int82int32_deprecated.md)（`related`）：《asc_int82int32 (废弃)》说明将int8_t类型转化为int32_t类型。 由于源操作数与目的操作数类型位宽比为1:4，读取数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3。；《AscInt162Int32》说明将src中int16_t类型的元素转换为int32_t类型，并将结果写入dst。 由于源操作数与目的操作数类型位宽比为1:2，读取数据时需要将一个VL大小的数据分为两部分，根据不同接口选择输入数据索引为奇数的位置或偶数的位置。。二者在废弃int8到int32接口可由int8到int16再扩宽到int32表达，废弃索引和uint8对应项用于迁移确认上存在可执行的直接衔接。
<!-- cannbot:related:end -->
