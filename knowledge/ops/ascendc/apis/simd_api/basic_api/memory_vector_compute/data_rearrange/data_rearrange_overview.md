---
type: API
title: 数据重排（ISASI）
description: Memory矢量计算ISASI数据重排接口索引页，包含Interleave与DeInterleave。
tags: [task.lookup, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_rearrange_ISASI/data_rearrange_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# 数据重排（ISASI）

提供 Interleave 和 DeInterleave 接口，用于 Memory 矢量计算的数据交织与解交织。Interleave 将 src0 和 src1 中的元素交织存入 dst0 和 dst1，DeInterleave 为其逆操作。

支持 int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、int64_t、uint64_t 数据类型，`count` 必须为偶数。操作数起始地址需 32Byte 对齐，不支持源操作数与目的操作数地址重叠。仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [DeInterleave 两路写反——按偶索引到 dst0 修正](../../../../../runbooks/precision/deinterleave_dst0_is_even_lane_output.md)（`exemplifies`）：DeInterleave 两路写反——按偶索引到 dst0 修正说明Reg 交织拆分把 dst0/dst1 接反会让 interleaved 路线整行错；按 dst0=偶索引、dst1=奇索引接线。
- [数据重排](../../reg_vector_compute/data_reorder/data_reorder.md)（`same_topic`）：数据重排 与《数据重排（ISASI）》的实质衔接是：Reg 数据重排与 memory/C 重排使用同一交织/解交织语义；两张排障卡分别限定 DeInterleave 偶奇输出和 B16 interleave store mask。
- [数据重排](../../../c_api/reg/data_rearrange/data_rearrange.md)（`same_topic`）：数据重排 的核心契约是“寄存器侧数据重排类接口汇总，提供deintlv、intlv等数据交错与解交错重排能力”；数据重排（ISASI） 补充“Memory矢量计算ISASI数据重排接口索引页，包含Interleave与DeInterleave”。
<!-- cannbot:related:end -->
