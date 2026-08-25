---
type: API
title: Load
description: 从UB非32字节对齐的源地址搬运数据至RegTensor，搬运量为VL（256B），内部封装了LoadUnAlignPre和LoadUnAlign接口。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reg_data_load/Load.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Load

头文件路径为："basic_api/reg_compute/kernel_reg_compute_datacopy_intf.h"。

Reg矢量计算数据搬运接口，支持从UB非32字节对齐的源地址srcAddr搬运至RegTensor，搬运量为VL（256B）。连续搬运时，用户需手动更新srcAddr地址。

该接口封装了LoadUnAlignPre和LoadUnAlign。

参数：T: 操作数数据类型。支持的数据类型请参考数据类型。；U: 目的操作数的RegTensor类型，例如RegTensor\，由编译器自动推导，用户不需要手动填写。；dstReg(输出): 目的操作数，类型为RegTensor。；srcAddr(输入): 源操作数，UB起始地址，不需要32字节对齐。

支持数据类型：b8、b16、b32、b64。

约束：- dstReg不支持RegTraitNumTwo。
- 接口内部定义了一个UnalignRegForLoad，该寄存器数量上限为4，超出后编译器将报错。

仅 Ascend 950PR/Ascend 950DT 支持。
