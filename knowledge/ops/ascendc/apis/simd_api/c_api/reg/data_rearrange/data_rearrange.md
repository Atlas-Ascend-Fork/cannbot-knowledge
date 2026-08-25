---
type: API
title: 数据重排
description: 寄存器侧数据重排类接口汇总，提供deintlv、intlv等数据交错与解交错重排能力。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_rearrange/data_rearrange.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 数据重排

提供 asc_intlv 和 asc_deintlv 接口，用于寄存器级数据交织与解交织。asc_intlv 将 src0 和 src1 中的元素交织存入 dst0 和 dst1，asc_deintlv 为其逆操作。

操作数为掩码寄存器时按位宽分组交织（b32 以 4bit 为一组，b16 以 2bit 为一组）；操作数为矢量数据寄存器时以元素为单位交织。支持 int8_t、uint8_t、half、bfloat16_t、int16_t、int32_t、float 等多种数据类型。仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [数据重排](../../../basic_api/reg_vector_compute/data_reorder/data_reorder.md)（`same_topic`）：数据重排 与《数据重排》的实质衔接是：Reg 数据重排与 memory/C 重排使用同一交织/解交织语义；两张排障卡分别限定 DeInterleave 偶奇输出和 B16 interleave store mask。
- [数据重排（ISASI）](../../../basic_api/memory_vector_compute/data_rearrange/data_rearrange_overview.md)（`same_topic`）：数据重排 的核心契约是“寄存器侧数据重排类接口汇总，提供deintlv、intlv等数据交错与解交错重排能力”；数据重排（ISASI） 补充“Memory矢量计算ISASI数据重排接口索引页，包含Interleave与DeInterleave”。
<!-- cannbot:related:end -->
