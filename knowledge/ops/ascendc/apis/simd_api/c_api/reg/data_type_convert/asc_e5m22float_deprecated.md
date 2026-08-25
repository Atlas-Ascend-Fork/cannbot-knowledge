---
type: API
title: asc_e5m22float (废弃)
description: 将vector_fp8_e5m2_t类型的源操作数以256B为单位分为四部分，读取其中一部分元素，将其转换成vector_float类型并写入目的操作数。
  - asc_e5m22float：读取第一部分。 - asc_e5m22float_v2：读取第二部分。 - asc_e5m22float_v3：读取第三部分。
  - asc_e5m22float_v4：读取第四部分。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_e5m22float_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# asc_e5m22float (废弃)

将vector_fp8_e5m2_t类型的源操作数以256B为单位分为四部分，读取其中一部分元素，将其转换成vector_float类型并写入目的操作数。

- asc_e5m22float：读取第一部分。

- asc_e5m22float_v2：读取第二部分。

- asc_e5m22float_v3：读取第三部分。

- asc_e5m22float_v4：读取第四部分。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：float、fp8_e5m2_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [asc_float2e5m2 (废弃)](asc_float2e5m2_deprecated.md)（`related`）：《asc_float2e5m2 (废弃)》的任务是“将float类型数据转换为fp8_e5m2类型，支持RINT舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式。”。《asc_e5m22float (废弃)》具体提供“将vector_fp8_e5m2_t类型的源操作数以256B为单位分为四部分，读取其中一部分元素，将其转换成vector_float类型并写入目的操作数。 - asc_e5m22float：读取第一部分。 - asc_e5m22float_v2：读取第二部分。 - asc_e5m22float_v3：读取第三部分。 - asc_e5m22float_v4：读取第四部分。”，它直接用于废弃 float→e5m2 转换的反向转换、舍入饱和和迁移入口。
- [__e5m2x22float2](../../../../simt_api/math_functions/fp8_type/fp8_conversion_functions/_e5m2x22float2.md)（`same_topic`）：__e5m2x22float2 与《asc_e5m22float (废弃)》的实质衔接是：该接口把 packed E5M2 两 lane 解码成 float2；E4M3/HIF8/half2 解码、FP8 类型说明和反向编码入口共同限定格式选择与 round/saturation。
<!-- cannbot:related:end -->
