---
type: API
title: ReGlu接口
description: 提供ReGlu激活函数接口及GetReGluMaxMinTmpSize等Tiling临时空间大小查询接口。
tags: [task.lookup, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/ReGlu_interface/ReGlu_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# ReGlu接口

提供 ReGlu 激活函数及 GetReGluMaxMinTmpSize 临时空间查询接口。ReGlu 是 GLU 变体，使用 ReLU 作为门控激活函数，接收两个源操作数 srcTensor0 与 srcTensor1，按元素计算后输出到 dstTensor。

接口为模板函数，支持 half、bfloat16_t、float 数据类型，`isReuseSource` 参数预留。临时空间支持 `sharedTmpBuffer` 传入和框架申请两种方式，大小通过 GetReGluMaxMinTmpSize 获取。仅支持 ND 格式输入，不支持源操作数与目的操作数地址重叠，sharedTmpBuffer 也不能与源 目的操作数重叠。
