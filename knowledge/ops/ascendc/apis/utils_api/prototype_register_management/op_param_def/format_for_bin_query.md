---
type: API
title: FormatForBinQuery
description: 设置Input/Output用于运行时算子二进制查找的数据格式，将多种数据格式映射到同一个算子二进制，减少二进制文件生成数量。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpParamDef/FormatForBinQuery.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# FormatForBinQuery

## 功能说明
设置Input/Output用于运行时算子二进制查找的数据格式，和Format/FormatList的数量一致，且一一对应。
算子编译过程中，会根据数据格式生成多个.o，并通过这些数据格式在运行时索引算子二进制。某些算子支持多种数据格式，且对数据格式不敏感，这时可以使用该接口，将多种数据格式映射到同一个算子二进制，多个数据格式可以复用一个.o，从而减少二进制文件的生成。
例如，如果一个算子的输入支持多种数据格式（ge::FORMAT_NC和ge::FORMAT_ND），并且使用ge::FORMAT_NC输入时可以复用ge::FORMAT_ND的二进制文件而不影响最终结果，那么可以采用如下配置：
这样，只需生成一个目标文件（.o），就能实现对多种数据格式的支持。
## 函数原型
## 参数说明
## 返回值说明
OpParamDef算子定义，OpParamDef请参考OpParamDef。
## 约束说明
-   FormatForBinQuery的参数个数需要和当前算子参数的Format或者FormatList的参数个数保持一致。
-   不支持与Scalar/ScalarList同时使用。
-   不支持与ValueDepend同时使用。
-   设置FormatForBinQuery后，会用FormatForBinQuery的数据格式替换当前Input/Output的数据格式，并检查新组合在替换前是否存在。如果存在，则指向对应的二进制，如果不存在，该参数失效，按照原来的数据格式生成。具体请参考示例一。
