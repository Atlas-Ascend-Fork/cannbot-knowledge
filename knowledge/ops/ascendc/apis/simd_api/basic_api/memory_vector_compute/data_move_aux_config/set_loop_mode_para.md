---
type: API
title: SetLoopModePara
description: 使能并设置DataCopy/DataCopyPad的loop mode参数，支持GM与UB之间的双向数据搬运循环模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move_aux_config/SetLoopModePara.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# SetLoopModePara

使能并设置DataCopy/DataCopyPad的loop mode参数，支持GM与UB之间的双向数据搬运循环模式。

重置loop mode的参数。与SetLoopModePara搭配使用，在使能loop mode并且设置loop mode的参数的数据搬运场景下，数据搬运结束后需要调用该函数来重置loop mode参数。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Global Memory -> Unified Buffer - GM -> VECIN - Unified Buffer -> Global Memory - VECOUT -> GM

本接口组包含 ResetLoopModePara, 逻辑位置TPosition。

本接口属于 UB 矢量计算数据搬移接口，用于不同存储间的数据拷贝。

约束：与SetLoopModePara搭配使用。在使能loop mode并完成数据搬运后，必须调用该接口重置loop mode参数，否则会影响下一次对应通路的数据搬运，引发异常。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [数据搬运辅助配置接口](data_move_aux_config.md)（`related`）：SetLoopModePara 设置循环搬运参数，与 ResetLoopModePara 构成状态启用和复位的完整调用链。
- [ResetLoopModePara](reset_loop_mode_para.md)（`same_topic`）：焦点处理DataCopy loop mode 的状态复位；SetLoopModePara正文界定“使能并设置DataCopy/DataCopyPad的loop mode参数，支持GM与UB之间的双向数据搬运循环模式”。候选是 ResetLoopModePara 对应的 SetLoopModePara，构成唯一状态配对。
<!-- cannbot:related:end -->
