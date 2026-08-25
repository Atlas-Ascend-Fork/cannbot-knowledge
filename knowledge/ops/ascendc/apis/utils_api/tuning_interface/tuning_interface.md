---
type: API
title: 调测接口
description: 提供printf、assert、__trap、asc_dump等调测接口。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/tuning_interface/tuning_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 调测接口

提供 AICore 核函数运行时的调测接口，包括日志输出（printf）、断言（assert、__trap）、数据转储（asc_dump）、计时（clock、asc_time_stamp）、性能采集（asc_prof_start、asc_prof_stop、asc_mark_stamp）和 Trace 标记（TRACE_START、TRACE_STOP）。这些接口用于核函数运行时的调试、性能分析和问题定位。

<!-- cannbot:related:start -->
## 相关

- [asc_dump](asc_dump.md)（`related`）：“asc_dump”定义：将对应内存上的数据打印出来，同时支持打印自定义的附加信息（仅支持uint32_t类型的信息），比如打印当前行号等。使用该接口需要包含"utils/debug/asc_dump.h"头文件。该功能主要用于调试和性能分析，通常在调测阶段使用，会对算子性能产生一定影响，生产环境可以通过设置ASCENDC_DUMP=0的方式关闭。；“调测接口”定义：提供printf、assert、__trap、asc_dump等调测接口。。实质衔接：asc_dump 用于调试期查看任意内存并带附加信息；DumpTensor 是张量级替代，生产环境需通过 ASCENDC_DUMP 关闭以免影响性能。
<!-- cannbot:related:end -->
