---
type: Guide
title: Ascend C多层级编程接口选择参考
description: 欢迎使用 Ascend C 进行昇腾AI处理器算子开发。Ascend C不仅致力于开放芯片完备编程能力支撑实现极致性能，同时通过多层级编程API设计，让您能够根据项目需求、团队技能与性能目标，灵活选择最合适的API，在开发效率与运行性能之间取得最佳平衡。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/asc_how_to_choose_api.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# Ascend C多层级编程接口选择参考

欢迎使用 Ascend C 进行昇腾AI处理器算子开发。Ascend C不仅致力于开放芯片完备编程能力支撑实现极致性能，同时通过多层级编程API设计，让您能够根据项目需求、团队技能与性能目标，灵活选择最合适的API，在开发效率与运行性能之间取得最佳平衡。
---
## 设计目标
Ascend C的设计目标可概括为 “高性能、完备性、易编程、可调试和兼容性”。其通过对C/C++语言标准进行最小化扩展，既支持基于指针的C语言开发习惯，也支持基于Tensor的C++编程范式，在支撑昇腾算子高效开发的同时，实现与现有生态的无缝衔接，保障开发体验的一致性。
我们秉持以下核心理念：
- 没有银弹：不同场景对性能与开发效率的要求各异，单一接口无法在所有场景下实现最优适配；
- 渐进式学习：新手可从易用性接口入手快速验证算法；专家则可向下钻取、精细调优，借助复杂接口充分释放硬件潜能。
## API层级
Ascend C提供三类接口，均支持底层完备编程能力：
API层级：语言：特点：目标用户：主要用途
Tpipe/Tque框架编程API：C++：基于 Tensor 编程通过 Tpipe/Tque 框架统一管理内存与同步：算子库开发者：借助框架自动管理同步与内存，提升编程易用性
基础API：C++：基于 Tensor 编程，提供 C++ 基础完备编程能力通过 MakeTensor / LocalMemoryAllocator 分配 Tensor，自主管理同步：算子库开发者：自主管理同步与内存，匹配 C++ Tensor 开发习惯，支撑极致性能
语言扩展层SIMD & SIMT API：C：基于 指针 编程，提供 C 基础完备编程能力通过数组 [] 分配内存，自主管理同步：算子库开发者：自主管理同步与内存，匹配 C 语言开发习惯，支撑极致性能
此外，Ascend C提供高阶 API 和算子模板库以进一步提升算子开发效率。
