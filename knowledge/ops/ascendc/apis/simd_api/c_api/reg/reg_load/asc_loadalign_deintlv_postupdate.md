---
type: API
title: AscLoadalignDeintlvPostupdate
description: 从UB读取连续2×VL长度数据并在Load过程中完成解交织，分别写入两个目的矢量寄存器，调用后自动更新源地址。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_loadalign_deintlv_postupdate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLoadalignDeintlvPostupdate

asc_loadalign_deintlv_postupdate用于从UB中读取以32B对齐地址src为起始位置的连续2 x VL长度数据。数据按元素类型宽度进行解释，在Load过程中完成解交织后，分别写入两个目的向量寄存器dst0和dst1。 与asc_loadalign_deintlv不同，该接口在完成数据加载后，会对源地址参数src执行后更新操作： 其中，offset的单位为元素个数，实际地址偏移字节数为：offset * sizeof(data_type)。
函数原型：支持的数据类型请参见[数据类型](#data-type)章节。
返回值：无。
约束：src必须为32B对齐地址，且访问范围不能超过UB有效地址上界减去2 x VL，否则可能导致UB越界访问。；在循环中使用本接口时，offset的取值需要保证更新后的src仍满足32B对齐要求。；offset以元素为单位，实际地址步长需要结合源数据类型宽度进行换算。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLoadalignDeintlv](asc_loadalign_deintlv.md)（`same_topic`）：以“asc_loadalign_deintlv用于从UB中读取以32B对齐地址为起始位置的连续2 x VL长度数据。”保持 32B 对齐的基础访问，再按“与asc_loadalign_deintlv不同，该接口在完成数据加载后，会对源地址参数src执行后更新操作： 其中，offset的单位为元素个数，实际地址偏移字节数为：offset * sizeof(data_type)。”把手工 src 推进替换为元素单位 offset，可验证循环步长是否仍落在有效 UB 范围。
<!-- cannbot:related:end -->
