---
type: API
title: Truncate
description: 将源操作数中的浮点数元素截断为整数值并保留原数据类型，存入目的操作数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/type_conversion/Truncate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Truncate

将源操作数中的浮点数元素截断为整数值（保留原数据类型），并存入目的操作数。

头文件："basic_api/reg_compute/kernel_reg_compute_vec_vconv_intf.h"。

参数：T: 操作数数据类型。支持的数据类型请参考数据类型。；roundMode: 舍入模式，取值如下： • RoundMode::CAST_RINT • RoundMode::CAST_ROUND • RoundMode::CAST_FLOOR • RoundMode::CAST_CEIL • RoundMode::CAST_TRUNC；mode: MaskMergeMode枚举类型，选择MERGING模式或ZEROING模式。 • ZEROING模式下，mask未筛选的元素在dstReg中置零。 • MERGING模式当前不支持。；S: srcReg/dstReg类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg(输入): 源操作数。 类型为RegTensor；mask(输入): 源操作数元素操作的有效指示，详细说明请参考MaskReg。

支持数据类型：half、bfloat16_t、float。

约束：- float类型只支持不饱和模式。

仅 Ascend 950PR/Ascend 950DT 支持。
