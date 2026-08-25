---
type: API
title: AscStorealignIntlv
description: 从两个矢量数据寄存器交错搬出元素到UB，将src0、src1的元素交错存储于dst中，存储长度为VL*2。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_storealign_intlv.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscStorealignIntlv

从矢量数据寄存器交错搬出到UB的接口，忽略mask，将src0、src1中的元素交错存储于dst中，存储长度为VL*2。支持数据类型为b8、b16、b32。
函数原型：void asc_storealign_intlv(__ubuf__ int8_t* dst_align32b, vector_int8_t src0, vector_int8_t src1)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [RoPE DIST_INTLV_B16 store mask 致零值](../../../../../runbooks/precision/rope_dist_intlv_b16_store_mask.md)（`exemplifies`）：AscStorealignIntlv 与《RoPE DIST_INTLV_B16 store mask 致零值》的实质衔接是：AscStorealignIntlv 忽略 mask，将两路 Reg lane 交错写 UB；普通 StoreAlign、C++ Store 和 DeIntlv 反向操作及 B16 交错故障直接核对偶奇 lane。
- [AscDeintlv](../data_rearrange/asc_deintlv.md)（`same_topic`）：AscStorealignIntlv 与《AscDeintlv》的实质衔接是：AscStorealignIntlv 忽略 mask，将两路 Reg lane 交错写 UB；普通 StoreAlign、C++ Store 和 DeIntlv 反向操作及 B16 交错故障直接核对偶奇 lane。
- [AscStorealign](asc_storealign.md)（`same_topic`）：AscStorealignIntlv 与《AscStorealign》的实质衔接是：AscStorealignIntlv 忽略 mask，将两路 Reg lane 交错写 UB；普通 StoreAlign、C++ Store 和 DeIntlv 反向操作及 B16 交错故障直接核对偶奇 lane。
- [StoreAlignContinuous](../../../basic_api/reg_vector_compute/reg_data_store/store_align_continuous.md)（`same_topic`）：AscStorealignIntlv 与《StoreAlignContinuous》的实质衔接是：AscStorealignIntlv 忽略 mask，将两路 Reg lane 交错写 UB；普通 StoreAlign、C++ Store 和 DeIntlv 反向操作及 B16 交错故障直接核对偶奇 lane。
- [reg数据搬出](reg_store.md)（`same_topic`）：AscStorealignIntlv 与《reg数据搬出》的实质衔接是：AscStorealignIntlv 忽略 mask，将两路 Reg lane 交错写 UB；普通 StoreAlign、C++ Store 和 DeIntlv 反向操作及 B16 交错故障直接核对偶奇 lane。
<!-- cannbot:related:end -->
