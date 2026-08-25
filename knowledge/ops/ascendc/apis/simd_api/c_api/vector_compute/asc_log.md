---
type: API
title: AscLog
description: asc_log（矢量计算）
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_log.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscLog

按元素取自然对数，计算公式如下：
函数原型：void asc_log(__ubuf__ half* dst, __ubuf__ half* src, uint32_t count)
参数：dst（输出）：目的操作数（矢量）的起始地址。；src（输入）：源操作数（矢量）的起始地址。；count（输入）：参与计算的元素个数。
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [Log](../../adv_api/math_compute/log_interface/log.md)（`related`）：高阶 Log 同样覆盖自然对数，并扩展到 base 2/10 和临时空间管理；AscLog 是 UB 上 half 自然对数的 C API 入口。
- [Log](../../basic_api/reg_vector_compute/basic_arithmetic/log.md)（`related`）：Reg Log 在 MaskReg 控制下对寄存器逐元素求自然对数，和 AscLog 的 UB 指针 count 模式形成按数据驻留位置的接口选择。
<!-- cannbot:related:end -->
