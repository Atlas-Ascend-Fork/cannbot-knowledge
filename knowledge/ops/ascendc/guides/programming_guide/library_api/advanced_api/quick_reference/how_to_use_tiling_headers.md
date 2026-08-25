---
type: Guide
title: 如何使用Tiling依赖的头文件
description: 由于AI处理器的Scalar计算单元执行能力有限，为减少算子Kernel侧的Scalar计算，将部分计算在Host端执行，这需要编写Host端Tiling代码。注意，在程序中调用高阶API的Tiling接口或者使用高阶API的Tiling结构体参数时，需要引入依赖的头文件。在不同的Tiling实现方式下，具体为：
tags: [task.lookup, topic.implementation.api_layer]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/library_api/advanced_api/quick_reference/how_to_use_tiling_headers.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 如何使用Tiling依赖的头文件

由于AI处理器的Scalar计算单元执行能力有限，为减少算子Kernel侧的Scalar计算，将部分计算在Host端执行，这需要编写Host端Tiling代码。注意，在程序中调用高阶API的Tiling接口或者使用高阶API的Tiling结构体参数时，需要引入依赖的头文件。在不同的Tiling实现方式下，具体为：
-   使用标准C++语法定义Tiling结构体
这种方式需要引入依赖的头文件如下。所有高阶API的Tiling结构体定义在AscendC::tiling命名空间下，因此需要通过AscendC::tiling访问具体API的Tiling结构体。
-   使用TILING_DATA_DEF宏定义Tiling结构体
这种方式需要引入依赖的头文件如下。所有高阶API的Tiling结构体和Tiling函数定义在optiling命名空间下。
