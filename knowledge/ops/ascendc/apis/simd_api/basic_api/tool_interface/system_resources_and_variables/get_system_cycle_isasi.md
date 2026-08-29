---
type: API
title: GetSystemCycle
description: 获取系统计数器当前的cycle值，通过前后差值可计算代码段执行时间。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetSystemCycle_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# GetSystemCycle

头文件路径为："basic_api/kernel_operator_sys_var_intf.h"。

获取系统计数器当前的cycle值。通过计算代码段前后cycle值的差值，可得到代码段消耗的系统cycle数，再通过换算即可获得代码段的执行时间。

针对Ascend 950PR/Ascend 950DT，若换算成时间需要按照1GHz的频率，时间单位为us，换算公式为：time = (cycle数/1000)us。

针对Atlas A3 训练系列产品/Atlas A3 推理系列产品，若换算成时间需要按照50MHz的频率，时间单位为us，换算公式为：time = (cycle数/50)us。

针对Atlas A2 训练系列产品/Atlas A2 推理系列产品，若换算成时间需要按照50MHz的频率，时间单位为us，换算公式为：time = (cycle数/50)us。

约束：该接口属于PIPE_S流水，若需要测试其他流水的指令时间，需要在调用该接口前通过PipeBarrier插入对应流水的同步，具体

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [选择低延迟指令，优化归约操作性能](../../../../../guides/operator_practice/simd_operator_optimization/vector_compute/low_latency_instruction.md)（`explains`）：“输入shape为30000，数据类型为float时，如下示例的性能数据对比如下，数据单位为cycle，使用GetSystemCycle接口获取。”；“获取系统计数器当前的cycle值。通过计算代码段前后cycle值的差值，可得到代码段消耗的系统cycle数，再通过换算即可获得代码段的执行时间。”。GetSystemCycle 是指南中比较归约方案 cycle 的直接测量接口，并给出平台频率换算合同。
- [AscGetSystemCycle](../../../c_api/sys_var/asc_get_system_cycle.md)（`same_topic`）：获取系统计数器当前的cycle值。通过计算代码段前后cycle值的差值，可得到代码段消耗的系统cycle数，再通过换算即可获得代码段的执行时间。；读取当前系统cycle计数器，返回int64_t类型的当前计数值。该计数器为只读系统计数器，宽度64bit，复位值为0，随系统时钟持续递增，反映硬件运行以来的累计cycle数，常用于性能统计、耗时测量与执行序的时序判断。本接口在AIC与AIV上均可调用，返回值含义一致。。两张 API 卡描述同一只读系统 cycle 计数器的 C++ 与 C 接口语义，均用于前后差值计时。
<!-- cannbot:related:end -->
