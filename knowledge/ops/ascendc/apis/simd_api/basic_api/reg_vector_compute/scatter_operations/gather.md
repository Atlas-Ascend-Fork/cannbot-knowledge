---
type: API
title: Gather
description: 根据索引值将源操作数按元素收集到目的操作数中，支持b8、b16、b32数据类型。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/scatter_operations/Gather.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Gather

该指令会根据索引值indexReg将源操作数srcReg按元素收集到目的操作数dstReg中。收集过程如下图所示

头文件："basic_api/reg_compute/kernel_reg_compute_gather_mask_intf.h"。

参数：T: 源操作数和目的操作数的数据类型，两者需保持一致。支持的数据类型请参考数据类型。；U: 索引值的数据类型，支持的数据类型请参考数据类型。；S: 目的操作数的RegTensor类型，例如RegTensor，由编译器自动推导，用户不需要手动填写。；V: 索引值的RegTensor类型，例如RegTensor，由编译器自动推导，用户不需要手动填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg(输入): 源操作数。 类型为RegTensor。；indexReg(输入): 索引值，单位：元素。 类型为RegTensor。 数据类型的位宽需要与目的操作数的位宽保持一致。indexReg中的值可以重复。 如果indexReg中索。

支持数据类型：b8、b16、b32。

约束：- 源操作数和目的操作数的数据类型需保持一致。
- 索引值和目的操作数的数据类型位宽需保持一致。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Gather 双加 LocalTensor 基址导致交错旋转乱码](../../../../../runbooks/precision/localtensor_gather_base_address_not_double_counted.md)（`exemplifies`）：《Gather》说明根据索引值将源操作数按元素收集到目的操作数中，支持b8、b16、b32数据类型。；《Gather 双加 LocalTensor 基址导致交错旋转乱码》说明Gather 已由 LocalTensor 提供源基址时，srcBaseAddr 再传物理地址会重复加基址；保持字节偏移并传 0 可恢复交错旋转。。二者在Reg Gather的index和baseAddr寻址合同与C API等价接口、维序/步长及LocalTensor基址故障直接对应上存在可执行的直接衔接。
- [Gather 非 dim 维缩小时折叠步长错位](../../../../../runbooks/precision/gather_non_axis_shape_shrink_requires_per_axis_source_strides.md)（`exemplifies`）：《Gather》说明根据索引值将源操作数按元素收集到目的操作数中，支持b8、b16、b32数据类型。；《Gather 非 dim 维缩小时折叠步长错位》说明torch.gather 的 DMA 与 SIMT 路线都必须按逐维 xstride 和输出坐标寻址；非 dim 维允许缩小，不能折叠成假定 extent 相等的 outer 步长。。二者在Reg Gather的index和baseAddr寻址合同与C API等价接口、维序/步长及LocalTensor基址故障直接对应上存在可执行的直接衔接。
- [gather 扁平偏移公式 dim 上方形状错配](../../../../../runbooks/precision/gather_dim.md)（`exemplifies`）：《Gather》说明根据索引值将源操作数按元素收集到目的操作数中，支持b8、b16、b32数据类型。；《gather 扁平偏移公式 dim 上方形状错配》说明AscendC gather kernel 用扁平公式 outer*x_block_+idx_val*x_inner_+inner 计算 x 偏移，outer 取自 index 坐标系却用 x 的 x_block_ 缩放；当 index 与 x 在 dim 之上某维形状不同时外层坐标错位，致该 case 大面积 mismatch，dim=0 时公式退化为正确故多用例不暴露。。二者在Reg Gather的index和baseAddr寻址合同与C API等价接口、维序/步长及LocalTensor基址故障直接对应上存在可执行的直接衔接。
- [多维 Gather 部分 case 错 — LUT 维序反了](../../../../../runbooks/precision/gather_lut_coordinate_decode_must_start_from_last_dimension.md)（`exemplifies`）：《Gather》说明根据索引值将源操作数按元素收集到目的操作数中，支持b8、b16、b32数据类型。；《多维 Gather 部分 case 错 — LUT 维序反了》说明C-contiguous 多维坐标必须从末维逆序解码；host LUT 是正确性回退而非快路，SIMT 可用同一逆序规则在线解码。。二者在Reg Gather的index和baseAddr寻址合同与C API等价接口、维序/步长及LocalTensor基址故障直接对应上存在可执行的直接衔接。
- [AscGather](../../../c_api/vector_compute/asc_gather.md)（`related`）：《Gather》说明根据索引值将源操作数按元素收集到目的操作数中，支持b8、b16、b32数据类型。；《AscGather》说明将src按照src_offset给定的偏移按元素收集到dst中。。二者在Reg Gather的index和baseAddr寻址合同与C API等价接口、维序/步长及LocalTensor基址故障直接对应上存在可执行的直接衔接。
- [Reg矢量计算离散操作](scatter_operations.md)（`related`）：《Gather》说明根据索引值将源操作数按元素收集到目的操作数中，支持b8、b16、b32数据类型。；《Reg矢量计算离散操作》说明寄存器矢量离散操作接口集合，包含Gather接口。。二者在Reg Gather的index和baseAddr寻址合同与C API等价接口、维序/步长及LocalTensor基址故障直接对应上存在可执行的直接衔接。
- [AscGather](../../../c_api/reg/reg_load/asc_gather.md)（`same_topic`）：《Gather》说明根据索引值将源操作数按元素收集到目的操作数中，支持b8、b16、b32数据类型。；《AscGather》说明根据索引位置index将源操作数src按元素收集到目的操作数dst中。。二者在Reg Gather的index和baseAddr寻址合同与C API等价接口、维序/步长及LocalTensor基址故障直接对应上存在可执行的直接衔接。
- [Gather](../../memory_vector_compute/scatter_gather/gather.md)（`same_topic`）：《Gather》明确“根据索引值将源操作数按元素收集到目的操作数中，支持b8、b16、b32数据类型。”；它与《Gather》的“根据基地址和地址偏移张量确定索引，将输入张量中对应元素收集到结果张量中，支持前n个数据和高维切分计算。”在实际调用参数、数据流或结果校验上直接衔接。
- [Gather](../reg_data_load/gather_discrete.md)（`same_topic`）：《Gather》说明根据索引值将源操作数按元素收集到目的操作数中，支持b8、b16、b32数据类型。；《Gather》说明根据索引值index将源操作数按元素收集到目的操作数dstReg中，index中每个元素表示相对于baseAddr的元素位置，支持多种数据类型组合。。二者在Reg Gather的index和baseAddr寻址合同与C API等价接口、维序/步长及LocalTensor基址故障直接对应上存在可执行的直接衔接。
<!-- cannbot:related:end -->
