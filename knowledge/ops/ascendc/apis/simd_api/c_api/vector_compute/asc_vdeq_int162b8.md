---
type: API
title: AscVdeqInt162b8
description: 将 int16_t 转换为 int8_t 或 uint8_t，并把结果写入每个 DataBlock 的上半块或下半块；调用前需通过 asc_set_deq_scale 设置量化参数。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_vdeq_int162b8.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: [a2, a3]
---


# AscVdeqInt162b8

将int16_t类型转化为int8_t或uint8_t类型，并将数据存放在每个DataBlock的上半块或下半块。使用该接口前需要调用asc_set_deq_scale设置量化参数。 计算公式如下：
函数原型：void asc_vdeq_int162b8_h(__ubuf__ int8_t* dst, __ubuf__ int16_t* src, uint32_t count)
约束：dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscSetDeqScale](asc_set_deq_scale.md)（`related`）：使用该接口前需要调用asc_set_deq_scale设置量化参数；设置DEQSCALE（量化参数）寄存器的值。前者明确把后者作为 int16 到 8 位反量化转换的调用前置条件，后者提供被消费的 DEQSCALE 配置。
<!-- cannbot:related:end -->
