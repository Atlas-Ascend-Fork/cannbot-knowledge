---
type: API
title: 系统初始化
description: 系统初始化接口索引页，包含InitSocState。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_init/system_init.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 系统初始化

提供 InitSocState 接口，对 AI Core 全局状态进行初始化，包括 AIC（Cube Core）与 AIV（Vector Core）的公共状态及各自特有状态。

初始化项包括：原子累加状态（关闭）、Mask 工作模式（Normal）、s322fp16 量化 scale 参数（置 1）、CTRL 寄存器（默认值）、原子操作类型（无效）、LoadData Padding 值（0）、Mask 全 1、loop mode 参数重置等。不同产品实际执行的初始化项有差异。

<!-- cannbot:related:start -->
## 相关

- [InitSocState](init_soc_state.md)（`related`）：《InitSocState》的任务是“初始化AI Core全局状态，包括AIC与AIV的公共状态及各自特有状态；不同产品实际执行的初始化项存在差异。”。《系统初始化》具体提供“系统初始化接口索引页，包含InitSocState。”，它直接用于AI Core 全局状态初始化的 C++/C 两层入口。
<!-- cannbot:related:end -->
