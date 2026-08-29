---
type: API
title: Rint接口
description: 按元素取最接近的整数，同等接近时取偶数，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Rint_interface/Rint_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Rint接口

按元素取最接近的整数，同等接近时取偶数，并提供临时空间大小获取接口。

获取与输入数据最接近的整数，若存在两个同样接近的整数，则获取其中的偶数。计算公式如下： 举例如下： Rint(3.9) = 4 Rint(3.3) = 3 Rint(3.5) = 4

本接口组包含 Rint。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
