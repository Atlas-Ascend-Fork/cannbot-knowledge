---
type: API
title: AscTransto5hd
description: 执行 NCHW 到 NC1HWC0 的格式转换，也可用于二维矩阵转置；单次 Repeat 最多处理 512 Byte。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_transto5hd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# AscTransto5hd

数据格式转换，一般用于将NCHW格式转换成NC1HWC0格式。特别的，也可以用于二维矩阵数据块的转置。本接口单次Repeat内可处理512Byte的数据（16个DataBlock），根据数据类型不同，支持不同shape的矩阵转置（比如数据类型为half时，单次Repeat可完成16*16大小的矩阵转置），同时还可以支持多次Repeat操作。 单次repeat内转换规则如下： 基于以上的转换规则，使用该接口进行NC1HWC0格式转换或者矩阵转置。NC1HWC0格式转换相对复杂，这里给出其具体的转换方法：
参数：dst（输出）：目的地址寄存器。；src（输入）：源地址寄存器。；repeat（输入）：重复迭代次数， repeat∈[0,255]。 注意事项： &bull;当repeat为1时，目的操作数/源操作数的有效起始位置为dst/src序列输入的起始位置加上dst_stride/src_stride。如果要让目的操作数/源操作数的有效起始位置为dst/src序列输入的起始位置，需要将dst_stride/src_stride置为0。 &bull;当repeat大于1时，第一次repeat中目的操作数/源操作数的有效起始位置为dst/src序列输入的起始位置，第二次会加上dst_stride/src_stride。以此类推。；dst_stride（输入）：相邻迭代间，目的操作数相同DataBlock地址Stride，单位：DataBlock。
约束：操作数地址对齐约束请参考存储单元说明。；操作数地址重叠约束请参考通用地址重叠约束。；进行NCHW格式到NC1HWC0格式的转换时，一般用法是将src/dst中的每个元素配置为每个HW平面的起点。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [TransDataTo5HD](../../basic_api/memory_vector_compute/data_layout_conversion/trans_data_to5_hd.md)（`related`）：两卡均执行 NCHW→NC1HWC0/5HD 转换；C 接口补充 512B repeat 和 stride 规则，基础 API 提供 LocalTensor 入口。
<!-- cannbot:related:end -->
