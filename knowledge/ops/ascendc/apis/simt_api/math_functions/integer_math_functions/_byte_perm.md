---
type: API
title: __byte_perm
description: 由输入的两个4字节的uint32_t类型数据组成一个8个字节的64比特位的整数，通过选择器s指定选取其中的4个字节，将这4个字节从低位到高位拼成一个uint32_t类型的整数。具体实现逻辑如下：
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/__byte_perm.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __byte_perm

按字节置换函数。将两个 uint32_t 输入 x、y 拼接成 8 字节 64 位整数（x 占低位 [0:31]，y 占高位 [32:63]），由选择器 s 指定从中抽取 4 个字节，从低到高拼成一个 uint32_t 返回。

函数原型：`unsigned int __byte_perm(unsigned int x, unsigned int y, unsigned int s)`

参数 x、y 为源操作数（uint32_t）；s 为选择器（uint32_t），其 s[0:3]、s[4:7]、s[8:11]、s[12:15] 四个 4 位字段各取值 0-7，分别指定返回整数的 byte0-byte3 在 8 字节整数中的字节索引。

返回选取出的 uint32_t 整数。当 x=0、y=0、s=0 时返回 0；当 x=1、y=1、s=1 时返回 16843008。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。
