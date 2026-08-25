---
type: API
title: TQueBind
description: TQueBind接口索引页，包含简介、构造函数、AllocTensor/FreeTensor、EnQue/DeQue及BufHandle管理。
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQueBind/TQueBind.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TQueBind

TQueBind绑定源逻辑位置和目的逻辑位置，根据两端位置确定内存分配和同步事件插入。TQue是TQueBind的简化模式，常规矢量编程使用TQue即可；涉及特殊数据通路（如VECIN→VECOUT、VECOUT→A1/B1/C1、CO2→VECIN）时需使用TQueBind。
模板参数src/dst支持VECIN/VECOUT/A1/A2/B1/B2/CO1/CO2及其组合，depth一般不超过4，mask控制ND到NZ格式转换。
Cube相关数据通路建议使用Matmul等高阶API实现，直接使用TQueBind控制较为复杂。提供AllocTensor/FreeTensor/EnQue/DeQue队列操作及FreeAllEvent、InitBufHandle/InitStartBufHandle等Buffer管理接口。

<!-- cannbot:related:start -->
## 相关

- [纯搬运类算子VECIN和VECOUT建议复用](../../../../../guides/operator_practice/simd_operator_optimization/memory_access/vecin_vecout_reuse.md)（`explains`）：纯搬运类算子VECIN和VECOUT建议复用 与《TQueBind》的实质衔接是：VECIN/VECOUT 复用依赖 TQueBind 将输入输出逻辑位置绑定到同一物理队列；高效搬运、UB 融合和优化总览说明这种复用减少搬运与 UB 占用的适用边界。
- [FreeAllEvent](free_all_event.md)（`same_topic`）：《FreeAllEvent》处理“释放TQueBind队列中申请的所有同步事件，便于在Buffer数量超过同步事件限制时重新申请队列。”。《TQueBind》明确“TQueBind接口索引页，包含简介、构造函数、AllocTensor/FreeTensor、EnQue/DeQue及BufHandle管理。”，可直接用于核对FreeAllEvent 对 TQueBind 事件和 Alloc/Fetch/Release event ID 生命周期的回收合同。
<!-- cannbot:related:end -->
