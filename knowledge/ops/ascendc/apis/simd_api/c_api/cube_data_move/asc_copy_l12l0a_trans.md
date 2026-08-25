---
type: API
title: AscCopyL12l0aTrans
description: 将2D格式数据带转置地从L1 Buffer加载到L0A Buffer。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_l12l0a_trans.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---
# AscCopyL12l0aTrans

该接口实现带转置的2D格式数据从L1 Buffer到L0A Buffer的加载。

下面通过示例来讲解接口功能和关键参数：下文图中一个N形或者一个Z形代表一个分形。

- 对于uint8_t/int8_t数据类型，每次迭代处理32 × 32 × 1B数据，可处理2个分形（一个分形512B），每次迭代中，源操作数中2个连续的16 × 32分形将被合并为1个32 × 32的方块矩阵，基于方块矩阵做转置，转置后分裂为2个16 × 32分形，根据目的操作数分形间隔等参数可以有不同的排布。

如下图示例
- 共处理3072B的数据，每次迭代处理32 × 32 × 1B数据，需要3次迭代可以完成，repeat_time = 3；
- src_stride = 1，表示相邻迭代间，源操作数前一个方块矩阵与后一个方块矩阵起始地址的间隔为1（单位：32 × 32 × 1B），这里的单位实际上是拼接后的方块矩阵的大小；

参数：dst(输出): 目的操作数。；src(输入): 源操作数。；index_id(输入): 方块矩阵的ID，搬运起始位置为源操作数中第几个方块矩阵（0为源操作数中第1个方块矩阵）。取值范围：index_id∈[0, 65535]。；repeat(输入): 迭代重复次数。repeat∈[0, 255]。 对于uint8_t/int8_t数据类型，每次迭代处理32 × 32 × 1B数据； 对于half/bfloat16_t数据类型，每次迭代处理16 × 16 × 2B数据； 对于float/int32_t/uint32_t数据类型，每次迭代处理16 × 16 × 4B数据。；src_stride(输入): 表示相邻迭代间，源操作数前一个方块矩阵与后一个方块矩阵起始地址的间隔，单位：（1024B）。取值范围：src_stride∈[0, 65535]。 对于uint8_t/int8_t数据类型，单位是32 × 32 × 1B； 对于half/bfloat16_t数据类型，单位是16 × 16 × 2B； 对于float/int32_t/uint32_t数据类型，单位是16 × 16 × 4B； 对于int4b_t数据类型，每次迭代处理16 × 64 × 0.5B数据。；dst_gap(输入): 表示相邻迭代间，目的操作数前一个迭代第一个分形的结束地址到下一个迭代第一个分形起始地址的间隔。取值范围：dst_gap∈[0, 65535]。

约束：- 各存储单元的空间大小和对齐要求
- repeat=0表示不执行搬运操作。
- 开发者需要保证目的操作数转置后的分形没有重叠。

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。
