---
type: API
title: 资源管理
description: 资源管理API总览，涵盖TPipe、TBuf、TBufPool、TQue、TQueBind、TSCM、LocalMemAllocator及workspace等。
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/resource_management.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 资源管理

AscendC 资源管理 API 总览，提供片上缓冲区的分配与管理能力。TPipe 为统一管道管理器，配合 GetTPipePtr 获取指针；TQue/TQueBind 管理 Queue 队列；TBuf 管理 Buffer；TBufPool/自定义 TBufPool 管理 Buffer 池；TSCM 管理 SCM 存储；LocalMemAllocator 提供动态分配；workspace/PopStackBuffer 提供 workspace 与栈 buffer 支持。

<!-- cannbot:related:start -->
## 相关

- [GetTPipePtr](get_t_pipe_ptr.md)（`related`）：GetTPipePtr：GetTPipePtr 返回当前 TPipe，全局命名空间 runbook直接修复其调用错误；TPipe与资源管理页解释返回对象及其生命周期。 目标卡《资源管理》补充：资源管理API总览，涵盖TPipe、TBuf、TBufPool、TQue、TQueBind、TSCM、LocalMemAllocator及workspace等。
<!-- cannbot:related:end -->
