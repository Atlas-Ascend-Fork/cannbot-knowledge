---
type: API
title: Power（数学计算）
description: 实现按元素做幂运算功能，提供3类接口，处理逻辑如下： ! !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Power_interface/Power.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# Power

按元素做幂运算（dst = src0 ^ src1），提供三类接口：Power(dstTensor, src0Tensor, src1Tensor)两个Tensor输入、Power(dstTensor, src0Tensor, src1Scalar)Tensor+标量、Power(dstTensor, src0Scalar, src1Tensor)标量+Tensor。模板参数T支持多种数据类型（因产品型号而异）。

每类接口提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分全部参与计算和部分参与计算。临时空间大小通过GetPowerMaxMinTmpSize获取。

模板参数isReuseSource预留，传false；config为PowerConfig类型，其中algo指定算法：INTRINSIC（默认，整型使用快速幂算法支持uint8_t/int8_t/uint16_t/int16_t/uint32_t/int32_t，浮点型按exp(y*ln(x))计算支持half/float）或DOUBLE_FLOAT_TECH（高精度浮点算法，精度提升后按exp(y*ln(x))计算减少精度损失，支持bfloat16_t/half/float）。接口参数：dstTensor输出；src0Tensor/src1Tensor或src0Scalar/src1Scalar输入；sharedTmpBuffer临时缓存；calCount参与计算元素个数。TPosition支持VECIN/VECCALC/VECOUT。

约束：不支持源操作数与目的操作数地址重叠；Atlas 推理系列产品AI Core幂运算指数必须小于2^31-1；遵循通用地址对齐约束。950PR/950DT支持uint8_t/int8_t/uint16_t/int16_t/uint32_t/int32_t/half/bfloat16_t/float；A3/A2训练推理和推理AI Core支持half/float/int32_t。

<!-- cannbot:related:start -->
## 相关

- [GetPowerMaxMinTmpSize](get_power_max_min_tmp_size.md)（`same_topic`）：Power 的三类 Tensor/Scalar 重载都在显式 sharedTmpBuffer 路径中要求用 GetPowerMaxMinTmpSize 预算空间；查询接口的两个 shape 正是用来判定所选重载。
- [GetPowerTmpBufferFactorSize](get_power_tmp_buffer_factor_size.md)（`same_topic`）：焦点处理Power 的 workspace factor 推算；Power（数学计算）正文界定“实现按元素做幂运算功能，提供3类接口，处理逻辑如下： ! !”。候选是 Power 计算、接口页和 max/min 查询，直接消费 factor 结果。
- [Power接口](power_interface.md)（`same_topic`）：Power（数学计算）说明实现按元素做幂运算功能，提供3类接口，处理逻辑如下： ! !；对Power接口而言，Power 计算卡定义三类幂运算重载，而两个临时空间查询接口分别支持动态 shape 和固定空间的分块选择。
<!-- cannbot:related:end -->
