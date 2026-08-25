---
type: API
title: 系统变量访问
description: 寄存器矢量系统变量访问接口集合，包含ClearSpr接口。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/system_variable_access/system_variable_access.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 系统变量访问

提供 ClearSpr 接口，用于对指定的特殊目的寄存器（SpecialPurposeReg）进行清零操作。通过模板参数 spr 指定目标寄存器，当前支持 AR 寄存器（配合 Squeeze 接口存储有效元素总字节数）。

该接口只能在 VF 函数内调用，命名空间为 AscendC::Reg。仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [ClearSpr](clear_spr.md)（`same_topic`）：系统变量访问 与《ClearSpr》的实质衔接是：本页的实际能力是 ClearSpr 清零 AR 特殊寄存器；GetSpr 读取同一 AR，而 Reg Squeeze 会把有效元素字节数写入 AR，因此它们形成明确的生产、读取和复位契约。
- [ClearSpr](../../special_register_access/clear_spr.md)（`same_topic`）：系统变量访问 与《ClearSpr》的实质衔接是：本页的实际能力是 ClearSpr 清零 AR 特殊寄存器；GetSpr 读取同一 AR，而 Reg Squeeze 会把有效元素字节数写入 AR，因此它们形成明确的生产、读取和复位契约。
- [GetSpr](../../special_register_access/get_spr.md)（`same_topic`）：系统变量访问 与《GetSpr》的实质衔接是：本页的实际能力是 ClearSpr 清零 AR 特殊寄存器；GetSpr 读取同一 AR，而 Reg Squeeze 会把有效元素字节数写入 AR，因此它们形成明确的生产、读取和复位契约。
- [Squeeze](../compare_and_select/squeeze.md)（`same_topic`）：系统变量访问 与《Squeeze》的实质衔接是：本页的实际能力是 ClearSpr 清零 AR 特殊寄存器；GetSpr 读取同一 AR，而 Reg Squeeze 会把有效元素字节数写入 AR，因此它们形成明确的生产、读取和复位契约。
<!-- cannbot:related:end -->
