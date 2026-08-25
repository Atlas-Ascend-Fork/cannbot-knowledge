---
type: API
title: MulsCast
description: 将矢量源操作数前count个数据与标量相乘再按CAST_ROUND模式转换成half类型，结果写入dst，支持标量在前和标量在后两种场景。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.composite]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/composite_compute/MulsCast_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# MulsCast

将矢量源操作数前count个数据与标量相乘再按CAST_ROUND模式转换成half类型，结果写入dst，支持标量在前和标量在后两种场景。

本接口组包含 LocalTensor, Reg矢量计算API。

本接口属于 UB 矢量计算复合算术接口，组合多个基础运算。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [MulCast](mul_cast.md)（`related`）：MulCast 用第二个 Tensor 替代标量完成乘法后再转换，适合判断 MulsCast 的标量约束何时需要升级为逐元素 scale。
- [MulsCast](../../reg_vector_compute/composite_compute/muls_cast.md)（`same_topic`）：Reg MulsCast 与本 Memory MulsCast 执行相同的标量乘加精度转换链，可据存储位置与是否保留寄存器链选择接口。
<!-- cannbot:related:end -->
