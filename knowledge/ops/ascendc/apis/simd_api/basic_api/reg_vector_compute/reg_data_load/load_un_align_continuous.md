---
type: API
title: LoadUnAlign
description: 将数据从非32字节对齐的UB地址连续搬运至RegTensor，利用UnalignRegForLoad暂存跨对齐边界数据，需配合LoadUnAlignPre使用。移
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reg_data_load/LoadUnAlign_continuous.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# LoadUnAlign

头文件路径为："basic_api/reg_compute/kernel_reg_compute_datacopy_intf.h"。

为提升对不规则内存地址的处理能力，Reg矢量计算支持在数据搬运过程中对非32字节对齐的地址进行访问，降低非对齐访问带来的性能开销。LoadUnAlign能够实现数据从非对齐的Unified Buffer（UB）连续搬运至RegTensor，利用非对齐寄存器UnalignRegForLoad作为临时缓存区，暂存跨对齐边界的数据，从而实现高效的连续非对齐数据传输。

非对齐搬运有三类接口：普通搬运接口、PostUpdate扩展搬运接口、使用AddrReg寄存器存储偏移量接口。

RegTensor的模板参数regTrait支持RegTraitNumOne及RegTraitNumTwo。
非对齐搬入原理

参数：T: 源操作数的数据类型。支持的数据类型请参考数据类型。；postMode: 用于控制是否使能UB地址会自动更新功能（post update），PostLiteral类型。具体参数说明请参考PostLiteral。；U: 目的操作数的RegTensor类型。例如RegTensor\，由编译器自动推导，用户不需要手动填写。；dstReg(输出): 目的操作数，类型为RegTensor。；ureg(输入/输出): 非对齐寄存器，UnalignRegForLoad类型，用于存储非32字节的数据，寄存器大小为32字节。；srcAddr(输入/输出): 源操作数，UB起始地址，不需要32字节对齐。；postUpdateStride(输入): 地址更新步长，uint32_t类型，单位：元素个数。根据postMode的取值有两种情况： &bull; POST_MODE_NORMAL：不支持。 &b。

支持数据类型：b8、b16、b32、b64。

约束：- LoadUnAlignPre与LoadUnAlign接口需要组合使用。
- PostUpdate扩展搬运接口只支持POST_MODE_UPDATE模式。
- 当RegTensor模板参数RegTrait为RegTraitNumOne和RegTraitNumTwo时，支持情况

仅 Ascend 950PR/Ascend 950DT 支持。
