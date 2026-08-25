---
type: API
title: ResetLoopModePara
description: 重置loop mode参数，与SetLoopModePara搭配使用，在使能loop mode的数据搬运结束后调用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move_aux_config/ResetLoopModePara.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# ResetLoopModePara

重置loop mode参数，与SetLoopModePara搭配使用，在使能loop mode的数据搬运结束后调用。

DataCopy、DataCopyPad过程中通过该接口使能loop mode并且设置loop mode的参数，在数据搬运结束后通过ResetLoopModePara重置loop mode的参数。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Global Memory -> Unified Buffer - GM -> VECIN - Unified Buffer -> Global Memory - VECOUT -> GM

本接口组包含 SetLoopModePara, 逻辑位置TPosition, SetLoopModePara。

本接口属于 UB 矢量计算数据搬移接口，用于不同存储间的数据拷贝。

约束：源操作数和目的操作数的起始地址需要保证32字节对齐。；目的操作数的数据不能重叠，如果有重叠，硬件层面不会报错或者告警，同时也不能保证重叠数据的正确性；但是不同迭代可以交织，例如内层循环中相邻迭代目的操作数的数据块间的间隔可以小于相邻连续目的操作数的数据块的间隔。；需要在每次使能loop mode并且设置loop mode的参数后通过ResetLoopModePara进行寄存器的复位，否则会影响到下一次对应通路的搬运的使用，引发异常。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
