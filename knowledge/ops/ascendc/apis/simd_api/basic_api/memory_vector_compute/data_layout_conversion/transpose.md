---
type: API
title: Transpose
description: 实现16x16二维矩阵数据块转置，或NCHW与NHWC数据格式互相转换，支持普通和增强两种模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_layout_conversion/Transpose.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Transpose

实现16x16二维矩阵数据块转置，或NCHW与NHWC数据格式互相转换，支持普通和增强两种模式。

Transpose接口用于实现16*16的二维矩阵数据块转置或者[N,C,H,W]与[N,H,W,C]数据格式互相转换。 16*16的普通转置接口计算原理和参考伪代码如下： [N,C,H,W]与[N,H,W,C]数据格式互相转换的增强转置计算原理和参考伪代码如下：

本接口属于 UB 矢量计算数据排布转换接口。

参数说明：T：操作数的数据类型。；dst：输出 目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 LocalTensor的起始地址需要32字节对齐。；src：输入 源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 LocalTensor的起始地址需要32字节对齐。 数据类型需要与dst保持一致。；sharedTmpBuffer：输入 共享的临时Buffer，sharedTmpBuffer的大小参考[表sharedTmpBuffer所需的内存](#table4)。；transposeParams：输入 控制Transpose的数据结构。结构体内包含：输入的shape信息和transposeType参数。该数据结构的定义请参考[表TransposeParamsExt结构体内参数说明](#table3)。 struct TransposeParamsExt {     __aicore__ TransposeParamsExt() {}     __aicore__ TransposeParamsExt(const uint16_t nSizeIn, const uint16_t cSizeIn, const uint16_t hSizeIn,         const uint16_t wSizeIn, const TransposeType transposeTypeIn)         : nSize(nSizeIn),           cSize(cSizeIn),           hSize(hSizeIn),           wSize(wSizeIn),           transposeType(transposeTypeIn)     {}     uint16_t nSize = 0;     uint16_t cSize = 0;     uint16_t hSize = 0;     uint16_t wSize = 0;     TransposeType transposeType = TransposeType::TRANSPOSE_ND2ND_B16; };

返回值：无。
