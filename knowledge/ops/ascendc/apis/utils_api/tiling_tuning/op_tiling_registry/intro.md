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

<!-- cannbot:related:start -->
## 相关

- [TilingDebug](../../../../guides/programming_guide/appendix/common_operations/tiling_debug.md)（`explains`）：TilingDebug 指南说明如何把 OpTilingRegistry 用于离线调测并检查输出 tiling 数据。
- [PlatformInfo](../context_builder/platform_info.md)（`related`）：《PlatformInfo》说明将指向fe::PlatFormInfos的指针传入TilingContext。；《Utils API简介》说明OpTilingRegistry类属于context_ascendc命名空间，主要用于加载Tiling实现的动态库，并获取算子的Tiling函数指针以进行调试和验证。该类通常与ContextBuilder类配合使用，后者用于构造Tiling函数所需的输入参数。具体用法可参考如何进行Tiling调测。。二者在PlatformInfo向ContextBuilder注入fe::PlatFormInfos且只允许BuildTilingContext路径；AddPlatformInfo与Tiling调测流程给出构造和消费闭环上存在可执行的直接衔接。
- [Tiling调测](../tiling_tuning.md)（`related`）：Tiling 调测流程实际组合 OpTilingRegistry 加载动态库、获取函数指针和 ContextBuilder 输入，是本简介的执行落地。
- [构造和析构函数](constructor_and_destructor.md)（`same_topic`）：OpTilingRegistry 简介说明对象负责加载 Tiling 动态库并查找函数，给构造/析构函数提供生命周期上下文。
<!-- cannbot:related:end -->
