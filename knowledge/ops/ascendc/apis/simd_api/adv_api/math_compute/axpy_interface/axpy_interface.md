---
type: API
title: Axpy接口
description: 提供Axpy(y=a*x+y)计算接口及其Tiling临时空间大小查询接口，包含Axpy、GetAxpyMaxMinTmpSize等。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Axpy_interface/Axpy_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Axpy接口

提供Axpy(y=a*x+y)计算接口及其Tiling临时空间大小查询接口，包含Axpy、GetAxpyMaxMinTmpSize等。

源操作数(srcTensor)中每个元素与标量求积后和目的操作数(dstTensor)中的对应元素相加，计算公式如下： 该接口功能同基础API Axpy，区别在于此接口指令是通过Muls和Add组合计算，从而提供更优的精度。

本接口组包含 Axpy。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。；该接口支持的精度组合如下：

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Axpy](../../../basic_api/memory_vector_compute/composite_compute/axpy.md)（`related`）：基础 Axpy 与高阶 Axpy 都实现 y=a*x+y，但前者是直接复合矢量接口，后者显式管理临时空间并强调 Muls+Add 精度；可据空间和精度约束选层级。
- [GetAxpyMaxMinTmpSize](get_axpy_max_min_tmp_size.md)（`related`）：Axpy 需要 sharedTmpBuffer 时，必须先用该接口取得满足当前 shape 的最大/最小临时空间，才能合法调用。
- [GetAxpyTmpBufferFactorSize](get_axpy_tmp_buffer_factor_size.md)（`related`）：该接口提供 Axpy 的 maxLiveNodeCount/extraBuf，可反推单次最大处理量并指导切块，是 Axpy Tiling 的直接输入。
- [AscAxpy](../../../c_api/reg/compound_compute/asc_axpy.md)（`same_topic`）：AscAxpy 与《Axpy接口》的衔接是：AscAxpy 的 C Vector、基础及高阶 Axpy 入口实现同一 alpha*x+y 数据流，差异集中在张量形态、临时空间和调度层级。
- [Axpy](axpy.md)（`same_topic`）：该接口页定义的临时空间、地址不重叠和 y=a*x+y 契约由 Axpy 计算接口直接实现。
<!-- cannbot:related:end -->
