---
type: API
title: 自定义TBufPool
description: 自定义TBufPool接口索引页，汇总EXTERN_IMPL_BUFPOOL宏、Reset、Init、GetBufHandle及地址与大小管理方法。
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/custom_TBufPool/custom_TBufPool.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# 自定义TBufPool

自定义 TBufPool 接口集合，允许用户自行管理 Buffer 池内存。EXTERN_IMPL_BUFPOOL 宏声明自定义实现；Init/Reset 初始化与重置池；GetBufHandle 获取 buffer 句柄；SetCurAddr/GetCurAddr/SetCurBufSize/GetCurBufSize 管理当前 buffer 地址与大小。适用于对内存布局有特殊需求的场景，使用前需配合 TPipe 的 InitBufPool 完成初始化。
