---
type: API
title: Ceil接口
description: 提供Ceil向上取整计算接口及其Tiling临时空间大小查询接口，包含Ceil、GetCeilMaxMinTmpSize等。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Ceil_interface/Ceil_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Ceil接口

提供Ceil向上取整计算接口及其Tiling临时空间大小查询接口，包含Ceil、GetCeilMaxMinTmpSize等。

获取大于或等于x的最小的整数值，即向正无穷取整操作。计算公式如下： 举例如下： Ceil(3.9) = 4.0 Ceil (-3.9) = -3.0

本接口组包含 Ceil。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：针对Atlas 推理系列产品AI Core，输入数据限制在[-2147483647.0, 2147483647.0]范围内。；不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [多核 ceil 尾块为负 — 每核按 remaining 截断](../../../../../runbooks/precision/ceil_partition_each_core_must_clamp_remaining.md)（`exemplifies`）：《Ceil接口》说明提供Ceil向上取整计算接口及其Tiling临时空间大小查询接口，包含Ceil、GetCeilMaxMinTmpSize等。；《多核 ceil 尾块为负 — 每核按 remaining 截断》说明ceil 分块后预计算末核 tail 可为负并让中后核越界；改为每核按 total-start 截断。。二者在Ceil计算、临时空间估算与多核尾段切分共同决定向上取整算子的正确执行上存在可执行的直接衔接。
- [Ceil](ceil.md)（`same_topic`）：《Ceil接口》说明提供Ceil向上取整计算接口及其Tiling临时空间大小查询接口，包含Ceil、GetCeilMaxMinTmpSize等。；《Ceil》说明获取大于或等于输入值的最小整数，即向正无穷方向取整。二者在Ceil计算、临时空间估算与多核尾段切分共同决定向上取整算子的正确执行上存在可执行的直接衔接。
- [Ceilf](../../../../simt_api/math_functions/float_math_functions/ceilf.md)（`same_topic`）：Ceilf 是 float 标量 SIMT 入口，Ceil 高阶接口对 LocalTensor 逐元素向正无穷取整并定义临时空间合同。
- [GetCeilMaxMinTmpSize](get_ceil_max_min_tmp_size.md)（`same_topic`）：《Ceil接口》说明提供Ceil向上取整计算接口及其Tiling临时空间大小查询接口，包含Ceil、GetCeilMaxMinTmpSize等。；《GetCeilMaxMinTmpSize》说明在host侧获取Ceil接口预留临时空间的最大和最小值，用于Tiling参数选择。二者在Ceil计算、临时空间估算与多核尾段切分共同决定向上取整算子的正确执行上存在可执行的直接衔接。
- [GetCeilTmpBufferFactorSize](get_ceil_tmp_buffer_factor_size.md)（`same_topic`）：《Ceil接口》说明提供Ceil向上取整计算接口及其Tiling临时空间大小查询接口，包含Ceil、GetCeilMaxMinTmpSize等。；《GetCeilTmpBufferFactorSize》说明获取Ceil接口的maxLiveNodeCount和extraBuf，用于推算固定空间下单次最大计算元素数。二者在Ceil计算、临时空间估算与多核尾段切分共同决定向上取整算子的正确执行上存在可执行的直接衔接。
<!-- cannbot:related:end -->
