---
type: API
title: Fma
description: 按元素计算两个输入相乘后与第三个输入相加的结果
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Fma_interface/Fma.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Fma

按元素计算两个输入相乘后与第三个输入相加的结果（dst = src0 * src1 + src2）。模板参数T支持half/float。仅Ascend 950PR/950DT支持。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。接口内部涉及精度转换，临时空间大小通过GetFmaMaxMinTmpSize获取。

模板参数config为FmaConfig类型，含isReuseSource（预留，传false）。接口参数：dst为输出操作数；src0、src1、src2为三个输入源操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dst一致；sharedTmpBuffer为临时缓存；count为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [MulAddDst FMA 单次舍入与 golden Mul+Add 双舍入偏差](../../../../../runbooks/precision/muladddst_fma_golden_mul_add.md)（`exemplifies`）：该卡用抵消输入证明 FMA 一次舍入与 Mul+Add 两次舍入的差异。
- [GetFmaMaxMinTmpSize](get_fma_max_min_tmp_size.md)（`related`）：GetFmaMaxMinTmpSize 给出的上下界用于 Fma 的 sharedTmpBuffer；低于最小值会破坏正确性，区间内增加空间可改善性能。
- [GetFmaTmpBufferFactorSize](get_fma_tmp_buffer_factor_size.md)（`related`）：固定 workspace 下 factor-size 决定单次 Fma tile。
- [AscFma](../../../c_api/reg/compound_compute/asc_fma.md)（`same_topic`）：高阶 Fma 在 LocalTensor 上封装同一融合乘加语义，连接 C Reg 实现与 Tensor API。
- [AscFma](../../../c_api/vector_compute/asc_fma.md)（`same_topic`）：AscFma 的核心契约是“按元素将src0和src1相乘并和dst相加，将最终结果存放进dst中，”；Fma 补充“按元素计算两个输入相乘后与第三个输入相加的结果”。
- [Fma接口](fma_interface.md)（`same_topic`）：Fma接口 与《Fma》的实质衔接是：Fma 接口页直接包含 Fma、最大最小空间和 factor 查询，C Reg/Vector 入口执行同一融合乘加；舍入案例说明 FMA 单次舍入不能拆成 Mul+Add。
<!-- cannbot:related:end -->
