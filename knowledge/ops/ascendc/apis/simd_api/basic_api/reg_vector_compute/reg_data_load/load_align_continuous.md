---
type: API
title: LoadAlign
description: 将数据从UB连续搬运至RegTensor，支持单搬入和双搬入模式，可通过LoadDist配置broadcast、上采样、下采样、解压缩等数据分布模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reg_data_load/LoadAlign_continuous.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# LoadAlign

头文件路径为："basic_api/reg_compute/kernel_reg_compute_datacopy_intf.h"。

LoadAlign能够实现数据从Unified Buffer（UB）连续搬运至RegTensor。支持单搬入模式和双搬入模式
- 单搬入模式：从UB读取VL数据量，搬入到一个RegTensor（VL）中。
- 双搬入模式：从UB读取2*VL数据量，交错搬运，将偶数索引和奇数索引的元素分别搬入两个RegTensor（2*VL）中。

连续对齐搬运有三类接口：普通搬运接口、PostUpdate扩展搬运接口、使用AddrReg寄存器存储偏移量接口。

RegTensor的模板参数regTrait支持RegTraitNumOne及RegTraitNumTwo。
数据搬入时，可以通过模板参数配置搬运的数据分布模式，能够实现broadcast、上采样、下采样、解压缩等功能，分布模式具体介绍

图1 连续对齐搬入分布模式图示

连续对齐搬入/搬出的三类搬运接口在迭代内的调用方式

参数：T: 源操作数的数据类型。支持的数据类型请参考数据类型。；postMode: 用于控制是否使能UB地址会自动更新功能（post update），PostLiteral类型。具体参数说明请参考PostLiteral。；dist: 数据分布模式，LoadDist类型。具体参数说明请参考表3 LoadDist参数说明（单搬入模式）。；U: 目的操作数的RegTensor类型。例如RegTensor\ ，由编译器自动推导，用户不需要手动填写。；dstReg(输出): 目的操作数，类型为RegTensor。；srcAddr(输入/输出): 源操作数，UB起始地址。；postUpdateStride(输入): 地址更新步长，int32_t类型，单位：元素个数。postUpdateStride * sizeof(T)的对齐约束请参考表3 LoadDist参数说明（单搬入模式）。根据postMode的取值有两种情况： • POST_MODE_NORMAL：不支持。 • POST_MODE_UPDATE：实际搬运UB起始地址为srcAddr，搬运后执行地址更新 srcAddr += postUpdateStride。；offset(输入): 地址偏移寄存器，AddrReg类型。需要在搬运前调用CreateAddrReg设定地址偏移量，实际搬运UB地址为srcAddr + 寄存器中存储的偏移量。AddrReg寄存器中存储的偏移量 * sizeof(T)的对齐约束请参考表3 LoadDist参数说明（单搬入模式）。

支持数据类型：b8、b16、b32、b64。

约束：- 位于Unified Buffer的地址约束、postUpdateStride * sizeof(T)对齐约束、AddrReg寄存器中存储的偏移量 * sizeof(T)对齐约束与分布模式LoadDist有关，具体地址约束
- 当RegTrait为RegTraitNumOne时，单搬入正常模式（DIST_NORM）下，若源UB的剩余空间不足256B，会发生UB越界访问。
- 单搬入模式：b64数据类型只支持LoadDist中的DIST_NORM模式。
- 当RegTensor模板参数RegTrait为RegTraitNumOne和RegTraitNumTwo时，支持情况
    | RegTensor模板参数RegTrait取值 | 支持的接口 | 支持的数据类型 |

仅 Ascend 950PR/Ascend 950DT 支持。
