---
type: API
title: Asinh接口
description: 提供Asinh反双曲正弦计算接口及其Tiling临时空间大小查询接口，包含Asinh、GetAsinhMaxMinTmpSize等。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Asinh_interface/Asinh_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Asinh接口

提供Asinh反双曲正弦计算接口及其Tiling临时空间大小查询接口，包含Asinh、GetAsinhMaxMinTmpSize等。

按元素做反双曲正弦函数计算，计算公式如下：

本接口组包含 Asinh。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：输入源数据需保持值域在[-65504, 65504]。若输入不在范围内，输出结果无效。；不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Asinhf](../../../../simt_api/math_functions/float_math_functions/asinhf.md)（`related`）：《Asinhf》明确“获取输入数据的双曲反正弦值。”；它与《Asinh接口》的“提供Asinh反双曲正弦计算接口及其Tiling临时空间大小查询接口，包含Asinh、GetAsinhMaxMinTmpSize等。”在实际调用参数、数据流或结果校验上直接衔接。
- [GetAsinhTmpBufferFactorSize](get_asinh_tmp_buffer_factor_size.md)（`related`）：《GetAsinhTmpBufferFactorSize》明确“获取Asinh接口的maxLiveNodeCount和extraBuffer，用于推算固定空间下单次最大计算元素数”；它与《Asinh接口》的“提供Asinh反双曲正弦计算接口及其Tiling临时空间大小查询接口，包含Asinh、GetAsinhMaxMinTmpSize等。”在实际调用参数、数据流或结果校验上直接衔接。
- [Sinh接口](../sinh_interface/sinh_interface.md)（`related`）：Asinh 是反函数且资源/数值边界不同，不能作为 Sinh 替代。
- [Asinh](asinh.md)（`same_topic`）：《Asinh》明确“按元素做反双曲正弦函数计算，输入值域需在-65504到65504范围内”；它与《Asinh接口》的“提供Asinh反双曲正弦计算接口及其Tiling临时空间大小查询接口，包含Asinh、GetAsinhMaxMinTmpSize等。”在实际调用参数、数据流或结果校验上直接衔接。
- [GetAsinhMaxMinTmpSize](get_asinh_max_min_tmp_size.md)（`same_topic`）：《GetAsinhMaxMinTmpSize》的任务是“在host侧获取Asinh接口预留临时空间的最大和最小值，用于Tiling参数选择”。《Asinh接口》具体提供“提供Asinh反双曲正弦计算接口及其Tiling临时空间大小查询接口，包含Asinh、GetAsinhMaxMinTmpSize等。”，它直接用于Asinh workspace 上下界和 factor 到 Kernel 的同一空间合同。
<!-- cannbot:related:end -->
