---
type: Guide
title: 运行正常（功能调试）
description: 运行正常是算子开发后进行调测的前提，是后续进行性能优化的基础。Ascend C提供了多种调测方法和调测工具，供开发者使用，具体内容请参考功能调试。
tags: [task.lookup, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/functional_debug/running_normally.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 运行正常

运行正常是算子开发后进行调测的前提，也是后续进行性能优化的基础。算子开发完成后，需要先确保其在目标硬件上能够正确执行（不崩溃、不越界、不超时），再进入功能调试（验证计算结果精度是否符合预期）和性能优化（提升执行效率和资源利用率）阶段。Ascend C提供了多种调测方法和调测工具供开发者使用，包括CPU模拟调试、NPU上板执行调试、精度比对工具、Dump数据落盘分析等。具体调测方法和工具使用请参考功能调试章节。
