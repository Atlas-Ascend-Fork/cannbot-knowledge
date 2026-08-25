---
type: Guide
title: AOT编译优化（高级编程）
description: AOT（Ahead-of-Time，提前编译）编译优化是一种将运行时参数提前到编译阶段常量化的性能优化技术。通过在编译阶段对Kernel进行额外的常量化编译，在运行时根据Tiling参数自动匹配预编译的特化版本，让编译器能够进行更深度的优化（如循环展开、死代码消除、常量传播等），从而获得超越通用版本的执行性能。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aot_compilation_optimization.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# AOT编译优化

## 概述
AOT（Ahead-of-Time，提前编译）编译优化是一种将运行时参数提前到编译阶段常量化的性能优化技术。通过在编译阶段对Kernel进行额外的常量化编译，在运行时根据Tiling参数自动匹配预编译的特化版本，让编译器能够进行更深度的优化（如循环展开、死代码消除、常量传播等），从而获得超越通用版本的执行性能。
## 核心原理
在Ascend C算子开发中，Tiling参数（如矩阵分块大小、操作类型等）通常在运行时由Host侧计算并传入Kernel。通用版本Kernel以变量形式使用这些参数，无法深度优化。
AOT的核心思想是：将特定Tiling配置以编译期常量的形式固化到模板代码中，让编译器在编译阶段就能看到这些值，进一步实现：
- 循环展开：基于常量边界完全展开内层循环，消除循环控制开销。
- 常量传播：在编译期计算所有依赖Tiling常量的表达式，减少运行时的标量计算。
- 死代码消除：根据常量操作类型、分块大小裁剪永远不会执行的条件分支减少执行代码量，降低ICache Miss比率。
## 整体流程
### Kernel常量化预编译
- 根据算子的典型Shape和输入，编写Tiling常量模板定义
- Kernel函数实现，常量Tiling与运行时Tiling变量合一的代码实现
### Host在运行时选择特定Kernel
在Host调用Kernel的代码中加入常量化Tiling匹配和调用，编译器根据指定常量Tiling模板与Kernel混合编译实现常量Kernel实例化。
### 完整示例
一个完整的AOT编译优化Matmul示例可参考 matmul_aot_compilation。该示例演示了纯Cube场景下实现AOT编译的完整流程，并将模板方法进行提取实现了一套简易API。
## 注意事项
1. Tiling字节兼容性：如果算子修改了Tiling结构体，则需要确保定义的常量与当前的Tiling结构体定义一致。
2. 编译时间与二进制体积：每个AOT特化版本都会增加编译时间和二进制体积。建议只针对高频使用的配置预编译AOT版本，避免过度特化。
3. 运行时开销：常量Tiling的匹配过程增加额外Host开销，开发者需结合算子使用场景进行相应调整。
