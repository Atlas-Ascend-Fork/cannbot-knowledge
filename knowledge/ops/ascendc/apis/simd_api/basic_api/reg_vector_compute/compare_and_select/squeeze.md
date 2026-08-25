---
type: API
title: Squeeze
description: 将srcReg中被mask选择的有效元素依次复制到dstReg中连续排列，剩余位置置0。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/compare_and_select/Squeeze.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Squeeze

头文件路径为："basic_api/reg_compute/kernel_reg_compute_gather_mask_intf.h"。

将传入的srcReg中被mask选择的有效元素依次复制到dstReg中，有效元素在dstReg中从低到高连续排列，剩余位置元素置为0，如图1所示。

特别地，当模板参数store取值为GatherMaskMode::STORE_REG时，Squeeze会将有效元素的总字节数存入AR特殊寄存器。此时配合使用连续非对齐搬出的场景3接口（无需显式传入偏移量），StoreUnAlign会自动从AR寄存器读取有效字节数作为地址偏移，参考调用示例。

参数：T: 目的操作数和源操作数的数据类型。；store: GatherMaskMode选择是否将有效元素的总字节数存入AR寄存器，AR寄存器描述参考表 模板参数说明。 • NO_STORE_REG，有效元素的总字节数不存入AR寄存器； • STORE_REG，有效元素的总字节数存入AR寄存器。；U: 目的操作数和源操作数的RegTensor类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg(输入): 源操作数。 类型为RegTensor。；mask(输入): mask用于控制每次迭代内参与计算的元素。

支持数据类型：int8_t、uint8_t、int16_t、uint16_t、half、int32_t、uint32_t、float。

约束：- 当模板参数store取值为GatherMaskMode::STORE_REG时，由于硬件约束，StoreUnAlign指令和Squeeze指令必须交替使用，例如
- 当store取值为GatherMaskMode::NO_STORE_REG时，不涉及AR寄存器，Squeeze和StoreUnAlign不强制交替。

仅 Ascend 950PR/Ascend 950DT 支持。
