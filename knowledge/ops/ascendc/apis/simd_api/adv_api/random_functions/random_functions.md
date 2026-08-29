---
type: API
title: 随机函数
description: 随机函数接口导航页，包含PhiloxRandom随机数生成接口。
tags: [task.lookup, topic.compute.random_sampling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/random_functions/random_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# 随机函数

提供 PhiloxRandom 随机数生成接口。PhiloxRandom 基于 Philox 计数器伪随机算法，输入 128bit 计数器（4×32bit）和两个 32bit key，输出 4 个 32bit 整数。

接口提供连续模式和 stride 模式：连续模式按 `count` 顺序生成；stride 模式通过 PhiloxRandomParams（stride、row、column）支持按列分批生成。模板参数 `Rounds` 支持 7 或 10。目的操作数支持 uint32_t、int32_t（数据类型范围内均匀分布）和 float（0-1 均匀分布），起始地址需 32Byte 对齐。仅 Ascend 950PR/Ascend 950DT 支持。
