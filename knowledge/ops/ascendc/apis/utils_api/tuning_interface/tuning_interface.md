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
