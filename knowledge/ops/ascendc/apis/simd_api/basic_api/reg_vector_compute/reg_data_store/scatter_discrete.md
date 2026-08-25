---
type: API
title: ScatterDiscrete
description: 根据索引值index将源操作数srcReg中的元素分散到目的操作数UB中。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reg_data_store/Scatter_discrete.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ScatterDiscrete

头文件路径为："basic_api/reg_compute/kernel_reg_compute_datacopy_intf.h"。

该指令会根据索引值index将源操作数srcReg中的元素分散到目的操作数UB中。分散过程如图1所示

参数：T: 目的操作数的数据类型。支持的数据类型请参考数据类型。；U: 索引值index的数据类型。支持的数据类型请参考数据类型。；S: 源操作数的RegTensor类型。例如RegTensor\ ，由编译器自动推导，用户不需要手动填写。；V: 索引值的RegTensor类型，例如RegTensor\ ，由编译器自动推导，用户不需要手动填写。；baseAddr(输出): 目的操作数，UB中的基地址，需要32字节对齐。；srcReg(输入): 源操作数，类型为RegTensor。；index(输入): 索引值，srcReg中的每个元素在UB中相对于baseAddr的位置，单位：元素个数。类型为RegTensor。 注：index中的值必须唯一。若存在重复的index值，系统仅保留其中一个对应的数据，其余将被忽略。无法确定具体保留哪一个，因此必须确保index值不重复。；mask(输入): 源操作数元素操作的有效指示，详细说明请参考MaskReg。

约束：- 位于Unified Buffer的首地址必须32B对齐。
- 当T为int8_t或者uint8_t数据类型时，源操作数中仅偶数位元素有效。即srcReg中的偶数位置[0, 2, 4, ..., 252, 254]的数据会被分散存储到目的操作数中。
- index中的值必须唯一。若存在重复的index值，系统仅保留其中一个对应的数据，其余将被忽略。无法确定具体保留哪一个，因此必须确保index值不重复。
- 当目的操作数的数据类型T为B64时，T、U、S、V只支持以下组合

仅 Ascend 950PR/Ascend 950DT 支持。
