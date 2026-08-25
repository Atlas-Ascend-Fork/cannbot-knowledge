---
type: API
title: MoveMask
description: 从SetVectorMask设置的掩码寄存器中读取Mask值，按模板参数T对应格式转换后写入MaskReg。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/MaskReg_compute/MoveMask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# MoveMask

头文件路径为："basic_api/reg_compute/kernel_reg_compute_maskreg_intf.h"。

从SetVectorMask设置的掩码寄存器{MASK1, MASK0}中读取Mask值，并按模板参数T对应的数据格式转换后写入返回值MaskReg。具体实现方式
b16类型读取完整128bit的{MASK1, MASK0}，将每个bit复制为2bit；b32类型读取64bit的MASK0，并将每个bit复制为4bit。

Mask与MaskReg的机制对比，具体

参数：T: 数据类型，决定mask值写入格式： &bull; 对于b16类型，会读取完整的128bit {MASK1, MASK0}数据，并将每bit复制为2bit。

支持数据类型：b16、b32。

约束：- 本接口为兼容性接口，建议优先采用CreateMask接口和UpdateMask接口进行MaskReg计算。
- 使用前需要先调用SetMaskCount/SetMaskNorm手动设置mask模式，并调用SetVectorMask设置掩码寄存器SPR{MASK1, MASK0}。

仅 Ascend 950PR/Ascend 950DT 支持。
