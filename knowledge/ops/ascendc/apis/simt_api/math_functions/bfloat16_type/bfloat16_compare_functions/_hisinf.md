---
type: API
title: __hisinf
description: 判断bfloat16类型浮点数是否为无穷，输入为inf或-inf时返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_compare_functions/__hisinf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hisinf

判断bfloat16类型浮点数是否为无穷，输入为inf或-inf时返回true。
判断浮点数是否为无穷。
函数原型：bool __hisinf(bfloat16_t x)
返回值：接口功能不受全局饱和模式影响。返回值为：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Isinf](../../float_math_functions/isinf.md)（`related`）：Isinf 与《__hisinf》的实质衔接是：SIMT Isinf 与张量 IsInf、half/bfloat16 __hisinf 执行同一无穷判定，可按数据载体切换并核对返回语义。
- [GetIsInfMaxMinTmpSize](../../../../simd_api/adv_api/math_compute/is_inf_interface/get_is_inf_max_min_tmp_size.md)（`same_topic`）：《__hisinf》处理“判断bfloat16类型浮点数是否为无穷，输入为inf或-inf时返回true。”。《GetIsInfMaxMinTmpSize》明确“在host侧获取IsInf接口预留或申请临时空间的最大和最小值，用于Tiling参数传递”，可直接用于核对half isinf 谓词与 IsInf 高阶/SIMT 实现及临时空间合同。
- [GetIsInfTmpBufferFactorSize](../../../../simd_api/adv_api/math_compute/is_inf_interface/get_is_inf_tmp_buffer_factor_size.md)（`same_topic`）：《__hisinf》处理“判断bfloat16类型浮点数是否为无穷，输入为inf或-inf时返回true。”。《GetIsInfTmpBufferFactorSize》明确“获取IsInf接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量”，可直接用于核对half isinf 谓词与 IsInf 高阶/SIMT 实现及临时空间合同。
- [IsInf](../../../../simd_api/adv_api/math_compute/is_inf_interface/is_inf.md)（`same_topic`）：《__hisinf》处理“判断bfloat16类型浮点数是否为无穷，输入为inf或-inf时返回true。”。《IsInf》明确“按元素判断输入浮点数是否为正负无穷，输出浮点数或布尔值”，可直接用于核对half isinf 谓词与 IsInf 高阶/SIMT 实现及临时空间合同。
- [IsInf接口](../../../../simd_api/adv_api/math_compute/is_inf_interface/is_inf_interface.md)（`same_topic`）：《__hisinf》处理“判断bfloat16类型浮点数是否为无穷，输入为inf或-inf时返回true。”。《IsInf接口》明确“按元素判断浮点数是否为±INF，并提供临时空间大小获取接口。”，可直接用于核对half isinf 谓词与 IsInf 高阶/SIMT 实现及临时空间合同。
- [__hisinf](../../half_type/half_compare_functions/_hisinf.md)（`same_topic`）：《__hisinf》处理“判断bfloat16类型浮点数是否为无穷，输入为inf或-inf时返回true。”。《__hisinf》明确“判断浮点数是否为无穷。”，可直接用于核对half isinf 谓词与 IsInf 高阶/SIMT 实现及临时空间合同。
<!-- cannbot:related:end -->
