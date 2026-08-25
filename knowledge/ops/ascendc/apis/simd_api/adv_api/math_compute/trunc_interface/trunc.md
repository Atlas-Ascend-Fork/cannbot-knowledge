---
type: API
title: Trunc
description: 按元素做浮点数截断，即向零取整操作。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Trunc_interface/Trunc.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# Trunc

按元素做浮点数截断，即向零取整操作（Trunc(3.9)=3, Trunc(-3.9)=-3）。模板参数T支持half/float。

提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetTruncMaxMinTmpSize获取。

模板参数isReuseSource预留，传入false即可。接口参数：dstTensor为输出操作数；srcTensor为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetTruncMaxMinTmpSize](get_trunc_max_min_tmp_size.md)（`related`）：GetTruncMaxMinTmpSize 按 shape/typeSize/isReuseSource 给出 Kernel Trunc 临时空间的硬下界与性能上界。
- [GetTruncTmpBufferFactorSize](get_trunc_tmp_buffer_factor_size.md)（`related`）：GetTruncTmpBufferFactorSize 与《Trunc》的实质衔接是：Trunc 的 factor-size 查询要与 Trunc kernel 及 max/min 空间查询配套，才能按 maxLiveNodeCount/extraBuf 正确反推 tile。
- [Truncate](../../../basic_api/reg_vector_compute/type_conversion/truncate.md)（`related`）：Advanced Trunc 固定向零截断，而 Reg Truncate 可选择 RINT、ROUND、FLOOR、CEIL 或 TRUNC。
- [AscFloat2float](../../../c_api/vector_compute/asc_float2float.md)（`same_topic`）：AscFloat2float 与《Trunc》的实质衔接是：AscFloat2float 通过舍入模式规范同类型值；SIMT 同名转换和 Rint/Round/Floor/Ceil/Trunc 卡提供每种模式的确切数学定义。
- [AscTrunc](../../../c_api/reg/data_type_convert/asc_trunc.md)（`same_topic`）：《AscTrunc》说明将浮点数按TRUNC（向零方向截断）截断为整数值，结果保持原浮点类型。；《Trunc》说明按元素做浮点数截断，即向零取整操作。。二者在AscTrunc与Memory Trunc、SIMT half/bfloat16/float变体共享向零截断语义，workspace查询用于高阶接口分块上存在可执行的直接衔接。
- [H2Trunc](../../../../simt_api/math_functions/half_type/half2_math_functions/h2trunc.md)（`same_topic`）：H2Trunc 与《Trunc》的实质衔接是：这些接口执行向零取整或与之紧邻的 floor/rint 舍入；half2、bfloat16x2、标量、SIMD 与 C 版本用于在数据宽度和执行层变化时保持 trunc 语义。
- [Truncate](../../../basic_api/memory_vector_compute/type_conversion/truncate_isasi.md)（`same_topic`）：《Truncate》处理“将源操作数的浮点数元素截断到整数位，保持原数据类型不变，支持多种舍入模式。”。《Trunc》明确“按元素做浮点数截断，即向零取整操作。”，可直接用于核对Truncate 向零取整在 Cast round-mode、高阶/基础/SIMT 接口中的等价语义。
- [Truncf](../../../../simt_api/math_functions/float_math_functions/truncf.md)（`same_topic`）：Truncf 与《Trunc》的实质衔接是：Truncf 与 SIMD、基础、C、half/half2/bfloat16x2 Trunc 都实现向零截断；空间查询只适用于高阶 tensor 版本，不能套到标量入口。
- [Trunc接口](trunc_interface.md)（`same_topic`）：《Trunc》明确“按元素做浮点数截断，即向零取整操作。”；它与《Trunc接口》的“按元素做浮点数截断（向零取整），并提供临时空间大小获取接口。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
