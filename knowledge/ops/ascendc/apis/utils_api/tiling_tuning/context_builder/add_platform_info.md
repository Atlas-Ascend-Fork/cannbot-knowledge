---
type: API
title: AddPlatformInfo
description: 设置硬件平台信息便于用户在算子Tiling函数调测中使用。支持以下两种设置方式： - 自动获取当前硬件平台信息：传入空指针，自动获取当前硬件信息并添加到ContextBuilder类中。
  - 指定硬件平台信息：传入具体的AI处理器型号，添加对应硬件信息至ContextBuilder类中。 若设置失败，会打印报错信息。关于日志配置和查看，请参考《环境变量参考》中日志相关环境变量。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/AddPlatformInfo.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# AddPlatformInfo

## 功能说明
设置硬件平台信息便于用户在算子Tiling函数调测中使用。支持以下两种设置方式：
-   自动获取当前硬件平台信息：传入空指针，自动获取当前硬件信息并添加到ContextBuilder类中。
-   指定硬件平台信息：传入具体的AI处理器型号，添加对应硬件信息至ContextBuilder类中。
若设置失败，会打印报错信息。关于日志配置和查看，请参考《环境变量参考》中日志相关环境变量。
## 函数原型
## 参数说明
customSocVersion：输入：AI处理器型号。
## 返回值说明
当前ContextBuilder对象。
## 约束说明
AddPlatformInfo调用后需要通过BuildTilingContext来构建Tiling的上下文，并传递给Tiling函数来使用。
