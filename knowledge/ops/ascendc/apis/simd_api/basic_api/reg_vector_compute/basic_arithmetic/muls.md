---
type: API
title: Muls
description: 根据mask对源操作数srcReg每个元素与标量scalarValue求积，将结果写入目的操作数dstReg。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/basic_arithmetic/Muls.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Muls

矢量内每个元素与标量求积。

头文件："basic_api/reg_compute/kernel_reg_compute_vec_binary_scalar_intf.h"。

参数：T: 矢量目的操作数和源操作数的数据类型。支持的数据类型请参考数据类型。；U: 标量源操作数的数据类型。支持的数据类型请参考数据类型。；mode: MaskMergeMode枚举类型，选择MERGING模式或ZEROING模式。 • ZEROING模式下，mask未筛选的元素在dstReg中置零。 • MERGING模式当前不支持。；S: 目的操作数的RegTensor类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg(输入): 源操作数。 类型为RegTensor。；scalarValue(输入): 源操作数。 类型为标量。；mask(输入): 源操作数中元素有效性的指示，详细说明请参考MaskReg。

支持数据类型：int16_t、uint16_t、half、int32_t、uint32_t、float、complex32、int64_t、uint64_t、complex64。

仅 Ascend 950PR/Ascend 950DT 支持。
