---
type: Guide
title: VfLoopOptimization
description: VF函数中循环满足Hardware Loop编码规范时可被编译器优化为硬件级向量循环，提升执行性能，支持成员变量访问、指令分布和地址管理优化。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/vector_compute/vf_optimization/vf_loop_optimization.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# VF循环优化

Ascend 950PR/Ascend 950DT对应的架构中，Vector Function（VF）是实现高性能向量计算的核心载体。VF函数中可以包含最多四层嵌套循环，每层循环中还可以包含多个串行循环，同时支持非循环的向量操作和标量操作。VF对控制结构的支持有限，仅支持for循环和条件判断，不支持switch、do-while和while-do等其他控制结构。VF循环通过尽可能优化为硬件级向量循环（Hardware Loop），从而实现性能优化。
当VF函数中的循环满足Hardware Loop编码规范时，会被编译器优化为Hardware Loop，提升整体执行性能；否则循环逻辑会由迭代变量和条件判断语句构成Software Loop，无法开启VF循环优化。
在遵循Hardware Loop编码规范、确保循环可被优化为Hardware Loop的基础上，可以通过成员变量访问、指令分布优化和地址管理优化等方面进一步提升性能。
## Hardware Loop编码规范
为了能让编译器识别并生成Hardware Loop，对应的Loop代码必须符合硬件设计的要求。具体规范如下：
-   迭代变量类型
VF内所有Loop的迭代变量必须是uint16_t类型。
-   起始值与步长
循环起始值从0开始。
每次迭代的步长必须是递增1。
-   循环内不允许跳转指令，比如if/else、三元运算符?:等条件判断跳转。
VF内if/else在Loop内会阻碍Hardware Loop的生成，编译器虽然会尽可能做if/else消除优化，但是不做完全性保证。
if控制流可使用if constexpr或者for(1)替换。if constexpr在编译时已经完成，无运行时开销，但是需要传入的参数是编译时常量，不能依赖运行时变量；for(1)可以触发编译器的循环优化，在当前硬件条件下，Vector侧执行Loop的性能是远远优于条件分支跳转的。
本示例展示了尾块处理场景，当尾块大小不为0时，hasTail为1，通过for(1)来代替if(hasTail)的判断，提高了Loop的性能。
-   一旦执行，循环计数/边界不允许被更改。
-   若要利用外层循环的计数作为循环边界，将外层循环计数器移动到另一个寄存器中，然后将其设置为循环边界。
下文示例展示了编译器识别并处理为Hardware Loop和Software Loop的两种场景：
## 循环内成员变量访问优化
在一个VF内，不推荐直接访问结构体或类对象的成员变量。直接访问结构体或类对象的成员变量相当于从栈上把内容搬运到Tensor寄存器中，之后通过地址访问Tensor上的内容，该操作将导致VF融合失效，建议通过局部变量临时传参解决，示例如下：
## 循环内指令分布优化
减少Loop循环内非索引相关语句。for循环中存在与索引无关的语句可以提出for循环外来减少指令数。
## 循环内地址管理优化
在VF循环中，当使用搬运指令时，需要计算搬入和搬出的地址偏移量，由此会引入较多的标量计算开销。在Ascend 950PR/Ascend 950DT中，通过引入地址寄存器，可有效优化地址偏移量的计算。

<!-- cannbot:related:start -->
## 相关

- [VF调用](../../../../../apis/simd_api/basic_api/reg_vector_compute/vf_call/vf_call.md)（`explains`）：VF 循环优化指南讨论将循环组织到 VF 内的收益和边界，补足 asc_vf_call 调用粒度与循环应由 wrapper 还是 VF 承担的决策。
- [VfFusionOptimization](vf_fusion_optimization.md)（`related`）：VF Fusion 依赖可融合的 Hardware Loop；Loop 指南给出 uint16_t 计数、0 起步、步长 1、循环内无跳转等可识别条件。
- [中级性能优化](../../../typical_operator_cases/simd_operator_impl/add_vector_operator/intermediate_optimization.md)（`related`）：中级性能优化 与《VfLoopOptimization》的实质衔接是：Add 中级优化围绕 mask 复用、双发、循环/融合与 Get/SetValue 访问开销实施。
- [指令双发优化](dual_issue_optimization.md)（`related`）：指令双发优化 与《VfLoopOptimization》的实质衔接是：双发优化依赖 VF 融合、循环/掩码复用、原子与地址寄存器编排；这些卡分别提供发射冲突定位和可执行改写。
<!-- cannbot:related:end -->
