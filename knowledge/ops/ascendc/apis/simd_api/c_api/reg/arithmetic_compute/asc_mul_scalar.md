---
type: API
title: AscMulScalar
description: 对源操作数src与标量value按元素做乘法运算，将结果写入目的操作数dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/asc_mul_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscMulScalar

对源操作数src、value进行按元素做乘操作，将结果写入目的操作数dst。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；value(输入): 源操作数（标量）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：float、half、int16_t、int32_t、uint16_t、uint32_t。

约束：mask对应位置为0的元素不参与计算，且在输出中置零。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscMuls](asc_muls_deprecated.md)（`same_topic`）：对源操作数src和value进行乘法运算再按照数据类型转换的ROUND舍入模式转成half类型，根据mask将结果写入目的操作数dst。；对源操作数src、value进行按元素做乘操作，将结果写入目的操作数dst。。两端都执行寄存器向量与标量的 mask 乘法；AscMuls 还固定 ROUND 后转 half 且已标废弃，AscMulScalar 是更通用的标量乘接口，互读可完成迁移时的语义核对。
<!-- cannbot:related:end -->
