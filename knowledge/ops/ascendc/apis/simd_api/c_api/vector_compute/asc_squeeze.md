---
type: API
title: AscSqueeze
description: 通过比较掩码src1，将src0中的向量压缩成更短的向量，存储到dst中。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_squeeze.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# AscSqueeze

通过比较掩码src1，将src0中的向量压缩成更短的向量，存储到dst中。
函数原型：void asc_squeeze(__ubuf__ uint16_t* dst, __ubuf__ uint16_t* src0, __ubuf__ uint16_t* src1, uint8_t repeat, uint8_t dst_block_stride, uint8_t src0_block_stride, uint8_t src1_block_stride, uint8_t dst_repeat_stride, uint8_t src0_repeat_stride, uint8_t src1_repeat_stride)
约束：dst、src0、src1的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscSqueeze](../reg/compare_and_select/asc_squeeze.md)（`same_topic`）：通过比较掩码src1，将src0中的向量压缩成更短的向量，存储到dst中；将src中被mask选择的有效元素依次复制到dst中，有效元素在dst中从低到高连续排列，剩余位置元素置为0。两卡都按 mask 压缩有效元素；焦点是 A2/A3 UB 三地址形式，候选是 950 Reg+MaskReg 形式并明确剩余位置清零。
<!-- cannbot:related:end -->
