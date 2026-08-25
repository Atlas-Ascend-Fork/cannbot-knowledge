---
type: API
title: Erf
description: 按元素做误差函数计算，也称为高斯误差函数
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Erf_interface/Erf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Erf

按元素做误差函数计算（高斯误差函数，error function）。模板参数T支持half/float。

提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetErfMaxMinTmpSize获取。

模板参数isReuseSource预留，传入false即可；config为ErfConfig类型，其中algo指定算法：PADE_APPROXIMATION（默认，高性能，帕德近似算法）或SUBSECTION_POLYNOMIAL_APPROXIMATION（高精度，分段多项式逼近）。接口参数：dstTensor为输出操作数；srcTensor为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 Reg 命名空间无 Erf/Tanh 封装](../../../../../runbooks/compilation/ascend950_reg_erf_tanh.md)（`exemplifies`）：该 runbook 证明 dav-3510 Reg 命名空间没有 Erf 封装，需选用高阶 Erf 或已支持的基础运算组合，给出 API 层选择边界。
- [GeGLU](../../activation_functions/ge_glu_interface/ge_glu.md)（`related`）：GeGLU 与《Erf》的实质衔接是：GeGLU 直接调用 GELU 门控语义并要求独立临时缓冲；接口页和两种空间查询决定 tiling，GELU/Erf 卡解释其激活公式。
- [Erf接口](erf_interface.md)（`same_topic`）：Erf说明按元素做误差函数计算，也称为高斯误差函数。
- [GetErfMaxMinTmpSize](get_erf_max_min_tmp_size.md)（`same_topic`）：GetErfMaxMinTmpSize 与《Erf》的衔接是：Erf 临时空间查询以 ErfMaxMinTmpSize 的计算因子和接口约束为依据，查询结果直接决定 Erf 调用可安全使用的 tmpBuffer 大小。
- [GetErfTmpBufferFactorSize](get_erf_tmp_buffer_factor_size.md)（`same_topic`）：factor-size 允许在固定临时空间下反推 Erf 单次最大元素数，与 MaxMin 查询互补。
<!-- cannbot:related:end -->
