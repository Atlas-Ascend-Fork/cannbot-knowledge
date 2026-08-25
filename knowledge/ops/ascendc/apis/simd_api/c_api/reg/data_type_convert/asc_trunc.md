---
type: API
title: AscTrunc
description: 将浮点数按TRUNC（向零方向截断）截断为整数值，结果保持原浮点类型。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_trunc.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscTrunc

将src中的浮点数元素按照TRUNC（向零方向截断）截断到整数值，结果仍保持原浮点数据类型写入dst。未被mask筛选的元素置零。

关于舍入模式

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、half。

约束：float类型只支持不饱和模式。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscFloat2Int16](asc_float2int16.md)（`related`）：《AscFloat2Int16》处理“将float类型数据转化为int16_t类型，并支持多种舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式与饱和模式。 由于源操作数与目的操作数类型位宽比为2:1，写入数据时需要将一个VL大小的数据分为两部分，根据不同接口选择数据写入索引为奇数的位置或偶数的位置。”。《AscTrunc》明确提供“将浮点数按TRUNC（向零方向截断）截断为整数值，结果保持原浮点类型。”，其参数、调用或验证步骤直接接入float 到 int16 的同源同目标转换及 rounding/saturation 选择。
- [GetTruncMaxMinTmpSize](../../../adv_api/math_compute/trunc_interface/get_trunc_max_min_tmp_size.md)（`related`）：《AscTrunc》说明将浮点数按TRUNC（向零方向截断）截断为整数值，结果保持原浮点类型。；《GetTruncMaxMinTmpSize》说明在host侧获取Trunc接口计算所需最大和最小临时空间大小，供Tiling参数选择。。二者在AscTrunc与Memory Trunc、SIMT half/bfloat16/float变体共享向零截断语义，workspace查询用于高阶接口分块上存在可执行的直接衔接。
- [GetTruncTmpBufferFactorSize](../../../adv_api/math_compute/trunc_interface/get_trunc_tmp_buffer_factor_size.md)（`related`）：《AscTrunc》说明将浮点数按TRUNC（向零方向截断）截断为整数值，结果保持原浮点类型。；《GetTruncTmpBufferFactorSize》说明获取maxLiveNodeCount和extraBuf，用于推算Trunc接口在固定临时空间下单次最大计算元素数量。。二者在AscTrunc与Memory Trunc、SIMT half/bfloat16/float变体共享向零截断语义，workspace查询用于高阶接口分块上存在可执行的直接衔接。
- [H2Trunc](../../../../simt_api/math_functions/bfloat16_type/bfloat16x2_math_functions/h2trunc.md)（`related`）：《AscTrunc》说明将浮点数按TRUNC（向零方向截断）截断为整数值，结果保持原浮点类型。；《H2Trunc》说明获取对输入数据各元素的浮点数截断后的整数。。二者在AscTrunc与Memory Trunc、SIMT half/bfloat16/float变体共享向零截断语义，workspace查询用于高阶接口分块上存在可执行的直接衔接。
- [Htrunc](../../../../simt_api/math_functions/bfloat16_type/bfloat16_math_functions/htrunc.md)（`related`）：《AscTrunc》说明将浮点数按TRUNC（向零方向截断）截断为整数值，结果保持原浮点类型。；《Htrunc》说明获取对输入bfloat16_t数据浮点数截断后的整数。。二者在AscTrunc与Memory Trunc、SIMT half/bfloat16/float变体共享向零截断语义，workspace查询用于高阶接口分块上存在可执行的直接衔接。
- [Htrunc](../../../../simt_api/math_functions/half_type/half_math_functions/htrunc.md)（`related`）：《AscTrunc》说明将浮点数按TRUNC（向零方向截断）截断为整数值，结果保持原浮点类型。；《Htrunc》说明获取对输入half数据浮点数截断后的整数。。二者在AscTrunc与Memory Trunc、SIMT half/bfloat16/float变体共享向零截断语义，workspace查询用于高阶接口分块上存在可执行的直接衔接。
- [Truncf](../../../../simt_api/math_functions/float_math_functions/truncf.md)（`related`）：《AscTrunc》说明将浮点数按TRUNC（向零方向截断）截断为整数值，结果保持原浮点类型。；《Truncf》说明获取对输入数据的浮点数截断后的整数。。二者在AscTrunc与Memory Trunc、SIMT half/bfloat16/float变体共享向零截断语义，workspace查询用于高阶接口分块上存在可执行的直接衔接。
- [类型转换](data_type_convert.md)（`related`）：《AscTrunc》说明将浮点数按TRUNC（向零方向截断）截断为整数值，结果保持原浮点类型。；《类型转换》说明寄存器侧类型转换类接口汇总，覆盖bfloat16、half、float、int等数据类型间的相互转换及取整操作。。二者在AscTrunc与Memory Trunc、SIMT half/bfloat16/float变体共享向零截断语义，workspace查询用于高阶接口分块上存在可执行的直接衔接。
- [H2Trunc](../../../../simt_api/math_functions/half_type/half2_math_functions/h2trunc.md)（`same_topic`）：AscTrunc 与 H2Trunc 都按向零方向把浮点值截到整数值并保持浮点载体；前者处理 Reg 向量，后者处理 half2 两 lane。
- [Trunc](../../../adv_api/math_compute/trunc_interface/trunc.md)（`same_topic`）：《AscTrunc》说明将浮点数按TRUNC（向零方向截断）截断为整数值，结果保持原浮点类型。；《Trunc》说明按元素做浮点数截断，即向零取整操作。。二者在AscTrunc与Memory Trunc、SIMT half/bfloat16/float变体共享向零截断语义，workspace查询用于高阶接口分块上存在可执行的直接衔接。
- [Trunc接口](../../../adv_api/math_compute/trunc_interface/trunc_interface.md)（`same_topic`）：《AscTrunc》说明将浮点数按TRUNC（向零方向截断）截断为整数值，结果保持原浮点类型。；《Trunc接口》说明按元素做浮点数截断（向零取整），并提供临时空间大小获取接口。。二者在AscTrunc与Memory Trunc、SIMT half/bfloat16/float变体共享向零截断语义，workspace查询用于高阶接口分块上存在可执行的直接衔接。
<!-- cannbot:related:end -->
