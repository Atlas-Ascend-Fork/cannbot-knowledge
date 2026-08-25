---
type: API
title: AscHalf2Int32
description: 将half类型数据转为int32_t类型，支持多种舍入模式，源操作数与目的操作数位宽比为1:2。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_half2int32.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscHalf2Int32

将half类型数据转为int32_t类型，并支持多种舍入模式。

关于舍入模式
由于源操作数与目的操作数类型位宽比为1:2，读取数据时需要将一个VL大小的数据分为两部分，根据不同接口选择输入数据索引为奇数的位置或偶数的位置。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器）。用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：half、int32_t。

约束：mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscHalf2int32](../../vector_compute/asc_half2int32.md)（`related`）：两者都完成 half→int32 并支持 RINT/ROUND/FLOOR/CEIL/TRUNC；Reg 版在寄存器中按 1:2 lane 布局输出，Vector 版在 UB 内存上要求 32B 对齐。
- [__half2int_rd](../../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_half2int_rd.md)（`related`）：__half2int_rd 与《AscHalf2Int32》的实质衔接是：这些卡保持 half 到整数转换并切换 rd/rn/rna/ru/rz 或目标有无符号；C 的 half2int16/32 入口说明向量执行层的目标位宽选择。
- [__half2int_rn](../../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_half2int_rn.md)（`related`）：SIMT __half2int_rn 是标量 half→int32 的 ties-to-even 路径，和 Reg RINT 版本可按标量线程与寄存器向量执行模型选择。
- [舍入模式与饱和模式](rounding_mode.md)（`related`）：AscHalf2Int32 的五种后缀由舍入模式定义；该卡给出 RINT、ROUND、FLOOR、CEIL、TRUNC 与饱和行为的选择依据。
- [__half2int_ru](../../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_half2int_ru.md)（`same_topic`）：__half2int_ru 与《AscHalf2Int32》的实质衔接是：__half2int_ru 保持 half→int 并切换 rd/rn/rna/rz，或保持 ceil 改变源/目标类型；C half2int16/32 入口明确向量目标位宽。
<!-- cannbot:related:end -->
