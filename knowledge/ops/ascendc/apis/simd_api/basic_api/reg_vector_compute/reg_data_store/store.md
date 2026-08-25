---
type: API
title: Store
description: 从RegTensor搬出至非32字节对齐的UB地址，支持搬出VL或指定count个数据。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reg_data_store/Store.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Store

头文件路径为："basic_api/reg_compute/kernel_reg_compute_datacopy_intf.h"。

Reg矢量计算数据搬运接口，支持从RegTensor搬出至非32字节对齐的UB地址dstAddr。连续搬运时，用户需手动更新dstAddr地址。

该接口封装了StoreUnAlign和StoreUnAlignPost。

参数：T: 操作数数据类型。支持的数据类型请参考数据类型。；U: 源操作数的RegTensor类型，例如RegTensor\，由编译器自动推导，用户不需要填写。；dstAddr(输出): 目的操作数，UB起始地址，不需要32字节对齐。；srcReg(输入): 源操作数，类型为RegTensor。；count(输入): 搬运数据量。连续搬运时需手动更新地址：dstAddr = dstAddr + count。

支持数据类型：b8、b16、b32、b64。

约束：-   count不能大于一个RegTensor能存储的数据个数，即count <= 256B / sizeof(T)。
-   接口内部定义了一个UnalignRegForStore，该寄存器数量上限为4，超出后编译器将报错。

仅 Ascend 950PR/Ascend 950DT 支持。
