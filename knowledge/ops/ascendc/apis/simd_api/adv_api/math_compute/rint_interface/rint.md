---
type: API
title: Rint
description: 获取与输入数据最接近的整数，等距时取偶数
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Rint_interface/Rint.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# Rint

获取与输入数据最接近的整数，若存在两个同样接近的整数则取偶数（Rint(3.9)=4, Rint(3.3)=3, Rint(3.5)=4）。模板参数T支持half/float。仅Ascend 950PR/950DT支持。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetRintMaxMinTmpSize获取。

模板参数config为RintConfig类型，含isReuseSource（预留，传false）。接口参数：dst为输出操作数，TPosition支持VECIN/VECCALC/VECOUT；src为输入操作数，数据类型需与dst一致；sharedTmpBuffer为临时缓存；count为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [AscFloat2Int32](../../../c_api/scalar_compute/asc_float2int32.md)（`related`）：AscFloat2Int32 与《Rint》的实质衔接是：AscFloat2Int32 的四种舍入模式对应 Rint/Round/Floor/Ceil，相关 float/half/bfloat16 转换卡用于保持目标位宽、源类型和逆转换契约。
- [AscRint](../../../c_api/reg/data_type_convert/asc_rint.md)（`related`）：Advanced Rint 与 AscRint 都执行 ties-to-even 且保持浮点结果，前者面向 LocalTensor，后者面向寄存器。
- [AscFloat2float](../../../c_api/vector_compute/asc_float2float.md)（`same_topic`）：AscFloat2float 与《Rint》的实质衔接是：AscFloat2float 通过舍入模式规范同类型值；SIMT 同名转换和 Rint/Round/Floor/Ceil/Trunc 卡提供每种模式的确切数学定义。
- [AscMulCastHalf2int8](../../../c_api/vector_compute/asc_mul_cast_half2int8.md)（`same_topic`）：AscMulCastHalf2int8 与《Rint》的实质衔接是：AscMulCastHalf2int8 融合 half 乘法、RINT 和 int8 饱和；MulCast、纯 Mul、Half2Int8 与 Rint 入口分别核对融合、目标宽度和舍入。
- [GetRintMaxMinTmpSize](get_rint_max_min_tmp_size.md)（`same_topic`）：焦点处理Rint 临时空间上下界与 factor 的配套 Tiling 契约；Rint正文说明“获取与输入数据最接近的整数，等距时取偶数”。候选把 host 侧 max/min 查询、factor 推算与 Rint kernel 调用连成同一 Tiling 参数链。
- [GetRintTmpBufferFactorSize](get_rint_tmp_buffer_factor_size.md)（`same_topic`）：GetRintTmpBufferFactorSize说明获取Rint接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量。
- [Rint接口](rint_interface.md)（`same_topic`）：“Rint接口”定义：按元素取最接近的整数，同等接近时取偶数，并提供临时空间大小获取接口。；“Rint”定义：获取与输入数据最接近的整数，等距时取偶数。实质衔接：Rint 接口页汇总 kernel 操作与两种临时空间估算；AscRint 提供寄存器 C API 的同一 ties-to-even 数值语义用于实现路径对照。
<!-- cannbot:related:end -->
