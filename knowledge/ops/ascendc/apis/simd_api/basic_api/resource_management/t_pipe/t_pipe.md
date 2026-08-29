---
type: API
title: TPipe
description: TPipe接口索引页，包含简介、构造函数、Init/Destroy、InitBuffer、事件ID管理及SpmBuffer读写等。
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/TPipe.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TPipe

AscendC 统一管道管理器，是 TBuf/TQue/TBufPool 等 buffer 资源的管理入口。通过 Init/Destroy 管理生命周期，InitBuffer 为 TQue/TBuf 分配内存，InitBufPool 为 TBufPool 分配内存；AllocEventID/ReleaseEventID/FetchEventID 管理事件 ID；InitSpmBuffer/WriteSpmBuffer/ReadSpmBuffer 管理 Spm 缓冲区；GetBaseAddr 获取基地址。每个核函数通常持有一个 TPipe 实例。
