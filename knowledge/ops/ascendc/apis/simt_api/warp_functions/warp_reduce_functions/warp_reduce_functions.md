---
type: API
title: Warp Reduce类函数
description: 提供Warp级别的归约求和、最值等接口。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/Warp_functions/Warp_reduce_functions/Warp_reduce_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Warp Reduce类函数

SIMT API Warp级归约函数集合，在单个Warp内执行归约操作。包含asc_reduce_add（Warp内所有Lane的值求和归约）、asc_reduce_max（Warp内所有Lane的值求最大值归约）、asc_reduce_min（Warp内所有Lane的值求最小值归约）。归约结果广播到Warp内所有Lane，无需额外的同步操作。适用于SIMT并行计算中的数据聚合场景，如损失计算、统计量计算等。

<!-- cannbot:related:start -->
## 相关

- [Warp函数](../warp_functions_intro.md)（`related`）：概述说明 Reduce 适合 Warp 内小范围归约且跨 Warp 需另行同步，专项页提供 add/max/min。
- [asc_reduce_add](asc_reduce_add.md)（`related`）：AscReduceAdd 是该函数族的求和实现，所有活跃 lane 接收同一 Warp 结果。
- [asc_reduce_max](asc_reduce_max.md)（`related`）：AscReduceMax 实现同一活跃线程归约契约的最大值聚合。
- [asc_reduce_min](asc_reduce_min.md)（`related`）：Warp Reduce 总览说明归约结果广播到 Warp 所有 Lane；AscReduceMin 给出其中仅对活跃线程取最小值、并向所有活跃线程返回同一结果的精确执行合同。
<!-- cannbot:related:end -->
