---
type: API
title: DeInterleave
description: 将源操作数src0和src1中的元素解交织存入目的操作数dst0和dst1中。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/MaskReg_compute/DeInterleave.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# DeInterleave

头文件路径为："basic_api/reg_compute/kernel_reg_compute_maskreg_intf.h"。

将源操作数src0和src1中的元素解交织存入目的操作数dst0和dst1中。解交织排列方式如下图所示，其中每个方格代表一个分组

参数：T: MaskReg所支持的数据类型，决定了解交织的位宽大小，例如对于uint32_t类型，解交织时以4bit为一组。；dst0: 目的操作数。；dst1: 目的操作数。；src0: 源操作数。；src1: 源操作数。

支持数据类型：b8、b16、b32。

仅 Ascend 950PR/Ascend 950DT 支持。
