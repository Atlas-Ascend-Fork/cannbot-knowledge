---
type: API
title: GetCosTmpBufferFactorSize
description: 获取Cos接口的maxLiveNodeCount和extraBuf，用于推算固定空间下单次最大计算元素数
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Cos_interface/GetCosTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetCosTmpBufferFactorSize

获取Cos接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。

提供两种重载：一种不带config参数（使用默认CosConfig），另一种带config参数（须与Cos Kernel接口模板参数config保持一致）。函数原型：void GetCosTmpBufferFactorSize([const CosConfig& config,] const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuf输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [Cos](cos.md)（`same_topic`）：GetCosTmpBufferFactorSize 给出 Cos 临时空间的固定因子计算方式，是另一条合法的 Host 侧 sizing 契约。
- [Cos接口](cos_interface.md)（`same_topic`）：GetCosTmpBufferFactorSize 给出 maxLiveNodeCount 和 extraBuf，用于从固定 UB 预算反推 Cos 单次处理量，是最大/最小空间查询之外的分块计算接口。
- [GetCosMaxMinTmpSize](get_cos_max_min_tmp_size.md)（`same_topic`）：焦点处理Cos 的 workspace 上下界查询；GetCosTmpBufferFactorSize正文界定“获取Cos接口的maxLiveNodeCount和extraBuf，用于推算固定空间下单次最大计算元素数”。候选是 Cos 计算本体、接口页和 factor 查询，三者共同确定同一个 workspace 契约。
<!-- cannbot:related:end -->
