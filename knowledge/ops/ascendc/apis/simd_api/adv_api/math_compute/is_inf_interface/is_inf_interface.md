---
type: API
title: IsInf接口
description: 按元素判断浮点数是否为±INF，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/IsInf_interface/IsInf_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# IsInf接口

按元素判断浮点数是否为±INF，并提供临时空间大小获取接口。

按元素判断输入的浮点数是否为±INF，输出结果为浮点数或布尔值。当输出为浮点类型时，对于±INF的输入数据，对应位置的结果为浮点类型的1，反之为0；当输出为bool类型时，对于±INF的输入数据，对应位置的结果为true，反之为false。计算公式如下： - 当输出为浮点类型时： - 当输出为bool类型时：

本接口组包含 IsInf。

本接口属于高阶数学计算接口。

支持的数据类型为 bool、half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：不支持源操作数与目的操作数地址重叠。；操作数地址偏移对齐要求请参见通用说明和约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
