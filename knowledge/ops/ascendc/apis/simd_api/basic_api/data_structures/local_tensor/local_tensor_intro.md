---
type: API
title: LocalTensor简介
description: LocalTensor表达AI Core中Local Memory（内部存储）内的L1/L0A/L0B/L0C Buffer及Unified
  Buffer中的数据。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/LocalTensor_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# LocalTensor简介

LocalTensor 表达 AI Core 中 Local Memory 内的数据，覆盖 L1/L0A/L0B/L0C Buffer 及 Unified Buffer。通过 TPosition 标识逻辑位置（A1/B1/C1/A2/B2/CO1/VECIN/VECOUT 等），同一物理内存可映射多个 TPosition。

核心方法：GetValue/SetValue 元素读写，GetShapeInfo/SetShapeInfo 形状管理，GetSize/GetLength 大小获取，GetPhyAddr 物理地址，ReinterpretCast 类型重解释，operator[]/operator() 下标访问，SetBufferLen/SetAddrWithOffset 地址管理，Print 调试打印，ToFile 数据导出。Pipe 编程框架下通过 TQue 分配，静态编程下通过构造函数指定 pos/addr/size。
