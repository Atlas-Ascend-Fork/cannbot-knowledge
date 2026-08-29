---
type: API
title: Brcb
description: 数据填充接口，每次取输入张量8个数，将每个数填充到结果张量一个DataBlock（32字节）中。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_padding/Brcb.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Brcb

数据填充接口，每次取输入张量8个数，将每个数填充到结果张量一个DataBlock（32字节）中。

Brcb接口对输入数据，每一次取输入张量中的8个数进行填充操作，将每个数填充到结果张量的一个DataBlock（32字节）中。 接口计算原理和参考伪代码如下：

本接口属于 UB 矢量计算数据填充接口。

参数说明：T：操作数数据类型。；dst：输出 目的操作数，类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。  LocalTensor的起始地址需要按照32字节对齐。；src：输入 源操作数，类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。  需要按照32字节对齐。  注：每一次迭代读取src中的8个元素，所以src的元素个数不小于8 * repeatTime。；repeatTime：输入 指令迭代次数，每次迭代完成8个DataBlock的数据收集，取值范围：repeatTime∈[0,255]。；repeatParams：输入 用于控制指令迭代的相关参数，类型为BrcbRepeatParms。  BrcbRepeatParams参数说明请参考[表3 BrcbRepeatParams结构体参数说明](#table3)。

约束：操作数地址对齐要求请参见通用地址对齐约束。；不支持源操作数与目的操作数使用同一块内存地址。；BrcbRepeatParams结构体内参数dstBlkStride不支持设置为0，若设置成0可能产生未定义行为。；针对Atlas 推理系列产品AI Core，使用时需要预留8KB的Unified Buffer空间，作为接口的临时数据存放区。

<!-- cannbot:related:start -->
## 相关

- [BilinearInterpolation](../basic_arithmetic/bilinear_interpolation_isasi.md)（`related`）：BilinearInterpolation 的第二步是“通过 Brcb 广播填充 src1”；Brcb 定义“每一次取输入张量中的8个数进行填充操作，将每个数填充到结果张量的一个DataBlock（32字节）中。”，后者提供权重广播布局。
- [AscBrcb](../../../c_api/vector_compute/asc_brcb.md)（`same_topic`）：Brcb接口对输入数据，每一次取输入张量中的8个数进行填充操作，将每个数填充到结果张量的一个DataBlock（32字节）中。；给定一个输入矢量，每一次取输入矢量中的8个数填充到结果矢量的8个datablock（32Bytes）中去，每个数对应一个datablock。。两卡定义相同的八元素逐 DataBlock 广播语义，只是接口层和平台表达不同。
<!-- cannbot:related:end -->
