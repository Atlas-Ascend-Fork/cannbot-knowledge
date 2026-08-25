---
type: API
title: Fma接口
description: 按元素执行融合乘加（a*b+c）计算，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Fma_interface/Fma_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Fma接口

按元素执行融合乘加（a*b+c）计算，并提供临时空间大小获取接口。

按元素计算两个输入相乘后与第三个输入相加的结果。计算公式如下：

本接口组包含 Fma。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [MulAddDst FMA 单次舍入与 golden Mul+Add 双舍入偏差](../../../../../runbooks/precision/muladddst_fma_golden_mul_add.md)（`exemplifies`）：Fma接口 与《MulAddDst FMA 单次舍入与 golden Mul+Add 双舍入偏差》的实质衔接是：Fma 接口页直接包含 Fma、最大最小空间和 factor 查询，C Reg/Vector 入口执行同一融合乘加；舍入案例说明 FMA 单次舍入不能拆成 Mul+Add。
- [AscFma](../../../c_api/reg/compound_compute/asc_fma.md)（`same_topic`）：Fma接口 与《AscFma》的实质衔接是：Fma 接口页直接包含 Fma、最大最小空间和 factor 查询，C Reg/Vector 入口执行同一融合乘加；舍入案例说明 FMA 单次舍入不能拆成 Mul+Add。
- [AscFma](../../../c_api/vector_compute/asc_fma.md)（`same_topic`）：Fma接口 与《AscFma》的实质衔接是：Fma 接口页直接包含 Fma、最大最小空间和 factor 查询，C Reg/Vector 入口执行同一融合乘加；舍入案例说明 FMA 单次舍入不能拆成 Mul+Add。
- [Fma](fma.md)（`same_topic`）：Fma接口 与《Fma》的实质衔接是：Fma 接口页直接包含 Fma、最大最小空间和 factor 查询，C Reg/Vector 入口执行同一融合乘加；舍入案例说明 FMA 单次舍入不能拆成 Mul+Add。
- [GetFmaMaxMinTmpSize](get_fma_max_min_tmp_size.md)（`same_topic`）：Fma接口 与《GetFmaMaxMinTmpSize》的实质衔接是：Fma 接口页直接包含 Fma、最大最小空间和 factor 查询，C Reg/Vector 入口执行同一融合乘加；舍入案例说明 FMA 单次舍入不能拆成 Mul+Add。
- [GetFmaTmpBufferFactorSize](get_fma_tmp_buffer_factor_size.md)（`same_topic`）：Fma接口 与《GetFmaTmpBufferFactorSize》的实质衔接是：Fma 接口页直接包含 Fma、最大最小空间和 factor 查询，C Reg/Vector 入口执行同一融合乘加；舍入案例说明 FMA 单次舍入不能拆成 Mul+Add。
<!-- cannbot:related:end -->
