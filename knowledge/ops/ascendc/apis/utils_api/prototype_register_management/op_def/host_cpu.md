---
type: API
title: HostCPU（OpDef）
description: 设置Host CPU的配置信息：包括算子输入输出的name、支持的dtype、format等信息。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpDef/HostCPU.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# HostCPU

## 功能说明
设置Host CPU的配置信息：包括算子输入输出的name、支持的dtype、format等信息。
## 函数原型
## 参数说明
无
## 返回值说明
OpHostCPUDef请参考OpHostCPUDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [FlagPartial](../op_host_cpu_def/flag_partial.md)（`same_topic`）：HostCPU（OpDef）说明设置Host CPU的配置信息：包括算子输入输出的name、支持的dtype、format等信息。
- [OpHostCPUDef](../op_host_cpu_def/op_host_cpu_def.md)（`same_topic`）：OpHostCPUDef说明OpHostCPUDef算子定义接口索引；对HostCPU（OpDef）而言，HostCPU 返回 OpHostCPUDef，后者承载 HostCPU 子图注册配置，形成明确的 fluent API 返回值契约。
<!-- cannbot:related:end -->
