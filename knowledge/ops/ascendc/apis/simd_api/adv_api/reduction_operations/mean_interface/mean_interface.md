---
type: API
title: Mean接口
description: 沿最后一轴对各元素求平均值，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/Mean_interface/Mean_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Mean接口

沿最后一轴对各元素求平均值，并提供临时空间大小获取接口。

根据最后一轴的方向对各元素求平均值。 如果输入是向量，则在向量中对各元素相加求平均；如果输入是矩阵，则沿最后一个维度对元素求平均。本接口最多支持输入为二维数据，不支持更高维度的输入。 如下图所示，对shape为(4, 5)的二维矩阵进行求平均操作，输出结果为[3， 8， 13， 18]。 在了解接口具体功能之前，需要了解一些必备概念：数据的行数称之为外轴长度（outter），每行实际的元素个数称之为内轴的实际元素个数（n），内轴实际元素个数n向上32字节对齐后的元素个数称之为补齐后的内轴元素个数(inner)。本接口要求输入的内轴长度满足32字节对齐，所以当n占据的字节长度不是32字节的整数倍时，需要开发者将其向上补齐到32字节的整数倍。如下样例中，元素类型为float，每行的实际元素个数n为5，占据字节长度为20字节，不是32字节的整数倍，向上补齐后得到32字节，对应的元素个

本接口组包含 Mean。

本接口属于高阶归约运算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：操作数地址对齐要求请参见通用地址对齐约束。；不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；当前仅支持ND格式的输入，不支持其他格式。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
