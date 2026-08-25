---
type: API
title: Utils API简介
description: OpTilingRegistry类属于context_ascendc命名空间，主要用于加载Tiling实现的动态库，并获取算子的Tiling函数指针以进行调试和验证。该类通常与ContextBuilder类配合使用，后者用于构造Tiling函数所需的输入参数。具体用法可参考如何进行Tiling调测。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/OpTilingRegistry/intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 简介

OpTilingRegistry类属于context_ascendc命名空间，主要用于加载Tiling实现的动态库，并获取算子的Tiling函数指针以进行调试和验证。该类通常与ContextBuilder类配合使用，后者用于构造Tiling函数所需的输入参数。具体用法可参考如何进行Tiling调测。
## 所需的头文件和库文件
-   需要包含的头文件
-   需要链接的库文件：libtiling_api.a。
## Public成员函数
