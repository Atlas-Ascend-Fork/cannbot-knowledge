---
type: Guide
title: 编程接口概述（库API）
description: '>本章提供编程API的概述。具体API参考见Ascend C API。'
tags: [task.lookup, topic.implementation.api_layer]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/library_api/programming_interface_overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 编程接口概述

>本章提供编程API的概述。具体API参考见Ascend C API。

Ascend C提供一组类库API，开发者使用标准C++语法和类库API进行编程。Ascend C编程类库API示意图如下所示，分为：

-   **语言扩展层C API**：开放芯片完备编程能力，支持数组分配内存，一般基于指针编程，提供与业界一致的C语言编程体验。

-   **基础API**：实现对硬件能力的抽象，开放芯片的能力，保证完备性和兼容性。标注为ISASI（Instruction Set Architecture Special Interface，硬件体系结构相关的接口）类别的API，不能保证跨硬件版本兼容。
-   **高阶API**：实现一些常用的计算算法，用于提高编程开发效率，通常会调用多种基础API实现。高阶API包括数学库、Matmul、Softmax等API。高阶API可以保证兼容性。
-   **Utils API（公共辅助函数）**：丰富的通用工具类，涵盖标准库、平台信息获取、运行时编译及日志输出等功能，支持开发者高效实现算子开发与性能优化。

>Ascend C API所在头文件目录为：
> - 语言扩展层C API：`${INSTALL_DIR}/asc/include/c_api`
> - 基础API：`${INSTALL_DIR}/asc/include/basic_api`
> - 高阶API：（注意，如下目录头文件中包含的接口如果未在资料中声明，属于间接调用接口，开发者无需关注）
>    - `${INSTALL_DIR}/asc/include/adv_api`
>    - `${INSTALL_DIR}/asc/include/tiling`，
> - Utils API：`${INSTALL_DIR}/asc/include/utils`
>`${INSTALL_DIR}`请替换为CANN软件安装后文件存储路径。以root用户安装为例，安装后文件默认存储路径为：/usr/local/Ascend/cann。
>
> 使用Ascend C API依赖的库文件说明如下：
> - 语言扩展层C API：不涉及
> - 基础API：不涉及
> - 高阶API：因高阶API配套Host Tiling接口，需要链接libtiling_api.a。
> - Utils API：不涉及

<!-- cannbot:related:start -->
## 相关

- [基础API概述](basic_api/overview.md)（`related`）：Basic API 概述展开硬件能力抽象、兼容性与 ISASI 边界，是上位接口分层中的基础层细化。
- [库API概述](advanced_api/overview.md)（`related`）：Advanced API 概述解释算法封装、Host Tiling 链接依赖和开发效率优势，与基础层形成直接选型对照。
- [异构系统与编程模型](../../getting_started/quick_start/heterogeneous_system_and_programming_model.md)（`same_topic`）：异构系统与编程模型 与《编程接口概述（库API）》的实质衔接是：该快速入门从异构系统、host/device 编程模型扩展到 AI Core SIMT、SIMD/SIMT 混合和库 API；这些概述共同解释算子从 host tiling 到 device kernel 的边界。
<!-- cannbot:related:end -->
