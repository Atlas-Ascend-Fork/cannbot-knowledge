---
type: API
title: Gather
description: 根据索引值index将源操作数按元素收集到目的操作数dstReg中，index中每个元素表示相对于baseAddr的元素位置，支持多种数据类型组合。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reg_data_load/Gather_discrete.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Gather

头文件路径为："basic_api/reg_compute/kernel_reg_compute_datacopy_intf.h"。

该指令会根据索引值index将源操作数按元素收集到目的操作数dstReg中。收集过程如图1所示

参数：T0: 目的操作数的数据类型。支持的数据类型请参考数据类型。；T1: 源操作数的数据类型。支持的数据类型请参考数据类型。；T2: 索引值的数据类型，支持的数据类型请参考数据类型。；T3: 目的操作数的RegTensor类型。例如RegTensor\，由编译器自动推导，用户不需要手动填写。；T4: 索引值的RegTensor类型，例如RegTensor\，由编译器自动推导，用户不需要手动填写。；dstReg(输出): 目的操作数，类型为RegTensor。；baseAddr(输入): 源操作数，UB中的基地址，需要32字节对齐。；index(输入): 索引值，dstReg中的每个元素在UB中相对于baseAddr的位置，单位：元素。类型为RegTensor。index中的值可以重复。 例：baseAdd。

约束：- 位于Unified Buffer的地址必须32字节对齐。
- index索引值对应的数据必须在UB有效地址范围内。
- 当T0为b16类型，T1为b8数据类型时，目的操作数的低8位与源操作数相同，高8位自动补0。例如源操作数T1数据类型为int8_t
    40=0b00101000 -> 0b0000000000101000，扩充至16位后等于40；

    -40=0b11011000 -> 0b0000000011011000，扩充至16位后等于216。

- 当源操作数数据类型T1为B64时，T0、T1、T2、T3、T4只支持以下组合
    | T0 | T1 | T2 | T3（自动推导） | T4（自动推导） | 备注 |

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Gather 双加 LocalTensor 基址导致交错旋转乱码](../../../../../runbooks/precision/localtensor_gather_base_address_not_double_counted.md)（`exemplifies`）：《Gather 双加 LocalTensor 基址导致交错旋转乱码》处理“Gather 已由 LocalTensor 提供源基址时，srcBaseAddr 再传物理地址会重复加基址；保持字节偏移并传 0 可恢复交错旋转。”。《Gather》明确提供“根据索引值index将源操作数按元素收集到目的操作数dstReg中，index中每个元素表示相对于baseAddr的元素位置，支持多种数据类型组合。”，其参数、调用或验证步骤直接接入Gather 的 base 地址、byte offset、重复偏移故障和地址计算合同。
- [AscGather](../../../c_api/vector_compute/asc_gather.md)（`related`）：AscGather 与《Gather》的实质衔接是：AscGather 的 offset 是逐元素收集地址；Reg/Memory Gather 与各错位 runbook 直接解释偏移、基址、维序和非轴步长的正确构造。
- [GatherB](gather_b_discrete.md)（`related`）：GatherBDiscrete 将同类离散搬入从元素粒度改为 32B DataBlock 粒度且只使用前 8 个索引；与 focal 的元素级 Gather 构成粒度选型。
- [Reg数据搬入](reg_data_load.md)（`related`）：集合页把按索引离散搬入分流到 Gather，而连续地址使用 Load/LoadAlign/LoadUnAlign。
- [AscGather](../../../c_api/reg/reg_load/asc_gather.md)（`same_topic`）：两者都从 UB 基址按逐元素 index 收集到寄存器；基础 Reg Gather 明确 index 单位为元素及类型组合，补足 C AscGather 的参数语义。
- [Gather](../scatter_operations/gather.md)（`same_topic`）：《Gather》说明根据索引值将源操作数按元素收集到目的操作数中，支持b8、b16、b32数据类型。；《Gather》说明根据索引值index将源操作数按元素收集到目的操作数dstReg中，index中每个元素表示相对于baseAddr的元素位置，支持多种数据类型组合。。二者在Reg Gather的index和baseAddr寻址合同与C API等价接口、维序/步长及LocalTensor基址故障直接对应上存在可执行的直接衔接。
- [ScatterDiscrete](../reg_data_store/scatter_discrete.md)（`same_topic`）：ScatterDiscrete 与《Gather》的实质衔接是：ScatterDiscrete 与 Gather、C/基础 Scatter 形成索引读写对偶；两张故障卡直接约束重复索引归约和 updates 形状。
<!-- cannbot:related:end -->
