---
type: API
title: 异常检测
description: 异常检测接口集，包含 ascendc_assert、assert、Trap、CheckLocalMemoryIA(ISASI) 等接口。
tags: [task.lookup, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/exception_detection/exception_detection.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 异常检测

AscendC 异常检测接口集合，用于在核函数运行时进行条件检查与异常触发。ascendc_assert、assert 用于条件断言，条件不满足时触发异常；Trap 主动触发 trap 中断；CheckLocalMemoryIA(ISASI) 用于 ISASI 场景下检查 local memory 使用情况。异常检测有助于定位越界、溢出、资源超限等问题。
