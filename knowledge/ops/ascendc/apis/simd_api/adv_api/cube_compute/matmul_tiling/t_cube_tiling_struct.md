---
type: API
title: TCubeTiling结构体
description: TCubeTiling结构体包含Matmul Tiling切分算法的相关参数，被传递给Matmul Kernel侧，用于Matmul的切块、搬运和计算过程等。TCubeTiling结构体的参数说明见表1。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/TCubeTiling_struct.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# TCubeTiling结构体

头文件路径为："basic_api/kernel_operator_mm_intf.h"。 Mmad接口是Ascend C面向昇腾AI芯片的矩阵乘加核心计算接口，专为高性能算子开发设计，封装了昇腾NPU硬件的矩阵乘加计算能力，广泛用于神经网络层（如全连接层、卷积层）、数值计算类算子的开发。 Mmad接口实现昇腾NPU矩阵乘计算能力，其数学表达式为： 针对Ascend 950PR/Ascend 950DT：

本接口组包含 Mmad, 使用说明 及辅助接口 GetTiling, GetTiling。

约束：结果矩阵C只支持位于L0C Buffer（CO1），左矩阵A只支持位于L0A Buffer（A2），右矩阵B只支持位于L0B Buffer（B2）。；当M、K、N中的任意一个值为0时，表示指令不会执行，该接口将被视为NOP（空操作）。；当M = 1时，会默认开启GEMV（General Matrix-Vector Multiplication）功能。在这种情况下，Mmad API从L0A Buffer读取数据时，会以ND格式进行读取，而不会将其视为ZZ或NZ格式。所以此时左矩阵需要直接按照ND格式进行排布（GEMV特性说明）。要注意的是，开启GEMV的情况下，A矩阵的起始地址仍要求512字节对齐。；一般来说，一次Mmad计算至少完成一次A(16*16*half) * B(16*16*half)数据块计算。但实际计算时M、K、N有效值可能不是16的倍数，从而有部分数据为无效数据。以M=30，K=70，N=40为例来介绍无效数据与有效数据的排布方式。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
