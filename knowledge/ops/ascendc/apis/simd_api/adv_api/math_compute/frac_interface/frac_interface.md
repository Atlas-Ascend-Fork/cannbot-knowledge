---
type: API
title: Frac接口
description: 按元素取小数部分，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Frac_interface/Frac_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Frac接口

按元素取小数部分，并提供临时空间大小获取接口。

按元素做取小数计算。计算公式如下： 举例如下： Frac(-258.41888) = -0.41888428 Frac(5592.625) = 0.625

本接口组包含 Frac。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：针对Atlas 推理系列产品AI Core，输入数据限制在[-2147483647.0, 2147483647.0]范围内。；不支持源操作数与目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [GetFracMaxMinTmpSize](get_frac_max_min_tmp_size.md)（`related`）：《GetFracMaxMinTmpSize》明确“在host侧获取Frac接口预留或申请临时空间的最大和最小值，用于Tiling参数传递”；它与《Frac接口》的“按元素取小数部分，并提供临时空间大小获取接口。”在实际调用参数、数据流或结果校验上直接衔接。
- [GetFracTmpBufferFactorSize](get_frac_tmp_buffer_factor_size.md)（`related`）：《GetFracTmpBufferFactorSize》明确“获取Frac接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量”；它与《Frac接口》的“按元素取小数部分，并提供临时空间大小获取接口。”在实际调用参数、数据流或结果校验上直接衔接。
- [Trunc接口](../trunc_interface/trunc_interface.md)（`related`）：《Trunc接口》明确“按元素做浮点数截断（向零取整），并提供临时空间大小获取接口。”；它与《Frac接口》的“按元素取小数部分，并提供临时空间大小获取接口。”在实际调用参数、数据流或结果校验上直接衔接。
- [Frac](frac.md)（`same_topic`）：《Frac》明确“按元素做取小数计算，返回输入数据的小数部分，支持half和float数据类型。”；它与《Frac接口》的“按元素取小数部分，并提供临时空间大小获取接口。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
