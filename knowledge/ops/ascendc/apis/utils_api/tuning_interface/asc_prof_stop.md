---
type: API
title: asc_prof_stop
description: SIMD场景下，设置性能数据采集信号停止，和asc_prof_start配合使用。使用msOpProf工具进行算子上板调优时，可在kernel侧代码段前后分别调用asc_prof_start和asc_prof_stop来指定需要调优的代码段范围。
tags:
- task.lookup
- topic.programming_model
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/tuning_interface/asc_prof_stop.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
source_headers:
- include/utils/debug/asc_time.h
---

# asc\_prof\_stop

## 功能说明

SIMD场景下，设置性能数据采集信号停止，和asc\_prof\_start配合使用。使用msOpProf工具进行算子上板调优时，可在kernel侧代码段前后分别调用asc\_prof\_start和asc\_prof\_stop来指定需要调优的代码段范围。

## 函数原型

```
__aicore__ inline void asc_prof_stop()
```

## 参数说明

无

## 返回值说明

无

## 约束说明

无

## 调用示例

```
asc_prof_stop();
```


<!-- cannbot:related:start -->
## 相关

- [asc_prof_start](asc_prof_start.md)（`related`）：SIMD场景下，用于设置性能数据采集信号启动，和asc_prof_stop配合使用。使用msOpProf工具进行算子上板调优时，可在kernel侧代码段前后分别调用asc_prof_start和asc_prof_stop来指定需要调优的代码段范围。；SIMD场景下，设置性能数据采集信号停止，和asc_prof_start配合使用。使用msOpProf工具进行算子上板调优时，可在kernel侧代码段前后分别调用asc_prof_start和asc_prof_stop来指定需要调优的代码段范围。。asc_prof_start 与 asc_prof_stop 分别标记 msOpProf 采集区间的起点和终点，两卡都要求在 Kernel 目标代码段前后成对调用，构成完整性能采集边界。
<!-- cannbot:related:end -->
