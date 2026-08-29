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

- [MulCast](mul_cast.md)（`same_topic`）：“将矢量源操作数前count个数据与标量相乘再按CAST_ROUND模式转换成half类型，结果写入dst，支持标量在前和标量在后两种场景。”与“按元素求积，并根据源操作数和目的操作数Tensor的数据类型进行精度转换。”提供双方正文证据。两端核心契约都是乘法后立即做 dtype 转换；MulsCast 把一端约束为标量并固定 CAST_ROUND 到 half，MulCast 则是双 Tensor 逐元素版本，互读可直接完成重载选型。
<!-- cannbot:related:end -->
