---
type: API
title: Acosh接口
description: 提供Acosh反双曲余弦计算接口及其Tiling临时空间大小查询接口，包含Acosh、GetAcoshMaxMinTmpSize等。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Acosh_interface/Acosh_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Acosh接口

提供Acosh反双曲余弦计算接口及其Tiling临时空间大小查询接口，包含Acosh、GetAcoshMaxMinTmpSize等。

按元素做双曲反余弦函数计算，计算公式如下：

本接口组包含 Acosh。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：输入源数据需保持值域在[1, 65504]。若输入不在范围内，输出结果无效。；不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Acosh](acosh.md)（`same_topic`）：《Acosh接口》明确“提供Acosh反双曲余弦计算接口及其Tiling临时空间大小查询接口，包含Acosh、GetAcoshMaxMinTmpSize等。”；它与《Acosh》的“按元素做双曲反余弦函数计算，输入值域需在1到65504范围内”在实际调用参数、数据流或结果校验上直接衔接。
- [Acoshf](../../../../simt_api/math_functions/float_math_functions/acoshf.md)（`same_topic`）：Acoshf 与《Acosh接口》的实质衔接是：Acoshf 是标量双曲反余弦；Acosh 高阶接口及空间查询是 tensor 版本，Coshf 是其反函数，可用于定义域和往返验证。
- [GetAcoshTmpBufferFactorSize](get_acosh_tmp_buffer_factor_size.md)（`same_topic`）：《Acosh接口》明确“提供Acosh反双曲余弦计算接口及其Tiling临时空间大小查询接口，包含Acosh、GetAcoshMaxMinTmpSize等。”；它与《GetAcoshTmpBufferFactorSize》的“获取Acosh接口的maxLiveNodeCount和extraBuffer，用于推算固定空间下单次最大计算元素数”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
