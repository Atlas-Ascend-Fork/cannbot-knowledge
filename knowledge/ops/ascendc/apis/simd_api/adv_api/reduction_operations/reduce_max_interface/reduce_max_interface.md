---
type: API
title: ReduceMax接口
description: 对多维向量在指定维度求最大值，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceMax_interface/ReduceMax_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# ReduceMax接口

对多维向量在指定维度求最大值，并提供临时空间大小获取接口。

对一个多维向量在指定的维度求最大值。 定义指定计算的维度（Reduce轴）为R轴，非指定维度（Normal轴）为A轴。如下图所示，对shape为(2, 3)的二维矩阵进行运算，指定在第一维求最大值，输出结果为[4, 5, 6]；指定在第二维求最大值，输出结果为[3, 6]。第一维是外层轴，简称外轴；第二维是内层轴，简称内轴。 图1 ReduceMax按第一个维度计算示例 图2 ReduceMax按最后一个维度计算示例

本接口组包含 ReduceMax。

本接口属于高阶归约运算接口。

约束：操作数地址对齐要求请参见通用地址对齐约束。；当srcInnerPad为True时，输入向量的内轴必须为32字节的整数倍。当原始向量的内轴长度n占据的字节长度不是32的整数倍时，需要开发者将其向上补齐到32的整数倍。开发者自行padding补齐后的内轴大小为inner = (n * sizeof(T) + 32 - 1) / 32 * 32 / sizeof(T)。；不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
