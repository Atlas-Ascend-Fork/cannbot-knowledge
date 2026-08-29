---
type: API
title: LoadTilingLibrary
description: 根据输入路径加载Tiling动态库，支持算子包编译或动态库编译方式获取的so文件，返回加载是否成功。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/OpTilingRegistry/LoadTilingLibrary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# LoadTilingLibrary

## 功能说明
根据输入的路径，加载对应的Tiling动态库。开发者基于工程化算子开发开发方式完成算子实现后，可通过算子包编译或算子动态库编译获取对应的Tiling动态库文件。
-   算子包编译：Tiling实现对应的动态库为算子包部署目录下的liboptiling.so。具体路径可参考算子包部署。
-   动态库编译：Tiling实现集成在算子动态库libcust_opapi.so中。具体路径可参考算子动态库和静态库编译。
## 函数原型
## 参数说明
## 返回值说明
true：Tiling动态库加载成功；false：Tiling动态库加载失败。具体错误可参考Log信息。
关于日志配置和查看，请参考《环境变量参考》中日志相关环境变量。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [TilingDebug](../../../../guides/programming_guide/appendix/common_operations/tiling_debug.md)（`explains`）：根据输入的路径，加载对应的Tiling动态库。开发者基于工程化算子开发开发方式完成算子实现后，可通过算子包编译或算子动态库编译获取对应的Tiling动态库文件。；在工程化算子开发过程中，开发者需实现Tiling函数，该函数原型是固定的，接受TilingContext作为输入。框架负责构造TilingContext并调用Tiling函数。若需单独进行Tiling调测，开发者可通过OpTilingRegistry加载编译后的Tiling动态库，获取Tiling函数的指针并进行调用，调用时Tiling函数的TilingContext入参使用ContextBuilder构建。。加载 API 是独立调测流程的入口，指南串起加载动态库、取函数指针和 ContextBuilder 构造入参。
- [GetTilingFunc](get_tiling_func.md)（`related`）：根据输入的路径，加载对应的Tiling动态库。开发者基于工程化算子开发开发方式完成算子实现后，可通过算子包编译或算子动态库编译获取对应的Tiling动态库文件。；典型用法：先通过 OpTilingRegistry.LoadTilingLibrary 加载算子 so 库，再调用 GetTilingFunc("AddCustom") 获取 Tiling 函数并执行。。加载接口把编译产物装入进程，GetTilingFunc 随后按算子名取得并执行其中的 Tiling 函数。
<!-- cannbot:related:end -->
