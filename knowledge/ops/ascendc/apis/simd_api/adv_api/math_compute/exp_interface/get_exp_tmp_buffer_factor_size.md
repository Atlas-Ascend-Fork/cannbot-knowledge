---
type: API
title: GetExpTmpBufferFactorSize
description: 获取Exp接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Exp_interface/GetExpTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetExpTmpBufferFactorSize

获取Exp接口的maxLiveNodeCount和extraBuffer，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuffer表示额外临时空间大小（字节）。

函数原型：void GetExpTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuffer)

参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuffer输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuffer) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。

约束：当反推出的currentShapeSize * typeSize < 256B时，currentShapeSize按256B/typeSize向上取整。

<!-- cannbot:related:start -->
## 相关

- [Exp](exp.md)（`same_topic`）：Exp 与《GetExpTmpBufferFactorSize》的实质衔接是：这些卡直接给出 Exp 的高阶、基础、Reg 与 C 入口及其临时空间契约；所连排障卡均以 Exp 的溢出、下溢、FTZ 或 clamp 行为作为精度根因和修复对象。
- [Exp接口](exp_interface.md)（`same_topic`）：GetExpTmpBufferFactorSize 与《Exp接口》的实质衔接是：该因子查询与 Exp、Exp 接口页及最大最小临时空间查询共同定义固定 UB 容量下单次可计算元素数。
- [GetExpMaxMinTmpSize](get_exp_max_min_tmp_size.md)（`same_topic`）：GetExpTmpBufferFactorSize 与《GetExpMaxMinTmpSize》的实质衔接是：该因子查询与 Exp、Exp 接口页及最大最小临时空间查询共同定义固定 UB 容量下单次可计算元素数。
<!-- cannbot:related:end -->
