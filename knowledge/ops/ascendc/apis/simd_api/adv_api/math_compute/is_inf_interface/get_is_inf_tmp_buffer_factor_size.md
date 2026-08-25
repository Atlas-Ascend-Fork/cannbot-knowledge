---
type: API
title: GetIsInfTmpBufferFactorSize
description: 获取IsInf接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/IsInf_interface/GetIsInfTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# GetIsInfTmpBufferFactorSize

获取IsInf接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLivedNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetIsInfTmpBufferFactorSize(const platform_ascendc::PlatformAscendC& ascendcPlatform, const uint32_t typeSize, uint32_t& maxLivedNodeCount, uint32_t& extraBuf)

参数：ascendcPlatform为平台信息；typeSize为输入数据类型字节数（half传2）；maxLivedNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLivedNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLivedNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [GetIsInfMaxMinTmpSize](get_is_inf_max_min_tmp_size.md)（`same_topic`）：《GetIsInfTmpBufferFactorSize》的任务是“获取IsInf接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量”。《GetIsInfMaxMinTmpSize》具体提供“在host侧获取IsInf接口预留或申请临时空间的最大和最小值，用于Tiling参数传递”，它直接用于IsInf workspace factor、上下界查询与 Kernel 调用合同。
- [IsInf](is_inf.md)（`same_topic`）：《GetIsInfTmpBufferFactorSize》的任务是“获取IsInf接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量”。《IsInf》具体提供“按元素判断输入浮点数是否为正负无穷，输出浮点数或布尔值”，它直接用于IsInf workspace factor、上下界查询与 Kernel 调用合同。
- [IsInf接口](is_inf_interface.md)（`same_topic`）：《GetIsInfTmpBufferFactorSize》的任务是“获取IsInf接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量”。《IsInf接口》具体提供“按元素判断浮点数是否为±INF，并提供临时空间大小获取接口。”，它直接用于IsInf workspace factor、上下界查询与 Kernel 调用合同。
- [__hisinf](../../../../simt_api/math_functions/bfloat16_type/bfloat16_compare_functions/_hisinf.md)（`same_topic`）：《__hisinf》处理“判断bfloat16类型浮点数是否为无穷，输入为inf或-inf时返回true。”。《GetIsInfTmpBufferFactorSize》明确“获取IsInf接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量”，可直接用于核对half isinf 谓词与 IsInf 高阶/SIMT 实现及临时空间合同。
<!-- cannbot:related:end -->
