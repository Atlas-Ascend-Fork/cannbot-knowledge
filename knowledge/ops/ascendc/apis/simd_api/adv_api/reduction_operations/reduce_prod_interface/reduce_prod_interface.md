---
type: API
title: ReduceProd接口
description: 对多维向量在指定维度求连乘积，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceProd_interface/ReduceProd_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# ReduceProd接口

对多维向量在指定维度求连乘积，并提供临时空间大小获取接口。

对一个多维向量在指定的维度求积。 定义指定计算的维度（Reduce轴）为R轴，非指定维度（Normal轴）为A轴。如下图所示，对shape为(2, 3)的二维矩阵进行运算，指定在第一维求乘积，输出结果为[4, 10, 18]；指定在第二维求乘积，输出结果为[6, 120]。 图1 ReduceProd按第一个维度计算示例 图2 ReduceProd按最后一个维度计算示例

本接口组包含 ReduceProd。

本接口属于高阶归约运算接口。

支持的数据类型为 float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：操作数地址对齐要求请参见通用地址对齐约束。；内部算法不处理累乘计算时的数据溢出，溢出场景不保证接口精度。；不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
