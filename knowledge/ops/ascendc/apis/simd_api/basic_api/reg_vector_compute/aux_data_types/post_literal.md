---
type: API
title: PostLiteral
description: 枚举类型，用于控制是否开启UB地址自动更新功能，含NORMAL不更新和UPDATE更新两种模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/aux_data_types/PostLiteral.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# PostLiteral

枚举类型，用于控制是否开启UB地址自动更新功能，含NORMAL不更新和UPDATE更新两种模式。

本接口属于 Reg 矢量计算辅助数据类型定义。

# PostLiteral | 参数名 | 描述 | | :-- | :-- | | PostLiteral | 用于控制是否开启UB地址自动更新功能（post update）。 enum class PostLiteral { POST_MODE_NORMAL, POST_MODE_UPDATE }; • POST_MODE_NORMAL：POST_MODE_NORMAL场景使用，UB操作数地址不更新。连续非对齐搬入（LoadUnAlign）不支持POST_MODE_NORMAL模式； • POST_MODE_UPDATE：POST_MODE_UPDATE场景使用，UB地址同时作为输入和输出，每次调用会更新。 |

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
