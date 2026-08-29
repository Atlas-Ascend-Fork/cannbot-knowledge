---
type: API
title: Utils APImax
description: 比较相同数据类型的两个数，返回最大值。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/cpp_stdlib/algorithms/max.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# max

比较相同数据类型的两个数，返回最大值。

函数原型：template <typename T, typename U>；__host__ __aicore__ inline constexpr auto max(const T& src0, const U& src1)

参数：T：输入数据src0的数据类型。当前支持的数据类型为bool、int8_t、uint8_t、int16_t、uint16_t、int32_t、uint32_t、float、int64_t、uint64_t。；U：输入数据src1的数据类型。当前支持的数据类型为bool、int8_t、uint8_t、int16_t、uint16_t、int32_t、uint32_t、float、int64_t、uint64_t。<br><br>预留类型，当前必须与T保持一致。；src0（输入）：源操作数。参与比较的输入。；src1（输入）：源操作数。参与比较的输入。

返回值：两个输入数据中的最大值。

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。
约束：两个源操作数的数据类型必须相同。
