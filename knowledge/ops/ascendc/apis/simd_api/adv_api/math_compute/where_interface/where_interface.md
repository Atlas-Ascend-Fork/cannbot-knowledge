---
type: API
title: Where接口
description: 根据条件从两个源操作数中选择元素生成目标操作数，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Where_interface/Where_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Where接口

根据条件从两个源操作数中选择元素生成目标操作数，并提供临时空间大小获取接口。

根据指定的条件，从两个源操作数中选择元素，生成目标操作数。两个源操作数均可以是LocalTensor或标量。

本接口组包含 Where。

本接口属于高阶数学计算接口。

支持的数据类型为 bool、int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、int64_t、uint64_t。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：不支持源操作数与目的操作数地址重叠。；操作数地址偏移对齐要求请参见通用说明和约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Where（数学计算）](where.md)（`same_topic`）：《Where接口》明确“根据条件从两个源操作数中选择元素生成目标操作数，并提供临时空间大小获取接口。”；它与《Where（数学计算）》的“根据指定的条件，从两个源操作数中选择元素，生成目标操作数。两个源操作数均可以是LocalTensor或标量。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
