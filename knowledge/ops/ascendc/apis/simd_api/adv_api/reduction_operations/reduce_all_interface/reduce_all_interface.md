---
type: API
title: ReduceAll接口
description: 对多维向量在指定维度求逻辑与，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceAll_interface/ReduceAll_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# ReduceAll接口

对多维向量在指定维度求逻辑与，并提供临时空间大小获取接口。

对一个多维向量在指定的维度求逻辑与。 定义指定计算的维度（Reduce轴）为R轴，非指定维度（Normal轴）为A轴。如下图所示，对shape为(2, 3)的二维矩阵进行运算，指定在第一维求逻辑与，输出结果为[1, 0, 0]；指定在第二维求逻辑与，输出结果为[0, 0]。 图1 ReduceAll按第一个维度计算示例 图2 ReduceAll按最后一个维度计算示例

本接口组包含 ReduceAll。

本接口属于高阶归约运算接口。

支持的数据类型为 uint8_t、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：操作数地址对齐要求请参见通用地址对齐约束。；源操作数srcTensor的输入数据只能为0或1。；不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [ReduceProd接口](../reduce_prod_interface/reduce_prod_interface.md)（`related`）：布尔全真归约不应以数值乘积替代，ReduceAll 提供明确布尔语义和 dtype 契约。
- [GetReduceAllMaxMinTmpSize](get_reduce_all_max_min_tmp_size.md)（`same_topic`）：焦点处理ReduceAll 临时空间上下界与 ReduceAll 执行接口；ReduceAll接口正文说明“对多维向量在指定维度求逻辑与，并提供临时空间大小获取接口”。候选消费该查询结果或定义同一 ReduceAll workspace 契约。
- [ReduceAll](reduce_all.md)（`same_topic`）：ReduceAll说明对一个多维向量在指定的维度求逻辑与。 定义指定计算的维度（Reduce轴）为R轴，非指定维度（Normal轴）为A轴。如下图所示，对shape为\(2, 3\)的二维矩阵进行运算，指定在第一维求逻辑与，输出结果为\[1, 0, 0\]；指定在第二维求逻辑与，输出结果为\[0, 0\]。 图1 ReduceAll按第一个维度计算示例 ! 图2 ReduceAll按最后一个维度计算示例 !。
<!-- cannbot:related:end -->
