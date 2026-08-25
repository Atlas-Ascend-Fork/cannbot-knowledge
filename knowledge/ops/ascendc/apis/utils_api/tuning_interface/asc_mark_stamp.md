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

<!-- cannbot:related:start -->
## 相关

- [AscTimeStamp](asc_time_stamp.md)（`related`）：asc_time_stamp 记录时间而 mark_stamp 标注路径位置，二者组合可定位热点并估计阶段耗时。
- [asc_prof_start](asc_prof_start.md)（`related`）：asc_prof_start/stop 定义指标采集窗口，mark_stamp 在窗口内细分执行路径。
- [asc_prof_stop](asc_prof_stop.md)（`related`）：asc_prof_stop 关闭包含 mark 的采集区间，形成可分析流水图。
- [Clock](clock.md)（`same_topic`）：Clock：Clock读取当前cycle count，AscTimeStamp提供同类设备时间戳，asc_mark_stamp把时间点写入调测流；联合使用可构造区间测量。 目标卡《asc_mark_stamp》补充：SIMD场景下，用户通过调用接口，用于在算子执行过程中标记特定位置，便于后期通过流水图分析代码执行路径与性能热点。
- [MarkStamp](../../simd_api/basic_api/debug_interface/performance_stats/mark_stamp.md)（`same_topic`）：MarkStamp 正文推荐使用 AscMarkStamp；后者给出事件标记的准确函数签名、标识范围和使用约束。
<!-- cannbot:related:end -->
