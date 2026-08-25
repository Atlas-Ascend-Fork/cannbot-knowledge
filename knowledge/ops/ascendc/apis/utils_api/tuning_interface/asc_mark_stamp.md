---
type: API
title: asc_mark_stamp
description: SIMD场景下，用户通过调用接口，用于在算子执行过程中标记特定位置，便于后期通过流水图分析代码执行路径与性能热点。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/tuning_interface/asc_mark_stamp.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_mark_stamp

SIMD场景下，用户通过调用接口，用于在算子执行过程中标记特定位置，便于后期通过流水图分析代码执行路径与性能热点。

函数原型：template<pipe_t pipe = PIPE_S>；__aicore__ inline void asc_mark_stamp(uint16_t idx)；template<pipe_t pipe = PIPE_S, uint16_t idx> 等4种重载

参数：pipe：指定打点所在的pipeline类型。；idx：用户设置的打点的唯一标识id。

返回值：无

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。
约束：-   idx取值范围为[0,4095]。为方便从打点图中找到对应的代码，建议不要重复使用相同的idx。
-   如果在循环中增加了一个asc_mark_stamp指令，每次执行到指令时都会输出一个打点，且idx是相同的。
