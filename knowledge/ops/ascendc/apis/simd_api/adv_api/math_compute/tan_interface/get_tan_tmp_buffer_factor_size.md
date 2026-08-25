---
type: API
title: GetTanTmpBufferFactorSize
description: 获取maxLiveNodeCount和extraBuf，用于推算Tan接口在固定临时空间下单次最大计算元素数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Tan_interface/GetTanTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# GetTanTmpBufferFactorSize

获取Tan接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

函数原型：void GetTanTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [Tan](tan.md)（`related`）：Tan 的 sharedTmpBuffer 重载需要 Host 为 tile 预留足够空间；FactorSize 可在 UB 预算确定时反推出安全 calCount。
- [GetTanMaxMinTmpSize](get_tan_max_min_tmp_size.md)（`same_topic`）：GetTanMaxMinTmpSize 与《GetTanTmpBufferFactorSize》的实质衔接是：该 host 查询直接服务 Tan 高阶接口，factor 查询用于把最大最小空间预算转换为实际 tiling 处理量。
- [Tan接口](tan_interface.md)（`same_topic`）：Tan接口 与《GetTanTmpBufferFactorSize》的实质衔接是：Tan 接口由 Tan 和两种临时空间查询组成；Atan 是反函数，Sin/Cos 卡解释 tan=sin/cos 的输入值域与验证关系。
<!-- cannbot:related:end -->
