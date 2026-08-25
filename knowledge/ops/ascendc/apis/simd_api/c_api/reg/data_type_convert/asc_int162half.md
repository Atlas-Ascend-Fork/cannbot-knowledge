---
type: API
title: AscInt162Half
description: 将src中int16_t类型的元素转换为half类型（16位浮点数），并将结果写入dst。源操作数和目的操作数位宽相同，转换后元素数量不变。支持5种舍入模式，关于舍入模式的详细说明请参见舍入模式与饱和模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_int162half.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscInt162Half

将src中int16_t类型的元素转换为half类型（16位浮点数），并将结果写入dst。源操作数和目的操作数位宽相同，转换后元素数量不变。支持5种舍入模式，关于舍入模式

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：half、int16_t。

约束：mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscInt162half](../../vector_compute/asc_int162half.md)（`same_topic`）：《AscInt162half》处理“将int16_t类型数据转换为half类型，支持多种舍入模式： - 不指定舍入模式：无舍入。 - RINT舍入模式：四舍六入五成双舍入。 - ROUND舍入模式：四舍五入舍入。 - FLOOR舍入模式：向负无穷舍入。 - CEIL舍入模式：向正无穷舍入。 - TRUNC舍入模式：向零舍入。”。《AscInt162Half》提供“将src中int16_t类型的元素转换为half类型（16位浮点数），并将结果写入dst。源操作数和目的操作数位宽相同，转换后元素数量不变。支持5种舍入模式，关于舍入模式的详细说明请参见舍入模式与饱和模式。”，其具体合同或探针直接接入int16 到 half 的 C 与 C++ 等价转换合同。
<!-- cannbot:related:end -->
