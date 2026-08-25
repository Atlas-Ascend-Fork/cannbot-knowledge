---
type: API
title: 系统资源与变量
description: 系统资源与变量查询接口索引页，汇总GetTaskRatio、GetUBSizeInBytes、GetVecLen、GetBlockNum/Idx及GetArchVersion等。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/system_resources_and_variables.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 系统资源与变量

提供运行时系统资源与变量的查询接口。GetUBSizeInBytes/GetRuntimeUBSize查询Unified Buffer容量，GetVecLen查询矢量计算单元单次处理元素数，GetTaskRatio查询任务比例。
GetBlockNum/GetBlockIdx获取核总数与当前核编号，GetSubBlockNum/GetSubBlockIdx(ISASI)获取子块信息，GetArchVersion查询硬件架构版本。
另含GetSystemCycle(ISASI)系统周期计数、GetProgramCounter(ISASI)程序计数器、GetSsbufBaseAddr和GetDataBlockSizeInBytes等资源地址与块大小查询。
