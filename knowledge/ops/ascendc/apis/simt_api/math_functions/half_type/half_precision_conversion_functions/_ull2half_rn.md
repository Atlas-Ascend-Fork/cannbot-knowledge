---
type: API
title: __ull2half_rn
description: 遵循CAST_RINT模式，将uint64类型数据转换为half类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__ull2half_rn.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __ull2half_rn

功能：遵循CAST_RINT模式，将uint64类型数据转换为half类型数据，返回转换后的值。

函数原型：half __ull2half_rn(const unsigned long long int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_RINT模式转换成的half类型数据。本接口受全局饱和寄存器影响，。特殊值：0→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__ull2half_rd](_ull2half_rd.md)（`same_topic`）：__ull2half_rd 与《__ull2half_rn》的实质衔接是：这些接口共享 uint64→half 或相邻 signed/uint32 输入，RD/RZ/RN/RNA/RU 用于核对大整数窄化的舍入与符号边界。
- [__ull2half_rna](_ull2half_rna.md)（`same_topic`）：__ull2half_rna 与《__ull2half_rn》的实质衔接是：uint64→half RNA 与其他舍入、有符号、bfloat16/float 目标变体共享大整数输入；UINT64 量化卡提供实际位宽约束。
- [__ull2half_ru](_ull2half_ru.md)（`same_topic`）：《__ull2half_ru》说明遵循CAST_CEIL模式，将uint64类型数据转换为half类型数据，返回转换后的值。；《__ull2half_rn》说明遵循CAST_RINT模式，将uint64类型数据转换为half类型数据，返回转换后的值。。二者在uint64到half的ru只改变舍入方向，同源同目标的rd/rn/rna/rz接口是直接选择集合上存在可执行的直接衔接。
- [__ull2half_rz](_ull2half_rz.md)（`same_topic`）：RZ 对同一 uint64→half 转换朝零截断，与 RN 的最近偶数行为直接对照。
<!-- cannbot:related:end -->
