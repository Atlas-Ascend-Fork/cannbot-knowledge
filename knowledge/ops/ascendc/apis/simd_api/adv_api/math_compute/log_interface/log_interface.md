---
type: API
title: Log接口
description: 按元素以e、2、10为底做对数运算，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Log_interface/Log_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Log接口

按元素以e、2、10为底做对数运算，并提供临时空间大小获取接口。

按元素以e、2、10为底做对数运算，计算公式如下：

本接口组包含 Log。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：不支持源操作数与目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core, Kirin X90。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [GetLogMaxMinTmpSize](get_log_max_min_tmp_size.md)（`related`）：Log 的 sharedTmpBuffer 可由该 Host 查询取得最大/最小边界，再作为 Tiling 依据。
- [GetLogTmpBufferFactorSize](get_log_tmp_buffer_factor_size.md)（`related`）：Factor 查询把固定空间换算为 Log/Log2/Log10 单次最大元素数，补齐切块决策。
- [Log](../../../basic_api/reg_vector_compute/basic_arithmetic/log.md)（`related`）：高阶 Log 作用于 LocalTensor 并管理临时空间，Reg Log 直接作用寄存器并用 mask；同为自然对数时可按编程层级和融合需求选择。
- [Log](log.md)（`same_topic`）：总览中的 e/2/10 底数选择、LocalTensor 与 sharedTmpBuffer 约束由 Log 具体接口实现。
<!-- cannbot:related:end -->
