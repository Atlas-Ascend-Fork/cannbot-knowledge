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
