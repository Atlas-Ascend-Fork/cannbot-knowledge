---
type: API
title: AscDeqInt162b8
description: 将 int16_t 转换为 int8_t 或 uint8_t，并把结果写入每个 DataBlock 的高半块或低半块；调用前需通过 asc_set_deq_scale 设置量化参数。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_deq_int162b8.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: [a2, a3]
---


# AscDeqInt162b8

将int16_t类型转换为int8_t或uint8_t类型，并将数据存放在每个DataBlock的高半块或低半块。使用该接口前需要调用asc_set_deq_scale接口设置量化参数。 如下图所示： 计算公式如下：
函数原型：void asc_deq_int162b8_h(__ubuf__ int8_t* dst, __ubuf__ int16_t* src, uint32_t count)
约束：dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscDeqInt322half](asc_deq_int322half.md)（`related`）：int16→b8 的反量化具有不同源/目标位宽与 scale 编码，不能复用 int32→half 契约。
- [AscSetDeqScale](asc_set_deq_scale.md)（`same_topic`）：焦点处理C API DeqScale 与 dequant 计算及头文件约束；AscDeqInt162b8正文说明“将 int16_t 转换为 int8_t 或 uint8_t，并把结果写入每个 DataBlock 的高半块或低半块；调用前需通过 asc_set_deq_scale 设置量化参数”。候选读取 DeqScale 完成 dequant，或给出 C API 可编译的包含与配置边界。
- [AscVdeqInt162b8](asc_vdeq_int162b8.md)（`same_topic`）：AscVdeqInt162b8 与《AscDeqInt162b8》的实质衔接是：AscVdeqInt162b8 调用前必须设置 deq scale；C/basic SetDeqScale 是直接前置契约，AscDeqInt162b8和头文件故障卡用于区分相关符号及正确包含方式。
<!-- cannbot:related:end -->
