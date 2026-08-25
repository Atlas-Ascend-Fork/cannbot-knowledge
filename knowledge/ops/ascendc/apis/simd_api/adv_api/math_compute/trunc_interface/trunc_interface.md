---
type: API
title: Trunc接口
description: 按元素做浮点数截断（向零取整），并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Trunc_interface/Trunc_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Trunc接口

按元素做浮点数截断（向零取整），并提供临时空间大小获取接口。

按元素做浮点数截断，即向零取整操作。计算公式如下： 举例如下： Trunc(3.9) = 3 Trunc(-3.9) = -3

本接口组包含 Trunc。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：针对Atlas 推理系列产品AI Core，输入数据限制在[-2147483647.0, 2147483647.0]范围内。；支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Frac](../frac_interface/frac.md)（`related`）：Frac 返回带符号小数部分，而 Trunc 定义向零取整；用 x-Trunc(x) 可构造与 Frac(-x) 符号一致的独立 oracle。
- [Frac接口](../frac_interface/frac_interface.md)（`related`）：《Trunc接口》明确“按元素做浮点数截断（向零取整），并提供临时空间大小获取接口。”；它与《Frac接口》的“按元素取小数部分，并提供临时空间大小获取接口。”在实际调用参数、数据流或结果校验上直接衔接。
- [GetTruncTmpBufferFactorSize](get_trunc_tmp_buffer_factor_size.md)（`related`）：GetTruncTmpBufferFactorSize 与《Trunc接口》的实质衔接是：Trunc 的 factor-size 查询要与 Trunc kernel 及 max/min 空间查询配套，才能按 maxLiveNodeCount/extraBuf 正确反推 tile。
- [AscTrunc](../../../c_api/reg/data_type_convert/asc_trunc.md)（`same_topic`）：《AscTrunc》说明将浮点数按TRUNC（向零方向截断）截断为整数值，结果保持原浮点类型。；《Trunc接口》说明按元素做浮点数截断（向零取整），并提供临时空间大小获取接口。。二者在AscTrunc与Memory Trunc、SIMT half/bfloat16/float变体共享向零截断语义，workspace查询用于高阶接口分块上存在可执行的直接衔接。
- [GetTruncMaxMinTmpSize](get_trunc_max_min_tmp_size.md)（`same_topic`）：GetTruncMaxMinTmpSize 的核心契约是“在host侧获取Trunc接口计算所需最大和最小临时空间大小，供Tiling参数选择”；Trunc接口 补充“按元素做浮点数截断（向零取整），并提供临时空间大小获取接口”。
- [Trunc](trunc.md)（`same_topic`）：《Trunc》明确“按元素做浮点数截断，即向零取整操作。”；它与《Trunc接口》的“按元素做浮点数截断（向零取整），并提供临时空间大小获取接口。”在实际调用参数、数据流或结果校验上直接衔接。
- [Truncate](../../../basic_api/memory_vector_compute/type_conversion/truncate_isasi.md)（`same_topic`）：《Truncate》处理“将源操作数的浮点数元素截断到整数位，保持原数据类型不变，支持多种舍入模式。”。《Trunc接口》明确“按元素做浮点数截断（向零取整），并提供临时空间大小获取接口。”，可直接用于核对Truncate 向零取整在 Cast round-mode、高阶/基础/SIMT 接口中的等价语义。
- [Truncf](../../../../simt_api/math_functions/float_math_functions/truncf.md)（`same_topic`）：Truncf 与《Trunc接口》的实质衔接是：Truncf 与 SIMD、基础、C、half/half2/bfloat16x2 Trunc 都实现向零截断；空间查询只适用于高阶 tensor 版本，不能套到标量入口。
<!-- cannbot:related:end -->
