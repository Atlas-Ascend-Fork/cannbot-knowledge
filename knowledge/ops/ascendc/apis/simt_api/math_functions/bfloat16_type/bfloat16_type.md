---
type: API
title: bfloat16类型
description: bfloat16类型函数总入口，涵盖算术、比较、数学库及精度转换函数，并包含bfloat16x2类型对应函数。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_type.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# bfloat16类型

bfloat16 类型 SIMT 数学函数的总入口，按功能分为算术函数、比较函数、数学库函数和精度转换函数四个子类。同时提供 bfloat16x2 双分量向量类型的对应算术、比较和数学库函数，用于在 AICore 上实现高效的低精度并行计算。

<!-- cannbot:related:start -->
## 相关

- [AscendC 标量类型误加命名空间导致模板分发编译失败](../../../../runbooks/compilation/device_half_bfloat16_types_are_global.md)（`exemplifies`）：《bfloat16类型》说明bfloat16类型函数总入口，涵盖算术、比较、数学库及精度转换函数，并包含bfloat16x2类型对应函数。；《AscendC 标量类型误加命名空间导致模板分发编译失败》说明CANN 9.0.1 的 device 标量类型 half 与 bfloat16_t 位于全局作用域；host dtype 分发实例化 kernel 时不能写成 AscendC::half 或 AscendC::bfloat16_t。。二者在bfloat16类型入口的实际使用受全局类型命名、B16边界转换和提升后lane宽度约束，而非由平台或版本过滤上存在可执行的直接衔接。
- [b16 提升 fp32 比较后按存储宽度分块会漏掉后半 lane](../../../../runbooks/precision/compute_lane_count_must_follow_promoted_fp32_width.md)（`exemplifies`）：《bfloat16类型》说明bfloat16类型函数总入口，涵盖算术、比较、数学库及精度转换函数，并包含bfloat16x2类型对应函数。；《b16 提升 fp32 比较后按存储宽度分块会漏掉后半 lane》说明2-byte 数据提升为 fp32 比较时，分块宽度必须按比较类型的单 repeat lane 数计算，否则后半 lane 不更新。。二者在bfloat16类型入口的实际使用受全局类型命名、B16边界转换和提升后lane宽度约束，而非由平台或版本过滤上存在可执行的直接衔接。
- [特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换](../../../../runbooks/precision/b16_reg_cast_layout_should_convert_at_localtensor_boundary.md)（`exemplifies`）：《bfloat16类型》说明bfloat16类型函数总入口，涵盖算术、比较、数学库及精度转换函数，并包含bfloat16x2类型对应函数。；《特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换》说明dav-3510/CANN 9.0.1 的已测 DIST_UNPACK_B16→Reg::Cast→UB 中间组合产生系统性偏差；classic AscendC::Cast 边界转换建立了正确性基线，不代表所有 Reg Cast 组合失效。。二者在bfloat16类型入口的实际使用受全局类型命名、B16边界转换和提升后lane宽度约束，而非由平台或版本过滤上存在可执行的直接衔接。
- [__bfloat162bfloat162](bfloat16_precision_conversion_functions/_bfloat162bfloat162.md)（`related`）：bfloat16 类型总览定义 bfloat16x2 数据类型、头文件与可用算术/转换族，是该构造接口的类型上下文。
<!-- cannbot:related:end -->
