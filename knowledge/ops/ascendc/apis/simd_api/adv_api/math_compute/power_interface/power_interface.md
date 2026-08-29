---
type: API
title: Power接口
description: 按元素做幂运算，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Power_interface/Power_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Power接口

按元素做幂运算，并提供临时空间大小获取接口。

实现按元素做幂运算功能，提供3类接口，处理逻辑如下：

本接口组包含 Power。

本接口属于高阶数学计算接口。

支持的数据类型为 uint8_t、int8_t、uint16_t、int16_t、uint32_t、int32_t。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：不支持源操作数与目的操作数地址重叠。；对于Atlas 推理系列产品AI Core，幂运算的指数必须小于2 31 -1。；操作数地址对齐要求请参见通用地址对齐约束。；支持的数据类型

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
