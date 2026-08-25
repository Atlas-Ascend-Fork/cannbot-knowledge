---
type: API
title: AscShflUp
description: 获取Warp内当前线程向前偏移delta的线程变量值，支持width参数划分分组
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/Warp_functions/Warp_shfl_functions/asc_shfl_up.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_shfl_up

获取Warp内当前线程向前偏移delta（当前线程Lane ID - delta）的线程输入的用于交换的var值；如果目标线程是非活跃状态，获取到寄存器中未初始化的值。其中，参数width用于划分Warp内线程的分组。参数width设置参与交换的32个线程的分组宽度，默认值为32，即所有线程分为1组。

在多个分组场景（width小于32）下，每个分组交换操作是独立的，每个线程获取本组内当前线程向前偏移delta的线程的var值。如果当前线程向前偏移delta的线程编号，即Lane ID - delta，小于所在分组的起始Lane ID，则返回当前线程的var值。

例如，Warp内32个活跃线程调用asc_shfl_up(LaneId, 2, 16)接口，每个线程的返回值为当前线程Lane ID - 2对应线程的var值，或者当前线程的var值。

函数原型：inline int32_t asc_shfl_up(int32_t var, uint32_t delta, int32_t width = warpSize)；inline uint32_t asc_shfl_up(uint32_t var, uint32_t delta, int32_t width = warpSize)；inline float asc_shfl_up(float var, uint32_t delta, int32_t width = warpSize) 等9种重载

参数：var（输入）：线程用于交换的输入操作数。；delta（输入）：期望获取的var值所在线程相对当前线程的向前偏移值。；width（输入）：Warp内参与交换的线程的分组宽度，默认值为32。width的取值范围为(0, 32]，width必须是2的倍数。

返回值：Warp内指定线程的var值。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。
约束：-   如果目标线程是非活跃状态，获取到寄存器中未初始化的值。
-   若delta >=width，所有线程都返回当前线程的var值。
-   width不是2的倍数或者超出32，返回值异常。
需包含头文件 "simt_api/device_warp_functions.h"。
支持 SIMT 与 SIMD/SIMT 混合编程场景。
