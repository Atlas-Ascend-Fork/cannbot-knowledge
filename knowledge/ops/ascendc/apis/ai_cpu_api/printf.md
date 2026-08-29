---
type: API
title: printf（AI CPU API）
description: 该接口提供AI CPU算子Kernel调试场景下的格式化输出功能，默认将输出内容解析并打印在屏幕上。
tags: [task.lookup, topic.implementation.api_layer.aicpu_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/AI-CPU-API/printf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# printf（AI CPU API）

该接口提供AI CPU算子Kernel调试场景下的格式化输出功能，默认将输出内容解析并打印在屏幕上。

函数原型：void printf(const char* fmt, ...)

参数：
- fmt（输入）：格式控制字符串，包含两种类型的对象：普通字符和转换说明。
普通字符将原样不动地打印输出。转换说明并不直接输出而是用于控制printf中参数的转换和打印。每个转换说明都由一个百分号字符（%）开始，，以转换说明结束，从而说明输出数据的类型。

约束：
- 该接口仅支持通过>>调用，并在异构编译场景使用。
- 该接口不支持打印除换行符之外的其他转义字符。
- 该接口使用Dump功能，所有使用Dump功能的接口在每个核上Dump的数据总量不可超过1M。请开发者自行控制待打印的内容数据量，超出则不会打印。
- 使用该接口时，若采用bisheng命令行编译，开发者需要手动链接相关的静态库；而使用CMake编译时，框架会自动处理链接问题，无需开发者额外关注。具体编译命令如下：通过--cce-aicpu-laicpu_api为Device链接libaicpu_api.a，通过--cce-aicpu-L指定libaicpu_api.a的库路径。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [kernel 源码改动未生效因 binary 缓存](../../runbooks/compilation/kernel_binary_cache_printf_hash_toggle.md)（`exemplifies`）：“该接口使用Dump功能，所有使用Dump功能的接口在每个核上Dump的数据总量不可超过1M。”规定 printf 探针的输出上限；“用上述 PRINTF 对照实验——加 PRINTF 后输出变化即确诊缓存未刷新。”展示该接口作为 kernel 二进制缓存生效探针的具体用法。
<!-- cannbot:related:end -->
