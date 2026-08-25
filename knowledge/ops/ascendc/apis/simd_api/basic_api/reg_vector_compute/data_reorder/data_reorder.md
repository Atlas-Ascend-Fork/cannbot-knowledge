---
type: API
title: 数据重排
description: Reg矢量计算数据重排接口索引页，包含Interleave与DeInterleave。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/data_reorder/data_reorder.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 数据重排

提供 Interleave 和 DeInterleave 接口，用于寄存器级元素交织与解交织。Interleave 将 srcReg0 和 srcReg1 中的元素交织存入 dstReg0 和 dstReg1，DeInterleave 为其逆操作。

操作数为 RegTensor 类型，由编译器自动推导。仅 Ascend 950PR/Ascend 950DT 支持，需在 VF 函数内调用。

<!-- cannbot:related:start -->
## 相关

- [DeInterleave 两路写反——按偶索引到 dst0 修正](../../../../../runbooks/precision/deinterleave_dst0_is_even_lane_output.md)（`exemplifies`）：数据重排 与《DeInterleave 两路写反——按偶索引到 dst0 修正》的实质衔接是：Reg 数据重排与 memory/C 重排使用同一交织/解交织语义；两张排障卡分别限定 DeInterleave 偶奇输出和 B16 interleave store mask。
- [RoPE DIST_INTLV_B16 store mask 致零值](../../../../../runbooks/precision/rope_dist_intlv_b16_store_mask.md)（`exemplifies`）：数据重排 与《RoPE DIST_INTLV_B16 store mask 致零值》的实质衔接是：Reg 数据重排与 memory/C 重排使用同一交织/解交织语义；两张排障卡分别限定 DeInterleave 偶奇输出和 B16 interleave store mask。
- [数据重排](../../../c_api/reg/data_rearrange/data_rearrange.md)（`same_topic`）：数据重排 与《数据重排》的实质衔接是：Reg 数据重排与 memory/C 重排使用同一交织/解交织语义；两张排障卡分别限定 DeInterleave 偶奇输出和 B16 interleave store mask。
- [数据重排（ISASI）](../../memory_vector_compute/data_rearrange/data_rearrange_overview.md)（`same_topic`）：数据重排 与《数据重排（ISASI）》的实质衔接是：Reg 数据重排与 memory/C 重排使用同一交织/解交织语义；两张排障卡分别限定 DeInterleave 偶奇输出和 B16 interleave store mask。
<!-- cannbot:related:end -->
