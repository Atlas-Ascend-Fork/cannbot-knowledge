---
type: API
title: MaskGenWithRegTensor
description: 将数据从RegTensor搬运至MaskReg，通过offset参数选择数据块，b16类型每个bit广播为2bit，b32类型每个bit广播为4bit。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reg_data_load/MaskGenWithRegTensor_MaskReg.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# MaskGenWithRegTensor

头文件路径为："basic_api/reg_compute/kernel_reg_compute_maskreg_intf.h"。

MaskGenWithRegTensor能够实现数据从RegTensor搬运至MaskReg。

- 数据类型为b16时，RegTensor（256B）分成16个数据块（16B），用户通过参数可选择某一个数据块，数据块的每个bit broadcast成2bit后变为32B，即输出的MaskReg。
- 数据类型为b32时，RegTensor（256B）分成32个数据块（8B），用户通过参数可选择某一个数据块，数据块的每个bit broadcast成4bit后变为32B，即输出的MaskReg。

具体搬运原理

参数：T: 源操作数的数据类型。支持的数据类型请参考数据类型。；offset: offset决定了srcReg中需要搬运的数据块，具体描述请参考关键特性说明。 • 当数据类型为b16，offset∈[0, 15]。 • 当数据类型为b32，offset∈[0, 31]。；U: 源操作数的RegTensor类型。例如RegTensor\ ，由编译器自动推导，用户不需要手动填写。；dst(输出): 目的操作数，类型为MaskReg。；srcReg(输入): 源操作数，类型为RegTensor。

支持数据类型：b16、b32。

约束：- 当数据类型为b16，offset∈[0, 15]；当数据类型为b32，offset∈[0, 31]。

仅 Ascend 950PR/Ascend 950DT 支持。
