---
type: API
title: AscMaxScalar
description: 矢量src的逐个元素与标量value比较取最大值，将结果写入目的操作数dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/asc_max_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscMaxScalar

矢量src的逐个元素与标量value比较大小，接着按照对应的比特位将最大值存入dst中。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；value(输入): 源操作数（标量）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、half、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

约束：- 输入src为-0、value为+0的情况下，输出dst为 +0。
- mask未筛选的元素在输出中置零。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscMax](asc_max.md)（`same_topic`）：“矢量src的逐个元素与标量value比较大小，接着按照对应的比特位将最大值存入dst中。”与“该接口根据mask，对源操作数src0、src1进行按元素求最大值操作，将结果写入目的操作数dst。”是双方正文中的具体合同。两端都按 mask 执行逐元素最大值，差别是第二操作数为标量 value 或矢量 src1，互读能选择正确重载并核对广播语义。
- [AscMaxScalar](../../vector_compute/asc_max_scalar.md)（`same_topic`）：矢量src的逐个元素与标量value比较大小，接着按照对应的比特位将最大值存入dst中。计算公式如下：；矢量src的逐个元素与标量value比较大小，接着按照对应的比特位将最大值存入dst中。两卡核心运算完全一致，分别承载 A2/A3 UB 指针接口与 950 寄存器加 mask 接口的跨代迁移契约。
<!-- cannbot:related:end -->
