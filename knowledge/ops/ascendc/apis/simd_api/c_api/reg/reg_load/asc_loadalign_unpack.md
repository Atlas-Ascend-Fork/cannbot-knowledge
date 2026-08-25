---
type: API
title: AscLoadalignUnpack
description: 从UB对齐搬入VL/2长度数据并unpack到VL长度，中间位置补0。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign_unpack.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadalignUnpack

对齐数据搬运接口，从UB连续对齐搬入目的操作数，实现解压缩搬入模式：按无符号整型u8/u16/u32加载VL/2长度数据，unpack到VL长度u16/u32/u64类型，中间位置补0。
函数原型：void asc_loadalign_unpack(vector_int8_t& dst, __ubuf__ int8_t* src)
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLoadalignUnpack4](asc_loadalign_unpack4.md)（`related`）：普通 Unpack 将 VL/2 的 u8/u16/u32 扩成双倍位宽，而 Unpack4 固定把 VL/4 u8 扩成 u32；对比可正确选择扩展倍率与目标布局。
- [AscUnpack](../data_compress/asc_unpack.md)（`related`）：LoadAlignUnpack 把 UB 搬入与解包融合，适合读取阶段减少独立 AscUnpack。
- [UnPack](../../../basic_api/reg_vector_compute/data_compression/un_pack.md)（`related`）：LoadAlignUnpack 把对齐搬入与 unpack 融合，适合从 UB 读取时减少独立步骤。
- [AscLoadalignUnpackPostupdate](asc_loadalign_unpack_postupdate.md)（`same_topic`）：Postupdate 变体在完成相同 unpack 对齐加载后还更新源地址，适合循环流式读取；基础变体保持地址不变。
<!-- cannbot:related:end -->
