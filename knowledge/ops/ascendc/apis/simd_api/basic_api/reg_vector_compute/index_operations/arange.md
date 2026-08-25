---
type: API
title: Arange
description: 以传入标量值为起始或终止值，生成递增或递减的索引序列并保存在目的寄存器中。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/index_operations/Arange.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Arange

头文件路径为："basic_api/reg_compute/kernel_reg_compute_vec_arange_intf.h"。

递增模式时，该函数以传入的scalarValue的值为起始值，生成递增的索引；递减模式时，该函数以传入的scalarValue的值为终止值，生成递减的索引，并将索引保存在dstReg中。

参数：T: 目的操作数的数据类型。；IndexOrder: 递增/递减模式。支持如下取值： • INCREASE_ORDER：递增模式 • DECREASE_ORDER：递减模式；U: 起始索引值的数据类型。；S: 目的操作数的RegTensor类型，例如RegTensor，由编译器自动推导，无需用户显式指定。；dstReg(输出): 目的操作数。 类型为RegTensor。；scalarValue(输入): 源操作数。 类型为标量。

支持数据类型：int8_t/int16_t/int32_t/half/float/int64_t。

约束：对于int8_t/int16_t/int32_t/int64_t，当索引超过该数据类型的边界值时会翻转为负数，如对于int8_t，127之后为-128、-127，以此类推。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [GetArangeMaxMinTmpSize](../../../adv_api/index_compute/get_arange_max_min_tmp_size.md)（`related`）：Reg Arange 是不依赖高阶 workspace 的寄存器路径。
- [SetSplitRange](../../../adv_api/cube_compute/matmul_tiling/set_split_range.md)（`related`）：Arange 常用于构造索引，而 SetSplitRange 定义 Matmul 切分区间；仅在生成切分索引时衔接。
- [Arange（索引计算）](../../../adv_api/index_compute/arange.md)（`same_topic`）：高阶 LocalTensor Arange 提供同任务的 workspace 路径。
- [AscArange](../../../c_api/reg/index_operate/asc_arange.md)（`same_topic`）：AscArange：AscArange、Reg Arange 与高级 Arange 都生成等差索引序列，差异在寄存器、LocalTensor和临时空间调用契约，适合实现路线互查。 目标卡《Arange》补充：以传入标量值为起始或终止值，生成递增或递减的索引序列并保存在目的寄存器中。
<!-- cannbot:related:end -->
