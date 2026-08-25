---
type: API
title: asc_float2e5m2 (废弃)
description: 将float类型数据转换为fp8_e5m2类型，支持RINT舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_float2e5m2_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# asc_float2e5m2 (废弃)

将float类型数据转换为fp8_e5m2类型，支持RINT舍入模式，饱和/非饱和模式。

关于舍入模式和饱和/非饱和模式

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：float、fp8_e5m2_t。

约束：- 开启饱和模式和非饱和模式时，需配置ctrl寄存器，ctrl寄存器

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [asc_e5m22float (废弃)](asc_e5m22float_deprecated.md)（`related`）：《asc_float2e5m2 (废弃)》的任务是“将float类型数据转换为fp8_e5m2类型，支持RINT舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式。”。《asc_e5m22float (废弃)》具体提供“将vector_fp8_e5m2_t类型的源操作数以256B为单位分为四部分，读取其中一部分元素，将其转换成vector_float类型并写入目的操作数。 - asc_e5m22float：读取第一部分。 - asc_e5m22float_v2：读取第二部分。 - asc_e5m22float_v3：读取第三部分。 - asc_e5m22float_v4：读取第四部分。”，它直接用于废弃 float→e5m2 转换的反向转换、舍入饱和和迁移入口。
- [asc_float2e4m3 (废弃)](asc_float2e4m3_deprecated.md)（`related`）：《asc_float2e5m2 (废弃)》的任务是“将float类型数据转换为fp8_e5m2类型，支持RINT舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式。”。《asc_float2e4m3 (废弃)》具体提供“将float类型转化为fp8_e4m3fn_t类型，支持RINT舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式。 由于源操作数与目的操作数类型位宽比为4:1，写入数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3。”，它直接用于废弃 float→e5m2 转换的反向转换、舍入饱和和迁移入口。
- [废弃接口](../../deprecated_interface/deprecated_interface.md)（`related`）：《asc_float2e5m2 (废弃)》的任务是“将float类型数据转换为fp8_e5m2类型，支持RINT舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式。”。《废弃接口》具体提供“废弃接口索引页，汇总矢量计算asc_abs_sync与原子操作asc_set_atomic_add_int等已废弃接口。”，它直接用于废弃 float→e5m2 转换的反向转换、舍入饱和和迁移入口。
- [类型转换](data_type_convert.md)（`related`）：《asc_float2e5m2 (废弃)》的任务是“将float类型数据转换为fp8_e5m2类型，支持RINT舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式。”。《类型转换》具体提供“寄存器侧类型转换类接口汇总，覆盖bfloat16、half、float、int等数据类型间的相互转换及取整操作。”，它直接用于废弃 float→e5m2 转换的反向转换、舍入饱和和迁移入口。
- [舍入模式与饱和模式](rounding_mode.md)（`related`）：《asc_float2e5m2 (废弃)》的任务是“将float类型数据转换为fp8_e5m2类型，支持RINT舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式。”。《舍入模式与饱和模式》具体提供“在进行数据类型转换时，Ascend C API支持多种舍入模式和饱和模式。这些模式决定了当源数据类型转换为不同精度或范围的目标数据类型时，如何处理数值的舍入和溢出问题。”，它直接用于废弃 float→e5m2 转换的反向转换、舍入饱和和迁移入口。
- [__e5m2x22float2](../../../../simt_api/math_functions/fp8_type/fp8_conversion_functions/_e5m2x22float2.md)（`same_topic`）：《asc_float2e5m2 (废弃)》的任务是“将float类型数据转换为fp8_e5m2类型，支持RINT舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式。”。《__e5m2x22float2》具体提供“将float8_e5m2x2_t类型数据的两个分量转换为浮点数，返回转换后的float2类型数据。”，它直接用于废弃 float→e5m2 转换的反向转换、舍入饱和和迁移入口。
<!-- cannbot:related:end -->
