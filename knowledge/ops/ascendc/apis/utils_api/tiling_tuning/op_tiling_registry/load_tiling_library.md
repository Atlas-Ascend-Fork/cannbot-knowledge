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
