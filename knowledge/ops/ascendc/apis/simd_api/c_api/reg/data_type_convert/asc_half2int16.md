---
type: API
title: AscHalf2Int16
description: 将half类型数据转换为int16_t，并支持多种舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式与饱和模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_half2int16.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscHalf2Int16

将half类型数据转换为int16_t，并支持多种舍入模式，饱和/非饱和模式。

关于舍入模式和饱和/非饱和模式

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器）。用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：half、int16_t。

约束：- mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。
- 开启饱和模式和非饱和模式时，需配置ctrl寄存器，ctrl寄存器

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [__half2int_rd](../../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_half2int_rd.md)（`related`）：__half2int_rd 与《AscHalf2Int16》的实质衔接是：这些卡保持 half 到整数转换并切换 rd/rn/rna/ru/rz 或目标有无符号；C 的 half2int16/32 入口说明向量执行层的目标位宽选择。
- [舍入模式与饱和模式](rounding_mode.md)（`related`）：舍入与饱和说明解释 AscHalf2Int16 的 RINT/ROUND/FLOOR/CEIL/TRUNC 及超范围处理，直接决定边界输入结果。
- [AscHalf2int16](../../vector_compute/asc_half2int16.md)（`same_topic`）：《AscHalf2int16》的任务是“将half类型数据转换为int16_t，并支持多种舍入模式。 - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入 - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入”。《AscHalf2Int16》具体提供“将half类型数据转换为int16_t，并支持多种舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式与饱和模式。”，它直接用于half→int16 的同源同目标实现及五种舍入模式。
- [__half2int_ru](../../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_half2int_ru.md)（`same_topic`）：__half2int_ru 与《AscHalf2Int16》的实质衔接是：__half2int_ru 保持 half→int 并切换 rd/rn/rna/rz，或保持 ceil 改变源/目标类型；C half2int16/32 入口明确向量目标位宽。
<!-- cannbot:related:end -->
