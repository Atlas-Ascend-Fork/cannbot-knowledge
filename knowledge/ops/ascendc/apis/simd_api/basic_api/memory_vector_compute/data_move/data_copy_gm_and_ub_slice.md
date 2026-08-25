---
type: API
title: DataCopy
description: 软仿接口，支持数据的切片搬运，提取多维Tensor数据的子集进行搬运。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopy_GMAndUB_slice.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# DataCopy

软仿接口，支持数据的切片搬运，提取多维Tensor数据的子集进行搬运。

该接口为软仿接口，从易用性角度出发进行设计，支持数据的切片搬运，提取多维Tensor数据的子集进行搬运。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Global Memory -> Unified Buffer - GM -> VECIN - Unified Buffer -> Global Memory - VECOUT -> GM - CO2 -> GM（仅Atlas 推理系列产品AI Core支持）

支持的数据通路：具体支持的数据通路为（以逻辑位置TPosition表示）：

- Global Memory -> Unified Buffer
    - GM -> VECIN
- Unified Buffer -> Global Memory
    - VECOUT -> GM

    - CO2 -> GM（仅Atlas 推理系列产品AI Core支持）



本接口属于 UB 矢量计算数据搬移接口，用于不同存储间的数据拷贝。

参数说明：T：源操作数或者目的操作数的数据类型。支持的数据类型请参考[数据类型](#zh-cn_topic_0000002565968945_section4219135304818)。；dst：输出 目的操作数。 •类型为LocalTensor时，存储位置为Unified Buffer，目的地址需要32字节对齐。 •类型为GlobalTensor时，存储位置为Global Memory，目的地址需要1字节对齐。；src：输入 源操作数。 •类型为GlobalTensor时，存储位置为Global Memory，源地址需要1字节对齐。 •类型为LocalTensor时，存储位置为Unified Buffer，源地址需要32字节对齐。；dstSliceInfo：输入 目的操作数切片信息，类型为SliceInfo。通过该参数可以配置切片的起始和终止元素个数、间隔、长度等信息。 SliceInfo参数说明请参考[表3](#table_slice_3)。；srcSliceInfo：输入 源操作数切片信息，类型为SliceInfo。通过该参数可以配置切片的起始和终止元素个数、间隔、长度等信息。 具体定义请参考`${INSTALL_DIR}/asc/include/basic_api/kernel_struct_data_copy.h`，`${INSTALL_DIR}`请替换为CANN软件安装后文件存储路径。 SliceInfo参数说明请参考[表3](#table_slice_3)。

约束：该接口为软仿接口，从易用性角度出发进行设计。；位于Global Memory的地址必须1字节对齐，位于Unified Buffer的地址必须32字节对齐。；burstLen，仅在dimValue = 1时生效，超出1维的情况下，必须配置为1，不支持配置成其他值。；切片数据搬运中的横向burstLen大小设置，需要用户自己通过计算：横向切片元素个数* sizeof(T)/32字节。横向切片元素个数* sizeof(T)的大小必须是32字节的倍数。
