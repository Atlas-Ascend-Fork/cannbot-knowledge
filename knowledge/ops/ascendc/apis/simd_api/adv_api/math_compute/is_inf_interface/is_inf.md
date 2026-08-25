---
type: API
title: IsInf
description: 按元素判断输入浮点数是否为正负无穷，输出浮点数或布尔值
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/IsInf_interface/IsInf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# IsInf

按元素判断输入浮点数是否为±INF。输出为浮点类型时，±INF位置结果为1，反之为0；输出为bool类型时，对应位置为true/false。仅Ascend 950PR/950DT支持。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetIsInfMaxMinTmpSize获取。

模板参数config为IsInfConfig类型，含isReuseSource（预留，传false）；T为目的操作数数据类型（支持bool/half/float）；U为源操作数数据类型（支持half/float）。接口参数：dst为输出操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型与src相同或为bool；src为输入操作数；sharedTmpBuffer为临时缓存；count为参与计算元素个数。

支持的输入输出数据类型组合：half-half/bool、float-float/bool。约束：不支持源操作数与目的操作数地址重叠；遵循通用地址偏移对齐约束。
