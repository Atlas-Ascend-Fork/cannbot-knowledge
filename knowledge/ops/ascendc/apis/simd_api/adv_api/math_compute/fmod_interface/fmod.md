---
type: API
title: Fmod
description: 按元素计算两个浮点数相除后的余数，Trunc为向零取整
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Fmod_interface/Fmod.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Fmod

按元素计算两个浮点数相除后的余数（dst = src0 - Trunc(src0/src1) * src1），其中Trunc为向零取整操作。模板参数T支持half/float。

提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetFmodMaxMinTmpSize获取。

模板参数isReuseSource预留，传false；config为FmodConfig类型，其中algo指定算法：NORMAL（默认，普通模式，支持half/float）或ITERATION_COMPENSATION（迭代补偿高精度模式，仅支持float）；iterationNum为迭代补偿轮次（仅ITERATION_COMPENSATION模式生效，范围1-11，默认11，轮次越多精度越高但性能越低，src0Tensor与src1Tensor指数位差异不应超过24*iterationNum）。接口参数：dstTensor输出；src0Tensor、src1Tensor输入（TPosition支持VECIN/VECCALC/VECOUT，类型需与dst一致）；sharedTmpBuffer临时缓存；calCount参与计算元素个数。

约束：针对Atlas 推理系列产品AI Core输入数据限制在[-2147483647.0, 2147483647.0]；src0Tensor与src1Tensor数据长度必须一致；Ascend 950PR/950DT上ITERATION_COMPENSATION模式仅支持float；不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。
