---
type: Guide
title: 库API概述
description: 高阶API基于单核对常见算法进行抽象和封装，实现了一些常用的计算算法，旨在提高编程开发效率。高阶API一般通过调用多种基础API实现。高阶API包括数学计算、矩阵计算、激活函数等API。
tags: [task.lookup, topic.implementation.api_layer]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/library_api/advanced_api/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 概述

高阶API基于单核对常见算法进行抽象和封装，实现了一些常用的计算算法，旨在提高编程开发效率。高阶API一般通过调用多种基础API实现。高阶API包括数学计算、矩阵计算、激活函数等API。

如下图所示，实现一个矩阵乘操作，使用基础API需要的步骤较多，需要关注格式转换、数据切分等逻辑；使用高阶API则无需关注这些逻辑，可以快速实现功能。

<!-- cannbot:related:start -->
## 相关

- [基础API概述](../basic_api/overview.md)（`related`）：高阶 API 概述说明其由多种基础 API 封装常见算法，可据开发效率、临时空间和控制粒度在基础/高阶间选型。
- [如何使用Kernel侧临时空间](quick_reference/how_to_use_kernel_temp_space.md)（`related`）：库API概述 与《如何使用Kernel侧临时空间》的实质衔接是：高阶 API 与基础 API 的层级选择、kernel 临时空间和 host tiling 头文件是该概述明确展开的开发契约。
- [如何使用Tiling依赖的头文件](quick_reference/how_to_use_tiling_headers.md)（`related`）：库API概述 与《如何使用Tiling依赖的头文件》的实质衔接是：高阶 API 与基础 API 的层级选择、kernel 临时空间和 host tiling 头文件是该概述明确展开的开发契约。
- [编程接口概述（库API）](../programming_interface_overview.md)（`related`）：Advanced API 概述解释算法封装、Host Tiling 链接依赖和开发效率优势，与基础层形成直接选型对照。
<!-- cannbot:related:end -->
