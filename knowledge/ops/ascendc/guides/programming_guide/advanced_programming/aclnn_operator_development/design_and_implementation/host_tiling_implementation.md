---
type: Guide
title: 高级编程基本流程
description: 本文属于基础内容，介绍Host侧Tiling在aclnn工程化算子开发方式中的基本编写流程。Host侧Tiling承接算子功能设计中的Tiling设计结论，把输入shape、属性和运行场景转换成Kernel启动前需要的参数。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/host_tiling_implementation.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 基本流程

本文属于基础内容，介绍Host侧Tiling在aclnn工程化算子开发方式中的基本编写流程。Host侧Tiling承接算子功能设计中的Tiling设计结论，把输入shape、属性和运行场景转换成Kernel启动前需要的参数。
## Tiling概念回顾
Tiling是在Kernel启动前，根据数据规模、平台资源和Kernel实现确定数据切分方式及运行配置的过程。Tiling本身不执行算子的张量计算，而是为Kernel准备运行所需的参数。
对于常见的数据并行算子，数据通常按以下两个层次切分：
- Block：Kernel的逻辑并行单元。整体数据分配给多个Block并行处理，Block数量通过numBlocks指定。
- Tile：单个Block内分批处理的数据单元。当一个Block负责的数据无法一次放入片上存储（例如UB）时，Kernel按Tile循环完成数据搬入、计算和写回。
TilingFunc运行在Host侧。框架在Kernel启动前调用TilingFunc，并通过TilingContext提供输入输出shape、属性信息。TilingFunc读取并校验这些信息，计算切分参数、选择Kernel分支，最后写回两类结果：
- TilingData：Kernel执行时需要读取的参数，例如总元素数、单次处理的数据量、循环次数、尾块长度和分支参数。
- Kernel启动配置：例如numBlocks、workspace大小、TilingKey和调度模式。
Host侧Tiling的输入和输出如下图所示：
图中，TilingContext是TilingFunc与框架之间的数据载体：TilingFunc从中读取输入输出shape、属性信息，并将TilingData、numBlocks、TilingKey和workspace大小等结果写回其中。
## 核心概念
Host侧Tiling的输出主要包括TilingData、numBlocks、workspace大小和TilingKey；不同运行场景还可能涉及调度模式（schedule mode）等Kernel launch配置。写代码前先理解这些输出，后面的流程会更容易对应。
### TilingData
TilingData用于承载Host侧传给Kernel侧的切分结果，只需定义Kernel实际使用的字段。常见字段包括总元素数、单次处理的数据量、循环次数、尾块长度和分支参数，具体字段由Kernel实现决定。
AddCustom基础样例只定义totalLength和tileNum。其中，totalLength表示总元素数；tileNum表示样例中总数据的分块数量。Kernel通过totalLength / tileNum计算单次处理的数据量，并与numBlocks共同确定每个Block的循环次数。
AscendC推荐使用标准C++语法定义Tiling结构体。这种方式便于组织固定大小、可直接复制的字段，且允许不同算子使用同名结构体。字段类型、数组写法和Host/Kernel侧一致性约束见使用约束。
本文档以标准C++语法为主线介绍Tiling实现的基本流程。

<!-- cannbot:related:start -->
## 相关

- [使用高阶API时配套的Tiling实现](tiling_with_advanced_api.md)（`related`）：TilingFunc运行在Host侧。；开发者需要把配套Tiling类的计算结果传到Kernel侧，并使用同一份数据初始化高阶API对象。基础 Host Tiling 流程由高阶 API 章节扩展为配套 Tiling 类的生产消费合同。
- [通过TilingData传递属性信息](tiling_data_attributes.md)（`related`）：TilingFunc运行在Host侧。；属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingData，由框架传到Kernel侧。基础流程的 Host 执行位置与属性跨 Host/Kernel 传递的具体办法直接衔接。
- [高级编程基本流程](kernel_operator_implementation.md)（`related`）：TilingData：Kernel执行时需要读取的参数，例如总元素数、单次处理的数据量、循环次数、尾块长度和分支参数。；tiling：框架追加：指向Host侧Tiling写入的数据。Host 生产的 TilingData 由 Kernel 入口最后一个参数直接消费。
<!-- cannbot:related:end -->
