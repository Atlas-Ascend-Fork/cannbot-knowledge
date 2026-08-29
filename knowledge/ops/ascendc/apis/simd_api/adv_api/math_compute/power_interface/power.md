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

- [ApplyAdamW A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/optim/apply_adam_w.md)（`related`）：“每个模板在 `Init` 中读取单元素 `step`、绑定本核 GM基址、初始化 Queue/TBuf、每核只计算一次两个 bias correction”需要幂运算形成 beta 的 step 次方，“按元素做幂运算（dst = src0 ^ src1）”提供可对照的 Power 计算合同。
- [ForeachPowScalar A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_pow_scalar.md)（`related`）：`Power<half,false>`，公共 unary foreach；按元素做幂运算（dst = src0 ^ src1），提供三类接口：Power(dstTensor, src0Tensor, src1Tensor)两个Tensor输入、Power(dstTensor, src0Tensor, src1Scalar)Tensor+标量、Power(dstTensor, src0Scalar, src1Tensor)标量+Tensor。；候选是 A2/A3 foreach FP16/FP32 tile 的直接数学 primitive。
- [ForeachPowScalarList A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_pow_scalar_list.md)（`related`）：ForeachPowScalarList 的 Device 语义是“Kernel 调用 `Power<T,false>` 计算 `y_i［j］=x_i［j］^{e_i}`。”；Power 页定义“按元素做幂运算（dst = src0 ^ src1）”并提供 Tensor+标量重载，后者是每个列表元素 tile 的直接计算原语。
- [GetPowerMaxMinTmpSize](get_power_max_min_tmp_size.md)（`related`）：“临时空间大小通过GetPowerMaxMinTmpSize获取。”在 Power 调用契约中指定 sizing 入口；“在minValue到maxValue范围内，临时空间越大性能越好。”说明该入口返回区间内的性能取舍。
- [GetPowerTmpBufferFactorSize](get_power_tmp_buffer_factor_size.md)（`related`）：“currentShapeSize = (currBuff - extraBuffer) / maxLiveNodeCount / typeSize”从固定 UB 预算反推单次元素数；“临时空间大小通过GetPowerMaxMinTmpSize获取。”说明 Power kernel 的另一种显式临时空间获取入口，两者构成 host 分块与 kernel 调用的选型链。
- [InplacePowTensorScalar 950 ACLNN 算子知识](../../../../../operators/aclnn/math/math/inplace_pow_tensor_scalar_950.md)（`related`）：otherwise -> Power<T,false,{INTRINSIC}>(x,T(e),len)；模板参数isReuseSource预留，传false；config为PowerConfig类型，其中algo指定算法：INTRINSIC（默认，整型使用快速幂算法支持uint8_t/int8_t/uint16_t/int16_t/uint32_t/int32_t，浮点型按exp(y*ln(x))计算支持half/float）或DOUBLE_FLOAT_TECH（高精度浮点算法，精度提升后按exp(y*ln(x))计算减少精度损失，支持bfloat16_t/half/float）。；候选给出整数通用指数分支所调用的 Power 算法合同。
<!-- cannbot:related:end -->
