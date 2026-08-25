---
type: API
title: log
description: 提供ASC_CPU_LOG日志接口。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/log/log.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# log

提供 Host 侧日志打印接口 ASC_CPU_LOG，包含 ASC_CPU_LOG_ERROR、ASC_CPU_LOG_INFO、ASC_CPU_LOG_WARNING、ASC_CPU_LOG_DEBUG 四个级别，可在算子的 TilingFunc 代码中输出调试信息。
非 Tiling 下沉场景下日志输出到 plog，日志级别由环境变量 ASCEND_GLOBAL_LOG_LEVEL 控制；Tiling 下沉场景下因 Tiling 函数运行在 AI CPU 上，需开启 Dump 功能使日志落盘后解析。
约束：Tiling 下沉场景下，若自定义算子工程由不支持 ASC_CPU_LOG 的旧版本 CANN 生成，则该接口无法输出日志，需检查 cmake/device_task.cmake 中是否存在 DEVICE_OP_LOG_BY_DUMP 字段以确认兼容性。

<!-- cannbot:related:start -->
## 相关

- [ASC_CPU_LOG](asc_cpu_log.md)（`same_topic`）：AscCpuLog 是 Log 工具的具体 Host/CPU 输出入口。
<!-- cannbot:related:end -->
