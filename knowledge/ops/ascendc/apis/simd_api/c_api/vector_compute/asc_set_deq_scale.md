---
type: API
title: AscSetDeqScale
description: 设置DEQSCALE（量化参数）寄存器的值。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_set_deq_scale.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscSetDeqScale

设置DEQSCALE（量化参数）寄存器的值。
函数原型：void asc_set_deq_scale(__ubuf__ uint64_t* tmp, float scale_arr[ASC_VDEQ_SIZE], int16_t offset_arr[ASC_VDEQ_SIZE], bool sign_mode_arr[ASC_VDEQ_SIZE])
参数：tmp（输入）：一块临时内存区域，用于存储一组大小为16的量化参数。；scale_arr（输入）：float数组类型，大小为16，用于存储一组量化参数。；offset_arr（输入）：int16_t数组类型，大小为16，用于存储一组量化参数。；sign_mode_arr（输入）：bool数组类型，大小为16，用于存储一组量化参数。；scale（half）（输入）：量化参数，half类型。适用于cast_deq等接口的int32_t转化为half的场景。；scale（float）（输入）：量化参数，float类型。设置DEQSCALE寄存器的值。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscVdeqInt162b8](asc_vdeq_int162b8.md)（`related`）：使用该接口前需要调用asc_set_deq_scale设置量化参数；设置DEQSCALE（量化参数）寄存器的值。前者明确把后者作为 int16 到 8 位反量化转换的调用前置条件，后者提供被消费的 DEQSCALE 配置。
<!-- cannbot:related:end -->
