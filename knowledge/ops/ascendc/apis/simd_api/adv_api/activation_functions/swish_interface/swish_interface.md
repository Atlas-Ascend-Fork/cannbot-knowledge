---
type: API
title: Swish接口
description: 提供Swish激活函数接口及GetSwishTmpSize等Tiling临时空间大小查询接口。
tags: [task.lookup, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/Swish_interface/Swish_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Swish接口

提供 Swish 激活函数及 GetSwishTmpSize 临时空间查询接口。Swish 计算公式为 x * sigmoid(βx)，其中 β 为常数参数，通过 `scalarValue` 入参传入。

接口为模板函数，支持 half、float 数据类型，β 参数数据类型需与源 目的操作数一致，`isReuseSource` 参数预留。通过 `dataSize` 指定实际计算元素个数。仅支持 ND 格式输入，不支持源操作数与目的操作数地址重叠。

<!-- cannbot:related:start -->
## 相关

- [GetSwishTmpSize](get_swish_tmp_size.md)（`related`）：GetSwishTmpSize 为 Swish Kernel 的中间变量预留提供直接空间预算。
- [Swish](swish.md)（`same_topic`）：Swish 与《Swish接口》的实质衔接是：Swish kernel 与临时空间查询直接配套；SiLU 是 beta=1 的同公式变体，Sigmoid 是门控项。
<!-- cannbot:related:end -->
