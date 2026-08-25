---
type: API
title: OpHostCPUDef
description: OpHostCPUDef算子定义接口索引。
tags: [task.lookup, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpHostCPUDef/OpHostCPUDef.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# OpHostCPUDef

OpHostCPUDef 用于定义算子在 Host CPU 上的执行属性，包括引擎类型（Engine）、分片标志（FlagPartial）、计算开销（ComputeCost）、异步执行标志（FlagAsync）、Kernel 库与 SO 路径（OpKernelLib、KernelSo）、入口函数名（FunctionName）和扩展配置（ExtendCfgInfo）。用于算子需要在 Host 侧 CPU 执行的场景。

<!-- cannbot:related:start -->
## 相关

- [Engine（原型注册管理）](engine.md)（`same_topic`）：Engine 为 HostCPU 实现指定执行引擎，是 OpHostCPUDef 的关键运行配置。
- [ExtendCfgInfo](extend_cfg_info.md)（`same_topic`）：ExtendCfgInfo：HostCPU ExtendCfgInfo与AICPU/AICore同名接口比较可确认配置落在哪类实现，OpHostCPUDef页定义其所属注册对象与其他属性组合。 目标卡《OpHostCPUDef》补充：OpHostCPUDef算子定义接口索引。
- [FlagPartial](flag_partial.md)（`same_topic`）：FlagPartial 声明分片执行语义，影响框架如何调度 HostCPU kernel。
- [FunctionName](function_name.md)（`same_topic`）：FunctionName 把注册对象绑定到实际 HostCPU 函数符号，是从定义到实现的直接契约。
- [HostCPU（OpDef）](../op_def/host_cpu.md)（`same_topic`）：OpHostCPUDef说明OpHostCPUDef算子定义接口索引；对HostCPU（OpDef）而言，HostCPU 返回 OpHostCPUDef，后者承载 HostCPU 子图注册配置，形成明确的 fluent API 返回值契约。
- [KernelSo](kernel_so.md)（`same_topic`）：KernelSo 指定承载函数的共享库，与 FunctionName 共同完成运行时加载。
- [OpKernelLib](op_kernel_lib.md)（`same_topic`）：OpKernelLib 与《OpHostCPUDef》的实质衔接是：OpKernelLib、KernelSo、Engine、FunctionName 和 OpHostCPUDef 是 HostCPU 注册的一组直接字段；AICPU OpkernelLib提供不同后端固定库名对照。
<!-- cannbot:related:end -->
