---
type: API
title: GetSinCosTmpBufferFactorSize
description: 获取SinCos接口所需的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/SinCos_interface/GetSinCosTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# GetSinCosTmpBufferFactorSize

获取SinCos接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLivedNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetSinCosTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLivedNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLivedNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLivedNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLivedNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [GetSinTmpBufferFactorSize](../sin_interface/get_sin_tmp_buffer_factor_size.md)（`related`）：同时需要 sin/cos 输出时应使用双输出接口的独立 factor 规则，不能沿用单 Sin 的容量估计。
- [SinCos](sin_cos.md)（`related`）：SinCos 计算需要 sharedTmpBuffer 和 count；FactorSize 的 maxLivedNodeCount/extraBuf 公式正用于确定该 count，能直接避免临时空间不足或除零。
- [GetSinCosMaxMinTmpSize](get_sin_cos_max_min_tmp_size.md)（`same_topic`）：GetSinCosMaxMinTmpSize 与《GetSinCosTmpBufferFactorSize》的衔接是：SinCos 临时空间查询依赖 SinCosMaxMinTmpSizeFactor，并为 SinCos 接口分配同时产出正弦、余弦所需的工作区。
- [SinCos接口](sin_cos_interface.md)（`same_topic`）：SinCos接口 与《GetSinCosTmpBufferFactorSize》的实质衔接是：SinCos 接口组以一次调用同时产出 sin/cos，并由两级工作区查询决定 tmpBuffer；Sincosf/Sincospif提供无 π 与带 π 缩放的标量对照。
- [Sincosf](../../../../simt_api/math_functions/float_math_functions/sincosf.md)（`same_topic`）：GetSinCosTmpBufferFactorSize说明获取SinCos接口所需的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。
<!-- cannbot:related:end -->
