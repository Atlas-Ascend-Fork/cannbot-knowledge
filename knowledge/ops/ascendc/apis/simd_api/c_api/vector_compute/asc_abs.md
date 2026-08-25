---
type: API
title: AscAbs
description: asc_abs（矢量计算）
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_abs.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscAbs

按元素取绝对值，计算公式如下：
函数原型：void asc_abs(__ubuf__ half* dst, __ubuf__ half* src, uint32_t count)
约束：dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [Abs 原地取绝对值后量化丢符号致 int8 坍缩](../../../../runbooks/precision/abs_inplace_overwrites_signed_source_before_quant.md)（`exemplifies`）：Abs 原地取绝对值后量化丢符号致 int8 坍缩说明动态量化 kernel 先 Abs(yNormFp32, yNormFp32) 原地取绝对值再 Muls(1/scale) 量化，会丢失符号、量化的是绝对值，导致 int8 输出坍缩为 ±1 量级、约 50% mismatch；须把 Abs 写入独立 buffer、Muls 作用在原始带符号 tensor 上。
- [AscendC::Abs 规范化 NaN payload 致逐位验收误报](../../../../runbooks/precision/ascendc_abs_nan_payload.md)（`exemplifies`）：AscendC::Abs 规范化 NaN payload 致逐位验收误报说明硬件 AscendC::Abs 把 FP16 NaN 规范化为全 1 payload（0x7fff），numpy.abs 保留原 payload（0x7e00），逐位一致验收误报失败；用位差 511 与 NaN 感知探针判别。
- [Abs](../../basic_api/memory_vector_compute/basic_arithmetic/abs.md)（`same_topic`）：Abs 与《AscAbs》的衔接是：这些卡分别给出 Abs 在 Reg、C Reg、C Vector 路径上的同一绝对值语义；原地覆盖时符号位丢失案例是该操作的直接别名风险。
- [Abs](../../basic_api/reg_vector_compute/basic_arithmetic/abs.md)（`same_topic`）：Abs说明对srcReg中有效元素逐个取绝对值并写入dstReg，复数类型取模。
- [AscAbs](../reg/arithmetic_compute/asc_abs.md)（`same_topic`）：AscAbs说明按元素取绝对值，将结果写入目的操作数dst。
- [AscAbsSync](../deprecated_interface/asc_abs_sync_deprecated.md)（`same_topic`）：《AscAbsSync》处理“已废弃的按元素取绝对值同步计算接口，请改用asc_abs和asc_sync实现精细化调优。”。《AscAbs》提供“asc_abs（矢量计算）”，其具体合同或探针直接接入废弃 AscAbsSync 拆分为 AscAbs 与 asc_sync 的迁移合同。
<!-- cannbot:related:end -->
